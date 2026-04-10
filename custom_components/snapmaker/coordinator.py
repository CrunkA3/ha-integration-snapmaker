"""DataUpdateCoordinator for snapmaker."""
from __future__ import annotations

from datetime import timedelta
import logging

import socket
import requests
import time

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    MANUFACTURER,
    CONF_TOKEN,
    CONF_IP,
    CONF_MODEL,
    UDP_PORT,
    UDP_BUFFER_SIZE,
    UDP_MSG,
    UDP_TIMEOUT,
    API_PORT,
    API_CONNECT_PATH,
    API_STATUS_PATH,
    API_DISCONNECT_PATH,
    HTTP_TIMEOUT,
    MAX_RETRY_COUNT,
)

_LOGGER = logging.getLogger(__name__)

class SnapmakerCoordinator(DataUpdateCoordinator):
    """Snapmaker coordinator.

    The CoordinatorEntity class provides:
        should_poll
        async_update
        async_added_to_hass
        available
    """

    def __init__(self, hass, entry):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name="Snapmaker",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=30),
        )
        
        self._retry_count = 0

        self._hass = hass
        self._entry = entry

        # Token is stored in the config entry; read it on startup.
        self._token = entry.data.get(CONF_TOKEN, "")

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(entry.entry_id, {
                    "name": entry.title,
                    "ip": entry.data.get(CONF_IP, ""),
                    "model": entry.data.get(CONF_MODEL, ""),
                    "status": "OFFLINE"
                })

        if "progress" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["progress"] = 0
        if "elapsedTime" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["elapsedTime"] = 0
        if "remainingTime" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["remainingTime"] = 0
        if "toolHead" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["toolHead"] = None
        if "nozzleTargetTemperature1" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["nozzleTargetTemperature1"] = None
        if "nozzleTargetTemperature2" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["nozzleTargetTemperature2"] = None
        if "nozzleTemperature1" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["nozzleTemperature1"] = None
        if "nozzleTemperature2" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["nozzleTemperature2"] = None
        if "isFilamentOut" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["isFilamentOut"] = None
        if "homed" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["homed"] = None
        if "heatedBedTargetTemperature" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["heatedBedTargetTemperature"] = None
        if "heatedBedTemperature" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["heatedBedTemperature"] = None
        if "fileName" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["fileName"] = None

        _LOGGER.info("SnapmakerCoordinator initialized: %s", self.data)

    @property
    def data(self):
        return self._hass.data[DOMAIN][self._entry.entry_id]

    @data.setter
    def data(self, value):
        _LOGGER.info("set data: %s", value)


    @property
    def device_info(self):
        """Return information to link this entity with the correct device."""
        return {
            "identifiers": {
                (DOMAIN, self._entry.entry_id)
                },
            "name": self._entry.title,
            "manufacturer": MANUFACTURER,
            "model": self.data["model"]
        }

    async def _async_update_data(self):
        """Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        _LOGGER.debug("SnapmakerCoordinator _async_update_data")

        try:
            discovered = await self._hass.async_add_executor_job(self._do_udp_discover)
        except UpdateFailed:
            raise
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with socket: {ex}")

        if discovered is None:
            # Socket timed out – increment retry counter and mark offline after threshold
            if self._retry_count >= MAX_RETRY_COUNT:
                self.data["status"] = "OFFLINE"
                self.data["progress"] = 0
                self.data["elapsedTime"] = 0
            self._retry_count += 1
            return self.data

        printer_name = discovered["name"]
        printer_ip = discovered["ip"]
        printer_model = discovered["model"]
        printer_status = discovered["status"]

        _LOGGER.debug("SnapmakerCoordinator got info for %s", printer_name)

        self._hass.data[DOMAIN][self._entry.entry_id]["status"] = printer_status
        self._hass.data[DOMAIN][self._entry.entry_id]["ip"] = printer_ip
        self._hass.data[DOMAIN][self._entry.entry_id]["model"] = printer_model

        self._retry_count = 0

        if printer_status == "RUNNING":
            new_token = await self._hass.async_add_executor_job(self._call_snapmaker_api)
            if new_token and new_token != self._token:
                self._token = new_token
                self._hass.config_entries.async_update_entry(
                    self._entry,
                    data={**self._entry.data, CONF_TOKEN: new_token},
                )
        else:
            self.data["toolHead"] = None
            self.data["nozzleTargetTemperature1"] = None
            self.data["nozzleTargetTemperature2"] = None
            self.data["nozzleTemperature1"] = None
            self.data["nozzleTemperature2"] = None
            self.data["isFilamentOut"] = None
            self.data["homed"] = None
            self.data["heatedBedTargetTemperature"] = None
            self.data["heatedBedTemperature"] = None
            self.data["fileName"] = None

        return self.data

    def _do_udp_discover(self) -> dict | None:
        """Blocking UDP broadcast. Returns printer info dict or None on timeout."""
        sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
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
        finally:
            sock.close()

    def _call_snapmaker_api(self) -> str | None:
        """Call the Snapmaker API. Returns the refreshed token, or None on failure."""
        try:
            token = self._connect()
            time.sleep(1)
            self._get_status(token)
            time.sleep(1)
            self._disconnect(token)
            return token
        except Exception as ex:
            _LOGGER.info("Error reading interface: %s", ex)
            return None

    def _connect(self) -> str:
        """POST to the connect endpoint and return the token from the response."""
        token = self._token
        requestUri = (
            f"http://{self.data['ip']}:{API_PORT}{API_CONNECT_PATH}"
            + ("" if not token else f"?token={token}")
        )
        response = requests.post(requestUri, timeout=HTTP_TIMEOUT)
        _LOGGER.debug(response.content)
        if response.status_code != 200:
            raise UpdateFailed(
                f"Connect returned HTTP {response.status_code}"
            )
        token_value = response.json().get("token")
        if not token_value:
            raise UpdateFailed("Connect response did not contain a token")
        return token_value

    def _disconnect(self, token: str):
        """POST to the disconnect endpoint."""
        requestUri = (
            f"http://{self.data['ip']}:{API_PORT}{API_DISCONNECT_PATH}"
            + ("" if not token else f"?token={token}")
        )
        try:
            requests.post(requestUri, timeout=HTTP_TIMEOUT)
        except Exception as ex:  # pylint: disable=broad-except
            _LOGGER.warning("Disconnect request failed: %s", ex)

    def _get_status(self, token: str):
        """GET the printer status and update coordinator data."""
        requestUri = f"http://{self.data['ip']}:{API_PORT}{API_STATUS_PATH}?token={token}"
        response = requests.get(requestUri, timeout=HTTP_TIMEOUT)

        if response.status_code != 200:
            raise UpdateFailed(
                f"Status request returned HTTP {response.status_code}"
            )

        responseJson = response.json()
        _LOGGER.debug("status api response: %s", responseJson)

        self.data["progress"] = responseJson["progress"]
        self.data["elapsedTime"] = responseJson["elapsedTime"]
        self.data["remainingTime"] = responseJson["remainingTime"]
        self.data["toolHead"] = responseJson.get("toolHead")
        self.data["nozzleTargetTemperature1"] = responseJson.get("nozzleTargetTemperature1")
        self.data["nozzleTargetTemperature2"] = responseJson.get("nozzleTargetTemperature2")
        self.data["nozzleTemperature1"] = responseJson.get("nozzleTemperature1")
        self.data["nozzleTemperature2"] = responseJson.get("nozzleTemperature2")
        self.data["isFilamentOut"] = responseJson.get("isFilamentOut")
        self.data["homed"] = responseJson.get("homed")
        self.data["heatedBedTargetTemperature"] = responseJson.get("heatedBedTargetTemperature")
        self.data["heatedBedTemperature"] = responseJson.get("heatedBedTemperature")
        self.data["fileName"] = responseJson.get("fileName")