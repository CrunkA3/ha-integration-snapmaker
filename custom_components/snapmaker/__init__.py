"""Snapmaker integration"""
import logging
import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN
from .coordinator import SnapmakerCoordinator

_LOGGER = logging.getLogger(__name__)


PLATFORMS: list[str] = ["sensor", "binary_sensor"]


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Snapmaker component and start background printer discovery."""
    hass.async_create_task(_async_discover_and_init_flow(hass))
    return True


async def _async_discover_and_init_flow(hass: HomeAssistant) -> None:
    """Discover a Snapmaker printer via UDP and trigger a config flow if found."""
    from .config_flow import _udp_discover
    from homeassistant import config_entries

    discovered = await hass.async_add_executor_job(_udp_discover)
    if discovered:
        _LOGGER.info(
            "Snapmaker printer discovered at %s – initiating config flow",
            discovered["ip"],
        )
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": config_entries.SOURCE_INTEGRATION_DISCOVERY},
                data=discovered,
            )
        )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Snapmaker from a config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok