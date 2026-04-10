"""Config flow for Snapmaker integration."""
from __future__ import annotations

import logging
import socket

import requests
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant  # noqa: F401 - kept for type clarity

from .const import (
    DOMAIN,
    CONF_TOKEN,
    CONF_IP,
    CONF_MODEL,
    CONF_PRINTER_NAME,
    UDP_PORT,
    UDP_BUFFER_SIZE,
    UDP_MSG,
    UDP_TIMEOUT,
    API_PORT,
    API_CONNECT_PATH,
)

_LOGGER = logging.getLogger(__name__)


def _udp_discover() -> dict | None:
    """Send UDP broadcast and return discovered printer info, or None on timeout."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(UDP_TIMEOUT)
    try:
        sock.sendto(UDP_MSG, ("255.255.255.255", UDP_PORT))
        reply, _ = sock.recvfrom(UDP_BUFFER_SIZE)
        elements = reply.decode("ASCII").split("|")
        printer_name, printer_ip = elements[0].split("@")
        _, printer_model = elements[1].split(":")
        _, printer_status = elements[2].split(":")
        return {
            "name": printer_name,
            "ip": printer_ip,
            "model": printer_model,
            "status": printer_status,
        }
    except socket.timeout:
        return None
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.warning("UDP discovery error: %s", ex)
        return None
    finally:
        sock.close()


def _connect_request(ip: str, token: str | None = None) -> str | None:
    """POST to the connect endpoint. Returns the token on HTTP 200, else None."""
    url = f"http://{ip}:{API_PORT}{API_CONNECT_PATH}"
    if token:
        url += f"?token={token}"
    try:
        response = requests.post(url, timeout=5)
        if response.status_code == 200:
            return response.json().get("token")
    except Exception as ex:  # pylint: disable=broad-except
        _LOGGER.debug("Connect request failed: %s", ex)
    return None


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Snapmaker."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_printer: dict | None = None
        self._printer_name: str | None = None

    # ------------------------------------------------------------------
    # Step 1 – manual trigger: search for a printer via UDP
    # ------------------------------------------------------------------
    async def async_step_user(self, user_input=None):
        """Discover printers via UDP broadcast.

        Called both when the user opens the flow for the first time and
        when they click Submit on the 'no printer found' retry form.
        """
        discovered = await self.hass.async_add_executor_job(_udp_discover)
        if discovered:
            self._discovered_printer = discovered
            return await self.async_step_confirm()

        # No printer found – show a form with only a submit button so the
        # user can trigger another search.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
            errors={"base": "no_printer_found"},
        )

    # ------------------------------------------------------------------
    # Step 1 (alternative) – automatic trigger from async_setup discovery
    # ------------------------------------------------------------------
    async def async_step_integration_discovery(self, discovery_info):
        """Handle a printer discovered automatically in the background."""
        self._discovered_printer = discovery_info

        # Abort silently if this printer is already configured.
        await self.async_set_unique_id(discovery_info["ip"])
        self._abort_if_unique_id_configured()

        return await self.async_step_confirm()

    # ------------------------------------------------------------------
    # Step 2 – user names the printer and confirms
    # ------------------------------------------------------------------
    async def async_step_confirm(self, user_input=None):
        """Show printer details and ask the user for a device name."""
        if user_input is not None:
            self._printer_name = (
                user_input.get(CONF_PRINTER_NAME) or self._discovered_printer["name"]
            )

            # Prevent duplicate entries for the same printer IP.
            if not self.unique_id:
                await self.async_set_unique_id(self._discovered_printer["ip"])
                self._abort_if_unique_id_configured()

            return await self.async_step_wait_for_approval()

        default_name = self._discovered_printer["name"]
        schema = vol.Schema(
            {
                vol.Required(CONF_PRINTER_NAME, default=default_name): str,
            }
        )
        return self.async_show_form(
            step_id="confirm",
            data_schema=schema,
            description_placeholders={
                "printer_name": self._discovered_printer["name"],
                "printer_ip": self._discovered_printer["ip"],
                "printer_model": self._discovered_printer["model"],
            },
        )

    # ------------------------------------------------------------------
    # Step 3 – connect without token, wait for printer approval
    # ------------------------------------------------------------------
    async def async_step_wait_for_approval(self, user_input=None):
        """Send a connect request and wait for the user to approve on the printer.

        On every call (initial and each submit) we attempt a tokenless
        connect.  Once the printer returns a token the entry is created.
        """
        ip = self._discovered_printer["ip"]

        token = await self.hass.async_add_executor_job(_connect_request, ip, None)

        if token:
            _LOGGER.info(
                "Snapmaker printer approved connection, token received for %s", ip
            )
            return self.async_create_entry(
                title=self._printer_name,
                data={
                    CONF_IP: ip,
                    CONF_MODEL: self._discovered_printer["model"],
                    CONF_TOKEN: token,
                    CONF_PRINTER_NAME: self._printer_name,
                },
            )

        # Not yet approved – show an info form; submitting it retries.
        return self.async_show_form(
            step_id="wait_for_approval",
            data_schema=vol.Schema({}),
            description_placeholders={
                "printer_name": self._printer_name or self._discovered_printer["name"],
            },
        )