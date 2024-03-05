from tuya_connector import TuyaOpenAPI
import json
import logging
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.const import ( STATE_ON, STATE_OFF,
    TEMP_CELSIUS, ATTR_TEMPERATURE, PRECISION_WHOLE)
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_FAN_MODE, SUPPORT_SWING_MODE)
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.components.climate import (
    ATTR_HVAC_MODE,
    _DEPRECATED_HVAC_MODE_OFF,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW)

from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_TEMPERATURE_UNIT,
    PRECISION_HALVES,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    TEMP_CELSIUS,
    TEMP_FAHRENHEIT,
)

TEMPERATURE_CELSIUS = "celsius"
TEMPERATURE_FAHRENHEIT = "fahrenheit"
DEFAULT_TEMPERATURE_UNIT = TEMPERATURE_CELSIUS

_LOGGER = logging.getLogger("air")
CONF_NAME = "name"
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

SUPPORT_FLAGS = (
    SUPPORT_TARGET_TEMPERATURE
    | SUPPORT_PRESET_MODE
    | SUPPORT_TARGET_TEMPERATURE_RANGE
    | SUPPORT_FAN_MODE
    | SUPPORT_SWING_MODE
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    # Replace "your_device_id" with your actual Tuya device ID
    # Initialize TuyaOpenAPI
    access_id = config.get(CONF_ACCESS_ID)
    access_key = config.get(CONF_ACCESS_KEY)
    ac = {
        "name": config[CONF_NAME],
        "device_id": config[CONF_DEVICE_ID],
        "access_id": config[CONF_ACCESS_ID],
        "access_key": config[CONF_ACCESS_KEY]
    }
    openapi = TuyaOpenAPI(API_ENDPOINT, access_id, access_key)
    openapi.connect()
    # Create TuyaLight instance and add to entities
    add_entities([TuyaClimate(openapi, ac)])

class TuyaClimate(ClimateEntity):
    def __init__(self, openapi, device_id):
        self._openapi = openapi
        self._device_id = device_id
        self._attr_target_temperature_low = 16
        self._attr_target_temperature_high = 30
        self._attr_preset_mode = None
        self._attr_preset_modes = None
        self._fan_mode = None
        self._swing_mode = None
        self._attr_precision = PRECISION_TENTHS
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temperature = 16
        self._precision = 1
        self._attr_supported_features = SUPPORT_FLAGS

    @property
    def name(self):
        return "Tuya Climate"
    
    @property
    def is_on(self):
        return self._state == STATE_ON
    
    @property
    def is_off(self):
        return self._state == STATE_OFF

    @property
    def temperature_unit(self):
        return TEMP_CELSIUS
    
    @property
    def target_temperature(self):
        """Return the temperature we try to reach."""
        return self._target_temperature

    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._attr_precision

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return ["heat", "cool", "auto", "off"]

    @property
    def fan_mode(self):
        return self._fan_mode

    @property
    def fan_modes(self):
        return ["low", "medium", "high", "auto"]

    @property
    def swing_mode(self):
        return self._swing_mode

    @property
    def swing_modes(self):
        return ["on", "off"]
    
    # @property
    # def temperature_unit(self, config_entry):
    #     """Return the unit of measurement used by the platform."""
    #     if (
    #         self.config(CONF_TEMPERATURE_UNIT, DEFAULT_TEMPERATURE_UNIT)
    #         == TEMPERATURE_FAHRENHEIT
    #     ):
    #         return TEMP_FAHRENHEIT
    #     return TEMP_CELSIUS

    async def send_command(self, power):
        """Helper method to turn on/off the AC."""
        # command_payload = {
        #     "power": power,
        #     "mode": 0,
        #     "temp": self._target_temperature,
        #     "wind": 3
        # }
        # body_json = json.dumps(command_payload)
        # body_dict = json.loads(body_json)

        # # Execute the blocking call using async_add_executor_job
        # result = self._openapi.post(
        #     "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
        # )
        # _LOGGER.debug(result)
        try:
            command_payload = {
                "power": power,
                "mode": 0,
                "temp": self._target_temperature,
                "wind": 3
            }
            body_json = json.dumps(command_payload)
            body_dict = json.loads(body_json)

            # Execute the blocking call using async_add_executor_job
            result = await self.hass.async_add_executor_job(self._openapi.post,
                "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
            )
            _LOGGER.debug(result)
        except Exception as e:
            _LOGGER.error(f"Error in send_command: {e}")

    

    
    async def async_set_temperature(self, **kwargs):
        raise NotImplementedError()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        temperature = kwargs.get(ATTR_TEMPERATURE)
        command_payload = {
                "power": 1,
                "temp" : temperature
            }
        body_json = json.dumps(command_payload)
        body_dict = json.loads(body_json)
        print(temperature)

        # Execute the blocking call using async_add_executor_job
        result = await self.hass.async_add_executor_job(self._openapi.post,
                            "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
            )
        _LOGGER.debug(result)


        if temperature is None:
            return

        if temperature < self._attr_target_temperature_low or temperature > self._attr_target_temperature_high:
            _LOGGER.warning('The temperature value is out of min/max range')
            return

        if self._precision == PRECISION_WHOLE:
            self._target_temperature = round(temperature)
        else:
            self._target_temperature = round(temperature, 1)

        if hvac_mode:
            await self.async_set_hvac_mode(hvac_mode)
            return

        # if not self._hvac_mode.lower() == _DEPRECATED_HVAC_MODE_OFF:
        #     await self.send_command(1)

        self.async_write_ha_state()
    

    # async def async_set_temperature(self, **kwargs):
    #     hvac_mode = kwargs.get(ATTR_HVAC_MODE)
    #     temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
    #     temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)

    #     if temperature_low is not None and temperature_high is not None:
    #         self._attr_target_temperature_low = temperature_low
    #         self._attr_target_temperature_high = temperature_high
    #     elif temperature_low is not None:
    #         self._attr_target_temperature_low = temperature_low
    #         self._attr_target_temperature_high = temperature_low

    #     await self.send_command(hvac_mode=hvac_mode)

    # async def async_set_temperature(self, **kwargs):
    #     temperature = kwargs.get(ATTR_TEMPERATURE)
    #     if temperature is not None:
    #         # Use the temperature value to set the desired temperature for your Tuya device
    #         await self.send_command(power=1, temperature=temperature)
    #     else:
    #         _LOGGER.warning("Temperature not provided in service call.")



    async def async_set_fan_mode(self, fan_mode):
        self._fan_mode = fan_mode
        await self.hass.async_add_executor_job(self.send_command, 1)

    async def async_set_swing_mode(self, swing_mode):
        self._swing_mode = swing_mode
        await self.hass.async_add_executor_job(self.send_command, 1)

    async def async_set_hvac_mode(self, hvac_mode):
        self._hvac_mode = hvac_mode
        await self.hass.async_add_executor_job(self.send_command, 1)

    # async def async_turn_on(self, **kwargs):
    #     """Turn on the AC."""
    #     await self.hass.async_add_executor_job(self.send_command, 1)
    #     self._state = STATE_ON

    #     if ATTR_TEMPERATURE in kwargs:
    #         temperature = kwargs[ATTR_TEMPERATURE]
    #         await self.async_set_temperature

    # async def async_turn_off(self):
    #     """Turn off the AC."""
    #     await self.hass.async_add_executor_job(self.send_command, 0)
    #     self._state = STATE_OFF

    async def async_turn_on(self, **kwargs) -> None:
        command_payload = {
                "power": 1
            }
        body_json = json.dumps(command_payload)
        body_dict = json.loads(body_json)

        # Execute the blocking call using async_add_executor_job
        result = await self.hass.async_add_executor_job(self._openapi.post,
                            "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
            )
        _LOGGER.debug(result)
        self._state = STATE_ON

    async def async_turn_off(self) -> None:
        command_payload = {
                "power": 0,
            
            }
        body_json = json.dumps(command_payload)
        body_dict = json.loads(body_json)

            # Execute the blocking call using async_add_executor_job
        result = await self.hass.async_add_executor_job(self._openapi.post,
                "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
            )
        _LOGGER.debug(result)
        self._state = STATE_ON
    







# import asyncio
# import logging
# from datetime import timedelta
# from tuya_connector import TuyaOpenAPI
# import voluptuous as vol
# from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
# from homeassistant.const import TEMP_CELSIUS, ATTR_TEMPERATURE
# from homeassistant.const import (
#     CONF_NAME, STATE_ON, STATE_OFF, STATE_UNKNOWN, STATE_UNAVAILABLE, ATTR_TEMPERATURE,
#     PRECISION_TENTHS, PRECISION_HALVES, PRECISION_WHOLE)
# from homeassistant.components.climate.const import (
#     HVAC_MODE_OFF, HVAC_MODE_HEAT, HVAC_MODE_COOL,
#     HVAC_MODE_DRY, HVAC_MODE_FAN_ONLY, HVAC_MODE_AUTO,
#     SUPPORT_TARGET_TEMPERATURE, SUPPORT_FAN_MODE,
#     SUPPORT_SWING_MODE, HVAC_MODES, ATTR_HVAC_MODE, SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_PRESET_MODE)
# from homeassistant.helpers import config_validation as cv
# from homeassistant.util import Throttle
# import json

# SUPPORT_FLAGS = 0
# CONF_TARGET_TEMPERATURE_DP = "target_temperature_dp"
# CONF_CURRENT_TEMPERATURE_DP = "current_temperature_dp"
# CONF_TEMPERATURE_STEP = "temperature_step"
# CONF_MAX_TEMP_DP = "max_temperature_dp"
# CONF_MIN_TEMP_DP = "min_temperature_dp"
# CONF_PRECISION = "precision"
# CONF_TARGET_PRECISION = "target_precision"
# CONF_HVAC_MODE_DP = "hvac_mode_dp"
# CONF_HVAC_MODE_SET = "hvac_mode_set"
# CONF_PRESET_DP = "preset_dp"
# CONF_PRESET_SET = "preset_set"
# CONF_HEURISTIC_ACTION = "heuristic_action"
# CONF_HVAC_ACTION_DP = "hvac_action_dp"
# CONF_HVAC_ACTION_SET = "hvac_action_set"
# CONF_ECO_DP = "eco_dp"
# CONF_ECO_VALUE = "eco_value"

# _LOGGER = logging.getLogger("air")
# CONF_NAME = "name"
# CONF_ACCESS_ID = 'access_id'
# CONF_ACCESS_KEY = 'access_key'
# API_ENDPOINT = "https://openapi.tuyain.com"
# CONF_DEVICE_ID = 'device_id'


# PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
#     vol.Optional(CONF_NAME): cv.string,
#     vol.Required(CONF_DEVICE_ID): cv.string,
#     vol.Required(CONF_ACCESS_ID): cv.string,
#     vol.Required(CONF_ACCESS_KEY): cv.string
# })


# def setup_platform(hass, config, add_entities, discovery_info=None):
#     # Replace "your_device_id" with your actual Tuya device ID
#     # Initialize TuyaOpenAPI
#     access_id = config.get(CONF_ACCESS_ID)
#     access_key = config.get(CONF_ACCESS_KEY)
#     ac = {
#         "name": config[CONF_NAME],
#         "device_id": config[CONF_DEVICE_ID],
#         "access_id": config[CONF_ACCESS_ID],
#         "access_key": config[CONF_ACCESS_KEY]
#     }
#     openapi = TuyaOpenAPI(API_ENDPOINT, access_id, access_key)
#     openapi.connect()
#     # Create TuyaLight instance and add to entities
#     add_entities([TuyaClimate(openapi, ac)])


# class TuyaClimate(ClimateEntity):
#     def __init__(self, openapi, device_id):
#         self._openapi = openapi
#         self._device_id = device_id
#         self._target_temperature_low = None
#         self._target_temperature_high = None
#         self._fan_mode = None
#         self._swing_mode = None
#         self._precision = PRECISION_WHOLE
#         self._hvac_mode = HVAC_MODE_OFF
#         self._target_temperature = None
#         self._attr_supported_features =  SUPPORT_TARGET_TEMPERATURE | SUPPORT_PRESET_MODE | SUPPORT_TARGET_TEMPERATURE_RANGE | SUPPORT_FAN_MODE | SUPPORT_SWING_MODE
    
#     # @property
#     # def unique_id(self):
#     #     """Return a unique ID."""
#     #     return f"tuya_climate_{self._device.d7035f8dc87bd285e2y9hf}"

#     @property
#     def name(self):
#         """Return the name of the climate device."""
#         return "Tuya Climate"

#     @property
#     def supported_features(self):
#         """Return the list of supported features."""
#         return SUPPORT_FLAGS

#     @property
#     def temperature_unit(self):
#         """Return the unit of measurement."""
#         return TEMP_CELSIUS

#     # @property
#     # def current_temperature(self):
#     #     """Return the current temperature."""
#     #     return self._temperature

#     @property
#     def hvac_mode(self):
#         """Return the current HVAC mode."""
#         return self._hvac_mode

#     @property
#     def hvac_modes(self):
#         """Return the list of available HVAC modes."""
#         return ["heat", "cool", "auto", "off"]
    
#     # @property
#     # def supported_features(self):
#     #     """Flag supported features."""
#     #     supported_features = 0
#     #     if self.has_config(CONF_TARGET_TEMPERATURE_DP):
#     #         supported_features = supported_features | SUPPORT_TARGET_TEMPERATURE
#     #     if self.has_config(CONF_MAX_TEMP_DP):
#     #         supported_features = supported_features | SUPPORT_TARGET_TEMPERATURE_RANGE
#     #     if self.has_config(CONF_PRESET_DP) or self.has_config(CONF_ECO_DP):
#     #         supported_features = supported_features | SUPPORT_PRESET_MODE
#     #     return supported_features


#     async def async_turn_on(self):
#         """Turn on the AC."""
#         command_payload = {
#           "power": 1,
#           "mode": 0,
#           "temp": 18,
#           "wind": 3
#         }
#         body_json = json.dumps(command_payload)
#         body_dict = json.loads(body_json)

#         # Execute the blocking call using async_add_executor_job
#         result = await self.hass.async_add_executor_job(
#             self._openapi.post, "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
#         )
#         _LOGGER.debug(result)

#     async def async_turn_off(self):
#         """Turn on the AC."""
#         command_payload = {
#           "power": 0,
#           "mode": 0,
#           "temp": 18,
#           "wind": 3
#         }
#         body_json = json.dumps(command_payload)
#         body_dict = json.loads(body_json)

#         # Execute the blocking call using async_add_executor_job
#         result = await self.hass.async_add_executor_job(
#             self._openapi.post, "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command", body_dict
#         )
#         _LOGGER.debug(result)

#     async def async_set_temperature(self, **kwargs):
#         hvac_mode = kwargs.get(ATTR_HVAC_MODE)
#         temperature_low = kwargs.get(ATTR_TARGET_TEMP_LOW)
#         temperature_high = kwargs.get(ATTR_TARGET_TEMP_HIGH)

#         if temperature_low is not None and temperature_high is not None:
#             self._target_temperature_low = temperature_low
#             self._target_temperature_high = temperature_high
#         elif temperature_low is not None:
#             self._target_temperature_low = temperature_low
#             self._target_temperature_high = temperature_low

#         await self.send_command(hvac_mode=hvac_mode)

#     async def async_set_hvac_mode(self, hvac_mode):
#         """Set new HVAC mode."""
#         # Implement your logic here to set the HVAC mode
#         # This could involve sending commands to change the mode via the Tuya API
#         self._hvac_mode = hvac_mode

#     async def send_command(self, hvac_mode=None):
#         command_payload = {
#             "power": 0,
#             "mode": 0,
#             "temp": self._target_temperature,
#             # "wind": self._fan_mode if self._fan_mode else 3,
#             # "shake": 1 if self._swing_mode == "on" else 0,
#         }

#         body_json = json.dumps(command_payload)
#         body_dict = json.loads(body_json)

#         result = await self._openapi.post(
#             "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command",
#             body=body_dict,
#         )
#         _LOGGER.debug(result)