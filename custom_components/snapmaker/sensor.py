"""Platform for Snapmaker integration"""
from __future__ import annotations
import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass
)

from homeassistant.core import (
    HomeAssistant,
    callback
)
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .printer import Printer
from .coordinator import SnapmakerCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    """Add sensors for passed entry in HA."""
    coordinator = SnapmakerCoordinator(hass, entry)

    printer_id = entry.entry_id
    printer = Printer(hass, printer_id, entry.title)

    await coordinator.async_config_entry_first_refresh()

    async_add_entities([
        StateSensor(coordinator, printer),
        IpSensor(coordinator, printer),
        ProgressSensor(coordinator, printer),
        ElapsedTimeSensor(coordinator, printer),
        RemainingTimeSensor(coordinator, printer),
        ToolHeadSensor(coordinator, printer),
        NozzleTargetTemperature1Sensor(coordinator, printer),
        NozzleTargetTemperature2Sensor(coordinator, printer),
        NozzleTemperature1Sensor(coordinator, printer),
        NozzleTemperature2Sensor(coordinator, printer),
        HeatedBedTargetTemperatureSensor(coordinator, printer),
        HeatedBedTemperatureSensor(coordinator, printer),
        FileNameSensor(coordinator, printer),
        ])




class StateSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Snapmaker printer."""
    #_attr_has_entity_name = True
    _attr_name = "State"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = [ "OFFLINE", "RUNNING", "IDLE", "PAUSED" ]
    #_attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:state-machine"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=0)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_state"
        self._attr_name = f"{self._printer.name} State"

        #self._attr_device_info = ...  # For automatic device registration
        #self._attr_unique_id = ...
        _LOGGER.info("Snapmaker StateSensor initialized")


    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.info("snapmaker StateSensor state")
        return self.coordinator.data["status"]


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("snapmaker StateSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()


    async def async_update(self):
        """Synchronize state"""
        #self._attr_native_value  = "OFFLINE"
        _LOGGER.debug("snapmaker StateSensor async_update")
        await self.coordinator.async_request_refresh()





class IpSensor(CoordinatorEntity, SensorEntity):
    """IP of a Snapmaker printer."""
    _attr_device_class = None
    _attr_icon = "mdi:ip-network"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_ip"
        self._attr_name = f"{self._printer.name} IP"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.info("snapmaker IpSensor state")
        return self.coordinator.data["ip"]


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("snapmaker IpSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()


    async def async_update(self):
        """Synchronize state"""
        #self._attr_native_value  = "OFFLINE"
        _LOGGER.debug("snapmaker IpSensor async_update")
        await self.coordinator.async_request_refresh()





class ProgressSensor(CoordinatorEntity, SensorEntity):
    """Progress of a Snapmaker printer."""
    _attr_device_class = None
    _attr_icon = "mdi:percent"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "%"
    _attr_suggested_display_precision = 2

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_progress"
        self._attr_name = f"{self._printer.name} Progress"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.info("snapmaker ProgressSensor state")
        return self.coordinator.data["progress"] * 100


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("snapmaker ProgressSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()


    async def async_update(self):
        """Synchronize state"""
        #self._attr_native_value  = "OFFLINE"
        _LOGGER.debug("snapmaker ProgressSensorpSensor async_update")
        await self.coordinator.async_request_refresh()


class ElapsedTimeSensor(CoordinatorEntity, SensorEntity):
    """ElapsedTime of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_icon = "mdi:timer-sand"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_suggested_display_precision = 0
    _attr_suggested_unit_of_measurement = "min"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_elapsed_Time"
        self._attr_name = f"{self._printer.name} elapsed Time"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug("snapmaker ElapsedTimeSensor state")
        if self.coordinator.data["elapsedTime"] == 0:
            return 0
            
        return self.coordinator.data["elapsedTime"] / 60


    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("snapmaker ElapsedTimeSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()


    async def async_update(self):
        """Synchronize state"""
        #self._attr_native_value  = "OFFLINE"
        _LOGGER.debug("snapmaker ElapsedTimeSensor async_update")
        await self.coordinator.async_request_refresh()


class RemainingTimeSensor(CoordinatorEntity, SensorEntity):
    """RemainingTime of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_icon = "mdi:timer-sand-complete"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "min"
    _attr_suggested_display_precision = 0
    _attr_suggested_unit_of_measurement = "min"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_remaining_Time"
        self._attr_name = f"{self._printer.name} remaining Time"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Return True if roller and hub is available."""
        return True

    @property
    def state(self):
        """Return the state of the sensor."""
        _LOGGER.debug("snapmaker RemainingTimeSensor state")
        if self.coordinator.data["remainingTime"] == 0:
            return 0

        return self.coordinator.data["remainingTime"] / 60



    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("snapmaker RemainingTimeSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()


    async def async_update(self):
        """Synchronize state"""
        #self._attr_native_value  = "OFFLINE"
        _LOGGER.debug("snapmaker RemainingTimeSensor async_update")
        await self.coordinator.async_request_refresh()


class ToolHeadSensor(CoordinatorEntity, SensorEntity):
    """Tool head of a Snapmaker printer."""
    _attr_device_class = None
    _attr_icon = "mdi:printer-3d-nozzle"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_tool_head"
        self._attr_name = f"{self._printer.name} Tool Head"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker ToolHeadSensor state")
        return self.coordinator.data["toolHead"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker ToolHeadSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker ToolHeadSensor async_update")
        await self.coordinator.async_request_refresh()


class NozzleTargetTemperature1Sensor(CoordinatorEntity, SensorEntity):
    """Nozzle 1 target temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_nozzle_target_temperature_1"
        self._attr_name = f"{self._printer.name} Nozzle Target Temperature 1"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker NozzleTargetTemperature1Sensor state")
        return self.coordinator.data["nozzleTargetTemperature1"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker NozzleTargetTemperature1Sensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker NozzleTargetTemperature1Sensor async_update")
        await self.coordinator.async_request_refresh()


class NozzleTargetTemperature2Sensor(CoordinatorEntity, SensorEntity):
    """Nozzle 2 target temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_nozzle_target_temperature_2"
        self._attr_name = f"{self._printer.name} Nozzle Target Temperature 2"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker NozzleTargetTemperature2Sensor state")
        return self.coordinator.data["nozzleTargetTemperature2"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker NozzleTargetTemperature2Sensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker NozzleTargetTemperature2Sensor async_update")
        await self.coordinator.async_request_refresh()


class NozzleTemperature1Sensor(CoordinatorEntity, SensorEntity):
    """Nozzle 1 temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_nozzle_temperature_1"
        self._attr_name = f"{self._printer.name} Nozzle Temperature 1"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker NozzleTemperature1Sensor state")
        return self.coordinator.data["nozzleTemperature1"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker NozzleTemperature1Sensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker NozzleTemperature1Sensor async_update")
        await self.coordinator.async_request_refresh()


class NozzleTemperature2Sensor(CoordinatorEntity, SensorEntity):
    """Nozzle 2 temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_nozzle_temperature_2"
        self._attr_name = f"{self._printer.name} Nozzle Temperature 2"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker NozzleTemperature2Sensor state")
        return self.coordinator.data["nozzleTemperature2"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker NozzleTemperature2Sensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker NozzleTemperature2Sensor async_update")
        await self.coordinator.async_request_refresh()


class HeatedBedTargetTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Heated bed target temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_heated_bed_target_temperature"
        self._attr_name = f"{self._printer.name} Heated Bed Target Temperature"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker HeatedBedTargetTemperatureSensor state")
        return self.coordinator.data["heatedBedTargetTemperature"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker HeatedBedTargetTemperatureSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker HeatedBedTargetTemperatureSensor async_update")
        await self.coordinator.async_request_refresh()


class HeatedBedTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Heated bed temperature of a Snapmaker printer."""
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = "°C"
    _attr_suggested_display_precision = 0

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_heated_bed_temperature"
        self._attr_name = f"{self._printer.name} Heated Bed Temperature"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker HeatedBedTemperatureSensor state")
        return self.coordinator.data["heatedBedTemperature"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker HeatedBedTemperatureSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker HeatedBedTemperatureSensor async_update")
        await self.coordinator.async_request_refresh()


class FileNameSensor(CoordinatorEntity, SensorEntity):
    """File name of the current print on a Snapmaker printer."""
    _attr_device_class = None
    _attr_icon = "mdi:file"

    def __init__(self, coordinator, printer):
        super().__init__(coordinator, context=1)
        self._printer = printer

        self._attr_unique_id = f"{self._printer.device_id}_file_name"
        self._attr_name = f"{self._printer.name} File Name"

    @property
    def device_info(self):
        return self.coordinator.device_info

    @property
    def available(self) -> bool:
        return True

    @property
    def state(self):
        _LOGGER.debug("snapmaker FileNameSensor state")
        return self.coordinator.data["fileName"]

    @callback
    def _handle_coordinator_update(self) -> None:
        _LOGGER.debug("snapmaker FileNameSensor handle_coordinator_update: %s", self.coordinator._entry.title)
        self.async_write_ha_state()

    async def async_update(self):
        _LOGGER.debug("snapmaker FileNameSensor async_update")
        await self.coordinator.async_request_refresh()