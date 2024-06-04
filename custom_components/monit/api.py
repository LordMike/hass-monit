"""Monit API Client."""
from __future__ import annotations

import asyncio
import socket
import logging
import xml.etree.ElementTree as ET

import aiohttp
import async_timeout

_LOGGER = logging.getLogger(__name__)


class MonitApiClientError(Exception):
    """Exception to indicate a general API error."""


class MonitApiClientCommunicationError(MonitApiClientError):
    """Exception to indicate a communication error."""


class MonitApiClientAuthenticationError(MonitApiClientError):
    """Exception to indicate an authentication error."""


class MonitApiStatus:
    """
    Represents the status retrieved from the Monit API.

    Attributes:
        server (MonitApiStatusServer): The server status information.
        checks (dict[str, MonitApiStatusCheck]): A dictionary of checks, keyed by the check name.
    """

    def __init__(self, server: MonitApiStatusServer, checks: dict[str, MonitApiStatusCheck]):
        """
        Initialize a MonitApiStatus instance.
        """
        self.server = server
        self.checks = checks


class MonitApiStatusCheck:
    """
    Represents the status of a single Monit check.

    Attributes:
        id (str): The unique identifier of the check.
        name (str): The name of the check.
        status (str): The status of the check.
        collected_time (float): The time the check data was collected, as a unix timestamp.
    """

    def __init__(self, id: str, name: str, status: str, collected_time: float):
        """
        Initialize a MonitApiStatusCheck instance.
        """
        self.id = id
        self.name = name
        self.status = status
        self.collected_time = collected_time


class MonitApiStatusServer:
    """
    Represents the status of the Monit server.

    Attributes:
        id (str): The unique identifier of the server.
        incarnation (int): The incarnation time of the server, a unix timestamp.
        version (str): The version of the Monit server.
        uptime (int): The uptime of the server in seconds.
        poll (int): The polling interval of the server in seconds.
        localhostname (str): The local hostname of the server.
    """

    def __init__(self, id: str, incarnation: int, version: str, uptime: int, poll: int, localhostname: str):
        """
        Initialize a MonitApiStatusServer instance.
        """
        self.id = id
        self.incarnation = incarnation
        self.version = version
        self.uptime = uptime
        self.poll = poll
        self.localhostname = localhostname


class MonitApiClient:
    """Monit API Client."""

    def __init__(
        self,
        url: str,
        username: str | None,
        password: str | None,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the Monit API Client."""
        self._url = url
        self._username = username
        self._password = password
        self._session = session

    async def async_get_data(self) -> dict:
        """Get data from the Monit API."""
        headers = {}
        if self._username and self._password:
            headers['Authorization'] = aiohttp.BasicAuth(
                self._username, self._password)

        full_url = f"{self._url.rstrip('/')}/_status?format=xml"
        return await self._api_wrapper(method="get", url=full_url, headers=headers)

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                _LOGGER.debug(
                    f"Making {method.upper()} request to {url} with headers: {headers} and data: {data}")
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                response_text = await response.text()
                _LOGGER.debug(
                    f"Received response with status code {response.status} and size {len(response_text)} bytes")

                if response.status in (401, 403):
                    raise MonitApiClientAuthenticationError(
                        "Invalid credentials")
                response.raise_for_status()
                return self._parse_xml(response_text)

        except asyncio.TimeoutError as exception:
            raise MonitApiClientCommunicationError(
                "Timeout error fetching information") from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            raise MonitApiClientCommunicationError(
                "Error fetching information") from exception
        except Exception as exception:  # pylint: disable=broad-except
            _LOGGER.error(f"Unexpected error: {exception}")
            raise MonitApiClientError(
                "Something really wrong happened!") from exception

    def _parse_xml(self, xml_text: str) -> dict:
        """Parse the XML data."""
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            _LOGGER.error(f"Error parsing XML: {e}")
            _LOGGER.error(f"Received XML: {xml_text}")
            raise MonitApiClientError(f"Error parsing XML: {e}") from e

        server_info = {}
        checks = {}

        server = root.find('server')
        if server is not None:
            server_info = MonitApiStatusServer(
                id=server.find('id').text,
                incarnation=int(server.find('incarnation').text),
                version=server.find('version').text,
                uptime=int(server.find('uptime').text),
                poll=int(server.find('poll').text),
                localhostname=server.find('localhostname').text
            )

        for service in root.findall('service'):
            collected_sec = int(service.find('collected_sec').text)
            collected_usec = int(service.find('collected_usec').text)
            collected_time = collected_sec + collected_usec / 1_000_000

            service_data = MonitApiStatusCheck(
                id=service.get('id'),
                name=service.find('name').text,
                status=service.find('status').text,
                collected_time=collected_time
            )
            checks[service_data.name] = service_data

        return MonitApiStatus(
            server=server_info,
            checks=checks
        )
