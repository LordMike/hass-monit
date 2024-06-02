"""Binary sensor platform for monit."""
from __future__ import annotations

from urllib.parse import urlparse
from datetime import datetime
from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorDeviceClass,
)
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_LAST_COLLECTED_TIME
from .coordinator import MonitDataUpdateCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Set up the binary_sensor platform."""
    coordinator: MonitDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        MonitBinarySensor(coordinator, check_name)
        for check_name in coordinator.data.checks.keys()
    )


class MonitBinarySensor(CoordinatorEntity[MonitDataUpdateCoordinator], BinarySensorEntity):
    """Monit binary sensor class."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: MonitDataUpdateCoordinator, check_name: str) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._check_name = check_name
        self._attr_name = check_name
        self._attr_unique_id = self.generate_unique_id(
            self, check_name)
        self._attr_device_info = self.generate_device_info(
            self, coordinator.url, coordinator.config_entry.entry_id)
        self._update_check_attributes()

    def _update_check_attributes(self) -> None:
        """Update check attributes from the coordinator data."""
        check = self.coordinator.data.checks.get(self._check_name, {})
        self._attr_is_on = check.status != '0'
        self._attr_extra_state_attributes = {
            ATTR_LAST_COLLECTED_TIME: self.format_collected_time(
                check.collected_time)
        }

    @staticmethod
    def generate_unique_id(self, check_name: str) -> str:
        """Generate a unique ID based on the server and check name."""
        serverId = self.coordinator.data.server.id
        return f"{serverId}_{check_name}"

    @staticmethod
    def generate_device_info(self, url: str, entry_id: str) -> DeviceInfo:
        """Generate device info based on the URL and entry ID."""
        version = self.coordinator.data.server.version
        serverId = self.coordinator.data.server.id
        hostname = self.coordinator.data.server.localhostname
        return DeviceInfo(
            identifiers={(DOMAIN, entry_id), ('Id', serverId)},
            manufacturer="Monit",
            sw_version=version,
            model="Monitoring Service",
            name=f"Monit ({hostname})",
            configuration_url=url,
        )

    @staticmethod
    def format_collected_time(collected_time: float) -> str:
        """Format the collected time to ISO 8601."""
        collected_datetime = datetime.utcfromtimestamp(
            collected_time).isoformat() + 'Z'
        return collected_datetime

    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        old_state = self._attr_is_on
        old_collected_time = self._attr_extra_state_attributes[ATTR_LAST_COLLECTED_TIME]

        # Update check attributes
        self._update_check_attributes()

        # Only write state if there are changes
        if self._attr_is_on != old_state or self._attr_extra_state_attributes[ATTR_LAST_COLLECTED_TIME] != old_collected_time:
            self.async_write_ha_state()

    @property
    def available(self) -> bool:
        """Return True if the binary_sensor is available."""
        return self.coordinator.last_update_success and self._check_name in self.coordinator.data.checks
