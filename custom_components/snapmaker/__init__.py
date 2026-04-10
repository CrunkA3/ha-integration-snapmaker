"""Snapmaker integration"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.typing import ConfigType

from .const import DOMAIN, CONF_IP

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
    if not discovered:
        return

    discovered_ip = discovered["ip"]

    # Skip if the printer is already configured.
    for entry in hass.config_entries.async_entries(DOMAIN):
        if entry.data.get(CONF_IP) == discovered_ip:
            _LOGGER.debug(
                "Snapmaker printer at %s is already configured, skipping discovery flow",
                discovered_ip,
            )
            return

    # Skip if there is already an in-progress flow for this domain and IP.
    for flow in hass.config_entries.flow.async_progress_by_handler(DOMAIN):
        if flow.get("context", {}).get("unique_id") == discovered_ip:
            _LOGGER.debug(
                "Config flow for Snapmaker printer at %s already in progress",
                discovered_ip,
            )
            return

    _LOGGER.info(
        "Snapmaker printer discovered at %s - initiating config flow",
        discovered_ip,
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