import requests
from homeassistant.components.light import LightEntity
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from pprint import pformat
from homeassistant.const import *

from homeassistant.components.light import PLATFORM_SCHEMA, SUPPORT_BRIGHTNESS, SUPPORT_COLOR
from homeassistant.const import CONF_NAME, STATE_ON, STATE_OFF, CONF_DEVICE_ID, CONF_CLIENT_SECRET
from homeassistant.components.tuya.const import TUYA_CLIENT_ID
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import voluptuous as vol
import homeassistant.helpers.config_validation as cv
from functools import partial
import time
from tuya_connector import TuyaOpenAPI
DOMAIN = "tlight"
from homeassistant.components.light import ATTR_BRIGHTNESS, ATTR_HS_COLOR
import json
from datetime import datetime
CONF_COLOR = "color"

_LOGGER = logging.getLogger("tlight")
CONF_ACCESS_ID = 'access_id'
CONF_ACCESS_KEY = 'access_key'
API_ENDPOINT = "https://openapi.tuyain.com"
CONF_DEVICE_ID = 'device_id'


PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_ACCESS_ID): cv.string,
    vol.Required(CONF_ACCESS_KEY): cv.string
})


def setup_platform(hass, config, add_entities, discovery_info=None):
    # Replace "your_device_id" with your actual Tuya device ID
    # Initialize TuyaOpenAPI
    access_id = config.get(CONF_ACCESS_ID)
    access_key = config.get(CONF_ACCESS_KEY)
    light = {
        "name": config[CONF_NAME],
        "device_id": config[CONF_DEVICE_ID],
        "access_id": config[CONF_ACCESS_ID],
        "access_key": config[CONF_ACCESS_KEY]
    }
    openapi = TuyaOpenAPI(API_ENDPOINT, access_id, access_key)
    openapi.connect()
    # Create TuyaLight instance and add to entities
    add_entities([TuyaLight(openapi, light)])


class TuyaLight(LightEntity):

    def __init__(self, openapi, light):
        super().__init__()
        self._openapi = openapi
        self._entity_id = "light.tuya_light_d78fc0d1660f2a0916fyz0"
        self._state = None
        self._brightness = None
        self._device_id = light["device_id"]
        self._access_id = light["access_id"]
        self._access_key = light["access_key"]
        self._hs_color = None
        self._attr_supported_features = SUPPORT_BRIGHTNESS | SUPPORT_COLOR

    
    @property
    def name(self):
        return "Tuya Light"

    @property
    def is_on(self):
        return self._state == STATE_ON
    
    @property
    def is_off(self):
        return self._state == STATE_OFF
    
    @property
    def brightness(self):
        return self._brightness
    
    @property
    def hs_color(self):
        """Return the color in (hs, brightness) format."""
        return self._hs_color

    @property
    def state_attributes(self):
        attrs = super().state_attributes
        attrs[ATTR_BRIGHTNESS] = self._brightness
        attrs[ATTR_HS_COLOR] = self._hs_color
        return attrs


    async def async_set_brightness(self, brightness):
        # Send command to set the brightness
        commands = {'commands': [{'code': 'bright_value_v2', 'value': brightness}]}
        result = await self.hass.async_add_executor_job(self._openapi.post, f'/v1.0/iot-03/devices/d78fc0d1660f2a0916fyz0/commands', commands)
        _LOGGER.debug(result)
        self._brightness = int(brightness)
        self.async_write_ha_state()

    async def async_get_color_data(self):
        result = await self.hass.async_add_executor_job(self._openapi.get, f'/v1.0/iot-03/devices/{self._device_id}')
        color_data = result.get('data', {}).get('colour_data_v2', {})
        return color_data

    async def async_set_color(self, hs_color, **kwargs):
        """Set the color of the light."""
        # Extract hue and saturation values from hs_color
        hue, saturation = hs_color

        # if not (brightness := kwargs.get(ATTR_BRIGHTNESS)):
        #         brightness = self.brightness or 0

        # Convert hue and saturation to Tuya's color command format
        tuya_hue = max(0, min(int(hue*255/360), 360))
        tuya_saturation = max(0, min(int(saturation*255), 100))
        # self.brightness = max(int(brightness), 255)
        # tuya_value = max(0, min(int(hs_color), 255))

        # color_data = json.dumps({
        #     "h": tuya_hue,
        #     "s": tuya_saturation,
        #     "v": brightness
        # })

        color_data = json.dumps({
            "h": tuya_hue,
            "s": tuya_saturation,
            "v": 255
        })
        

        _LOGGER.debug(f"Setting color - Hue: {hue}, Saturation: {saturation}")


        # Send command to set the color
        commands = {'commands': [{'code': 'colour_data_v2', 'value': color_data}]}
        result = await self.hass.async_add_executor_job(self._openapi.post, f'/v1.0/iot-03/devices/d78fc0d1660f2a0916fyz0/commands', commands)
        _LOGGER.debug(result)

        # Update the internal color state
        self._hs_color = hs_color
        self.async_write_ha_state()


    async def async_turn_on(self, **kwargs):
        # Send command to turn on the light
        commands = {'commands': [{'code': 'switch_led', 'value': True}]}
        result = await self.hass.async_add_executor_job(self._openapi.post, '/v1.0/iot-03/devices/d78fc0d1660f2a0916fyz0/commands', commands)
        _LOGGER.debug(result)
        self._state = STATE_ON

        if ATTR_BRIGHTNESS in kwargs:
            brightness = kwargs[ATTR_BRIGHTNESS]
            await self.async_set_brightness(brightness)

        if ATTR_HS_COLOR in kwargs:
            hs_color = kwargs[ATTR_HS_COLOR]
            await self.async_set_color(hs_color)


    async def async_turn_off(self, **kwargs):
        # Send command to turn off the light
        commands = {'commands': [{'code': 'switch_led', 'value': False}]}
        result = await self.hass.async_add_executor_job(self._openapi.post, '/v1.0/iot-03/devices/d78fc0d1660f2a0916fyz0/commands', commands)
        _LOGGER.debug(result)
        self._state = STATE_OFF
        # self.async_write_ha_state()


    
















# class TuyaLight(LightEntity):
#     """Representation of a Tuya light."""

#     def __init__(self, light):
#         """Initialize the light."""
#         super().__init__()
#         self._name = light["name"]
#         self._state = None
#         self._brightness = None
#         self._device_id = light["device_id"]
#         self._client_id = light["client_id"]
#         self._local_key = light["client_secret"]


#     async def _refresh_token(self):
#         """Refresh the Tuya API token."""
#         refresh_url = "https://openapi.tuyain.com/v1.0/token/refresh"
#         headers = {"Content-Type": "application/x-www-form-urlencoded"}

#         # Your logic to obtain the refresh token goes here
#         refresh_token = "your_refresh_token"

#         # Example request to refresh the token
#         response = requests.post(refresh_url, data={"refresh_token": refresh_token}, headers=headers)

#         try:
#             response.raise_for_status()
#             new_access_token = response.json().get("result", {}).get("access_token")

#             # Update the current token with the new one
#             # self._local_key = new_access_token

#             _LOGGER.info("Token refreshed successfully.")
#         except requests.exceptions.RequestException as e:
#             _LOGGER.error(f"Error refreshing Tuya API token: {e}")


#     async def _send_tuya_command(self, command, payload):
#         """Send a command to the Tuya API."""
    
#         # url = f"https://openapi.tuyain.com/v1.0/devices/{self._device_id}/commands"
#         # url = f"https://openapi.tuyain.com/v1.0/devices/d7d348196ed017cb0adg6h/commands"
#         url = f"https://openapi.tuyain.com/v1.0/iot-03/devices/d7d348196ed017cb0adg6h/commands"


#         # headers = {"Authorization": f"Bearer {self._local_key}",
#         #            "client_id": self._client_id,
#         #            "access_token": "ef97a7bd1d6cd325b455a1d24b72a887"}
#         # # headers = {"Authorization": f"Bearer {self._local_key}"}

#         data = {"commands": [{"code": command, "value": payload}]}
#         headers = {"sign_method": "HMAC-SHA256",
#                    "client_id": "m349744nfph3ut9gupqu",
#                    "t": timestamp,
#                    "mode": "cors",
#                    "Content-Type": "application/json",
#                    "sign": "419D558D77549FC033DD0ABF892580CFAB6DA5420D6C019512E78B895CBE4318",
#                    "access_token": "d544b19f7774d183eb9829ba45a42214",
#                    "Timestamp": timestamp}
#         # headers = {"Authorization": f"Bearer {self._local_key}"}

# #         data = {
# #   "commands": "[{\"code\": \"switch_led\",\"value\": true}]",
# #   "timestamp": timestamp
# # }

#         # Use functools.partial to create a partial function with predefined arguments
#         partial_post = partial(requests.post, url, headers=headers, json=data)
        

#         response = await self.hass.async_add_executor_job(partial_post)

#         if response.status_code == 401 and response.json().get("code") == 1010:
#             _LOGGER.warning("Token invalid. Refreshing token...")
#             await self._refresh_token()

#             # Retry the command after token refresh
#             response = await self.hass.async_add_executor_job(partial_post)


#         print(response)
#         a = response.json()
#         print(a)
#         try:
#             response.raise_for_status()  # Raise HTTPError for bad responses
#             return response.json()
#         except requests.exceptions.RequestException as e:
#             _LOGGER.error(f"Error sending Tuya API command: {e}")
#             return {"success": False, "error": str(e)}
        
#     async def async_turn_on(self, **kwargs):
#         """Turn the light on."""
#         response = await self._send_tuya_command("code", {"value": "true"})
#         # print(response)
#         _LOGGER.debug("Turn on %s", self._name)
#         if response.get("success"):
#             self._state = STATE_ON
#             self.async_write_ha_state()

#     async def async_turn_off(self, **kwargs):
#         """Turn the light off."""
#         response = await self._send_tuya_command("code", {"value": "false"})
#         _LOGGER.debug("Turn off %s", self._name)
#         if response.get("success"):
#             print(response)
#             self._state = STATE_OFF
#             self.async_write_ha_state()

    
#     # async def async_set_brightness(self, brightness):
#     #     """Set the brightness of the light."""
#     #     response = await self._send_tuya_command("setBrightness", {"value": brightness})
#     #     if response.get("success"):
#     #         self._brightness = brightness
#     #         self.async_write_ha_state()
    
# SUPPORT_FEATURES = SUPPORT_BRIGHTNESS | SUPPORT_COLOR