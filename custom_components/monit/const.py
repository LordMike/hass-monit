"""Constants for monit integration."""
from logging import Logger, getLogger

from datetime import timedelta

LOGGER: Logger = getLogger(__package__)

NAME = "Monit Integration"
DOMAIN = "monit"
VERSION = "0.0.1"
ATTRIBUTION = "Data provided by Monit"

CONF_URL = "url"
INITIAL_POLL_INTERVAL = timedelta(seconds=60)

ATTR_LAST_COLLECTED_TIME = "last_collected_time"
