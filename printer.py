"""A 'hub' that connects snapmaker devices."""
from __future__ import annotations

# See https://developers.home-assistant.io/docs/creating_integration_manifest

import asyncio
import random

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

class Printer:
    """Snapmaker 3d printer"""


    def __init__(self, hass: HomeAssistant, entry_id: str, name: str) -> None:
        """Init Printer."""
        self._hass = hass
        self._id = entry_id
        self._name = name
        self._callbacks = set()
        self._loop = asyncio.get_event_loop()
        self._state = "OFFLINE"

        # Some static information about this device
        #self.firmware_version = f"0.0.{random.randint(1, 9)}"
        self.model = "Test Model"

    @property
    def device_id(self) -> str:
        """Return ID for printer."""
        return self._id

    @property
    def name(self) -> str:
        """Return name for printer."""
        return self._name

    @property
    def online(self) -> float:
        """Printer is online."""
        # The dummy roller is offline about 10% of the time. Returns True if online,
        # False if offline.
        return self._state != "OFFLINE"