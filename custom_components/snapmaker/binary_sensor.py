"""Binary sensor platform for Snapmaker integration"""
from __future__ import annotations
import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)

from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .printer import Printer
from .coordinator import SnapmakerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Add binary sensors for passed entry in HA."""
    coordinator = SnapmakerCoordinator(hass, entry)

    printer_id = entry.entry_id
    printer = Printer(hass, printer_id, entry.title)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        FilamentOutSensor(coordinator, printer),
        HomedSensor(coordinator, printer),
    ])


class FilamentOutSensor(CoordinatorEntity, BinarySensorEntity):
    """Filament out status of a Snapmaker printer."""
    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_icon = "mdi:printer-3d-nozzle-alert"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_filament_out"
        self._attr_name = f"{self._printer.name} Filament Out"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data["status"] == "RUNNING"

    @property
    def is_on(self) -> bool | None:
        _LOGGER.debug("snapmaker FilamentOutSensor is_on")
        return self.coordinator.data["isFilamentOut"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker FilamentOutSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker FilamentOutSensor async_update")
        await self.coordinator.async_request_refresh()


class HomedSensor(CoordinatorEntity, BinarySensorEntity):
    """Homed status of a Snapmaker printer."""
    _attr_device_class = None
    _attr_icon = "mdi:home"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_homed"
        self._attr_name = f"{self._printer.name} Homed"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.coordinator.data["status"] == "RUNNING"

    @property
    def is_on(self) -> bool | None:
        _LOGGER.debug("snapmaker HomedSensor is_on")
        return self.coordinator.data["homed"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker HomedSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker HomedSensor async_update")
        await self.coordinator.async_request_refresh()
