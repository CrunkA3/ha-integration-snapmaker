"""DataUpdateCoordinator for snapmaker."""
from __future__ import annotations

from datetime import timedelta
import logging

import socket
import requests
import time
import async_timeout

from homeassistant.components.light import LightEntity
from homeassistant.core import callback
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import DOMAIN, MANUFACTURER

_LOGGER = logging.getLogger(__name__)

class SnapmakerCoordinator(DataUpdateCoordinator):
    """Snapmaker coordinator.

    The CoordinatorEntity class provides:
        should_poll
        async_update
        async_added_to_hass
        available
    """

    sockTimeout = 3.0
    bufferSize = 1024
    msg = b'discover'
    destPort = 20054
    smToken = "45992cd3-84f0-4995-b5bd-7f47948fff4c"

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

        hass.data.setdefault(DOMAIN, {})
        hass.data[DOMAIN].setdefault(entry.entry_id, {
                    "name": entry.title,
                    "ip": "",
                    "model": "",
                    "status": "OFFLINE"
                })

        if "progress" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["progress"] = 0
        if "elapsedTime" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["elapsedTime"] = 0
        if "remainingTime" not in hass.data[DOMAIN][entry.entry_id]:
            hass.data[DOMAIN][entry.entry_id]["remainingTime"] = 0

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
            UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            UDPClientSocket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            UDPClientSocket.settimeout(self.sockTimeout)

            UDPClientSocket.sendto(self.msg, ("255.255.255.255", self.destPort))
            reply, server_address_info = UDPClientSocket.recvfrom(self.bufferSize)
            
            elements = reply.decode('ASCII').split('|')

            printer_name, printer_ip = (elements[0]).split('@')
            model_key, printer_model = (elements[1]).split(':')
            status_key, printer_status = (elements[2]).split(':')
            
            if self.data == None:
                self.data = {}

            
            _LOGGER.debug("SnapmakerCoordinator got info for %s", printer_name)

            self._hass.data[DOMAIN][self._entry.entry_id]["status"] = printer_status
            self._hass.data[DOMAIN][self._entry.entry_id]["ip"] = printer_ip
            self._hass.data[DOMAIN][self._entry.entry_id]["model"] = printer_model
            
            self._retry_count = 0

            if printer_status == "RUNNING":
                apiResult = await self._hass.async_add_executor_job(self._call_snapmaker_api)
            
            return self.data

            #devices = list(deviceInfo)
            #self.last_results[printer_name] = deviceInfo

        except socket.timeout as ex:
            if self._retry_count >= 3:
                self.data["status"] = "OFFLINE"
                self.data["progress"] = 0
                self.data["elapsedTime"] = 0

            self._retry_count += 1
            
        except Exception as ex:
            raise UpdateFailed(f"Error communicating with socket: {ex}")

    def _call_snapmaker_api(self) -> bool:
        try:
            self._connect()
            time.sleep(1)
            self._get_status()
            time.sleep(1)
            self._disconnect()
            return True
        except Exception as ex:
            _LOGGER.info("Fehler beim lesen der Schnittstelle: %s", ex)
            return False

    def _connect(self):
        token = self.smToken
        requestUri = 'http://' + self.data["ip"] + ':8080/api/v1/connect' + ( '' if token == ''  else ('?token=' + token))
        response = requests.post(requestUri)
        _LOGGER.debug(response.content)
        self.smToken = response.json()['token']

    def _disconnect(self):
        token = self.smToken
        requestUri = 'http://' + self.data["ip"] + ':8080/api/v1/disconnect' + ( '' if token == ''  else ('?token=' + token))
        response = requests.post(requestUri)

    def _get_status(self):
        token = self.smToken
        requestUri = 'http://' + self.data["ip"] + ':8080/api/v1/status?token=' + token
        response = requests.get(requestUri)
        
        responseJson = response.json()
        _LOGGER.debug("status api response: %s", responseJson)

        self.data["progress"] = responseJson["progress"]
        self.data["elapsedTime"] = responseJson["elapsedTime"]
        self.data["remainingTime"] = responseJson["remainingTime"]
        #snapmaker = {
        #    "total_lines": responseJson['totalLines'],
        #    "current_line": responseJson['currentLine'],
        #    "progress": responseJson['progress'],
        #    "elapsed_time": responseJson['elapsedTime'],
        #    "remaining_time": responseJson['remainingTime'],
        #}