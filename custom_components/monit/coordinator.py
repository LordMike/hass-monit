"""DataUpdateCoordinator for monit."""
from __future__ import annotations

from datetime import timedelta, datetime

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.exceptions import ConfigEntryAuthFailed

from .api import MonitApiClient, MonitApiClientAuthenticationError, MonitApiClientError, MonitApiStatus
from .const import DOMAIN, LOGGER, INITIAL_POLL_INTERVAL


class MonitDataUpdateCoordinator(DataUpdateCoordinator[MonitApiStatus]):
    """Class to manage fetching data from the API."""

    config_entry: ConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        client: MonitApiClient
    ) -> None:
        """Initialize."""
        self.client = client
        self.url = client._url
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=INITIAL_POLL_INTERVAL
        )

    async def _async_update_data(self):
        """Update data via library."""
        try:
            result = await self.client.async_get_data()

            # Ensure we always have a sane poll time
            # Clamp to 10..600 seconds
            pollTime = min(600, max(10, result.server.poll))

            # Get the current time
            now = datetime.utcnow().timestamp()

            # Find the latest collection time from the checks
            latest_collected_time = max(
                float(check.collected_time) for check in result.checks.values()
            )

            # Calculate the next poll interval - add a small buffer
            # TODO we could track how far off the measurements are from the ideal poll time, and then use that instead. If poll is 120, but it takes 2 seconds to do, the actuall poll interval is 122
            # Guarantee at least 10s in the future
            nextPollTimestamp = latest_collected_time + pollTime + 3
            nextCheckTimeSeconds = max(10, nextPollTimestamp - now)

            # Log the new update interval
            LOGGER.debug(
                "Updating the monit update_interval to %d seconds based on last collected time and poll interval",
                nextCheckTimeSeconds
            )

            self.update_interval = timedelta(seconds=nextCheckTimeSeconds)

            return result
        except MonitApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except MonitApiClientError as exception:
            raise UpdateFailed(exception) from exception
