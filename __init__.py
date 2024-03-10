"""Snapmaker integration"""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, CONF_URL, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.discovery import load_platform
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import SnapmakerCoordinator
from .printer import Printer

_LOGGER = logging.getLogger(__name__)


#PLATFORMS: list[str] = ["device_tracker", "sensor"]
PLATFORMS: list[str] = [ "sensor" ]


#def setup(hass: HomeAssistant, config: ConfigType) -> bool:
#    """Set up the snapmaker component."""
#    load_platform(hass, Platform.DEVICE_TRACKER, DOMAIN, [], config)
#    load_platform(hass, Platform.SENSOR, DOMAIN, [], config)
#    _LOGGER.info("snapmaker2 setup complete")
#    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Hello World from a config entry."""
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    #hass.data.setdefault(DOMAIN, {})[entry.entry_id] = hub.Hub(hass)

    # This creates each HA object for each platform your device requires.
    # It's done by calling the `async_setup_entry` function in each platform module.
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    #coordinator = SnapmakerCoordinator(hass)
    #printer_id = entry.entry_id

    #printer = Printer(hass, printer_id, entry.title)

    # Fetch initial data so we have data when entities subscribe
    #
    # If the refresh fails, async_config_entry_first_refresh will
    # raise ConfigEntryNotReady and setup will try again later
    #
    # If you do not want to retry setup on failure, use
    # coordinator.async_refresh() instead
    #
    #await coordinator.async_config_entry_first_refresh()
    
    #async_add_entities([StateSensor(coordinator, printer)])

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # This is called when an entry/configured device is to be removed. The class
    # needs to unload itself, and remove callbacks. See the classes for further
    # details
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok