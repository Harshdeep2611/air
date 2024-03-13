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
    ATTR_TARGET_TEMP_LOW,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP)

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
        self._attr_precision = PRECISION_WHOLE
        self._hvac_mode = HVAC_MODE_OFF
        self._target_temperature = 21
        self._precision = 1
        self._attr_supported_features = SUPPORT_FLAGS
        #ADDED For TEmperature Range
        self._attr_max_temp=30
        self._attr_min_temp=16
        self.preset_mode=20
       
        self._current_temperature = None 


    mode_mapping = {"dry": 4, "fan_only": 3, "auto": 2, "cool": 0, "off": 0}

    @property
    def current_temperature(self) -> float | None:
        """Return the current temperature."""
        return self._current_temperature

    @property
    def name(self):
        return "AIR Conditioner"
    
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
    
    #Both Function ADDED for Min Max Temperature
    @property
    def min_temp(self):
        """Return the polling state."""
        return self._attr_min_temp
        
    @property
    def max_temp(self):
        """Return the polling state."""
        return self._attr_max_temp
    @property
    def target_temperature_step(self):
        """Return the supported step of target temperature."""
        return self._attr_precision

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return ["dry","fan_only", "auto", "cool", "off"]

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
  
    async def async_turn_on(self):
        await self.send_command(power=1)
        self._state = STATE_ON

    async def async_turn_off(self):
        await self.send_command(power=0)
        self._state = STATE_OFF


    async def async_update(self):
        """Update the state of the Tuya AC."""
        try:
            # Use Tuya Open API to get the current device status
            result = await self.hass.async_add_executor_job(
                self._openapi.get, f"/v2.0/infrareds/d79634ca31ef0ae8807vlh/remotes/d7af1190782799d1a6fu9u/ac/status"
            )
            print(result)
            # Extract relevant information from the result
            if result.get("success", False) and result.get("result", {}):
                status = result["result"].get("power")
                temperature = int(result["result"].get("temp"))
                mode = int(result["result"].get("mode"))

                if not isinstance(temperature, (int, float)):
                    _LOGGER.warning("Received invalid temperature value: %s", temperature)
                    temperature = temperature
                   
                if not isinstance(mode, (int, float)):
                    _LOGGER.warning("Received invalid temperature value: %s", temperature)
                    mode= mode
                # Update the internal state variables
                if status == "on":
                    self._state = STATE_ON
                elif status == "off":
                    self._state = STATE_OFF
                
                if temperature is not None:
                    self._current_temperature = temperature
               
                
                mode_value = self.mode_mapping.get(mode)
                if mode_value is not None:
                    self._hvac_mode = mode_value

                
                    
                # Update Home Assistant state
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"Error updating Tuya AC status: {e}")

    async def send_command(self, power):
        """Helper method to turn on/off the AC."""
       
        try:
            command_payload = {
                "power": power,
                
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

    async def async_set_hvac_mode(self, hvac_mode):
        mode_mapping = {"dry":4,"fan_only": 3, "auto": 2, "cool": 0, "off": 0}
        mode_value = mode_mapping.get(hvac_mode)
        if mode_value is not None:
            if hvac_mode == "off":
                power = 0
            else:
                power = 1
            
            command_payload = {
                "power": power,
                "mode": mode_value,
                
            }
            body_json = json.dumps(command_payload)
            body_dict = json.loads(body_json)

            try:
                # Execute the blocking call using async_add_executor_job
                result = await self.hass.async_add_executor_job(
                    self._openapi.post,
                    "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command",
                    body_dict
                )
                _LOGGER.debug(result)
            except Exception as e:
                _LOGGER.error(f"Error in sending HVAC mode command: {e}")
                return
            
            self._hvac_mode = hvac_mode
            self.async_write_ha_state()
        else:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        mode_mapping = {"low": 1, "medium": 2, "high": 3, "auto": 0,}  # Add more mappings as needed
        mode_value = mode_mapping.get(fan_mode)
        if mode_value is not None:
            command_payload = {
                "power": 1,
                "wind": mode_value,
                
            }
            body_json = json.dumps(command_payload)
            body_dict = json.loads(body_json)

            try:
                # Execute the blocking call using async_add_executor_job
                result = await self.hass.async_add_executor_job(
                    self._openapi.post,
                    "/v2.0/infrareds/d79634ca31ef0ae8807vlh/air-conditioners/d7af1190782799d1a6fu9u/scenes/command",
                    body_dict
                )
                _LOGGER.debug(result)
            except Exception as e:
                _LOGGER.error(f"Error in sending fan mode command: {e}")
                return
            
            self._fan_mode = fan_mode
            self.async_write_ha_state()
        else:
            _LOGGER.warning("Unsupported fan mode: %s", fan_mode)
            
    async def async_set_temperature(self, **kwargs):
        raise NotImplementedError()

    async def async_set_temperature(self, **kwargs):
        """Set new target temperatures."""
        power = kwargs.get(ATTR_HVAC_MODE)
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        temperature = kwargs.get(ATTR_TEMPERATURE)
        command_payload = {
                "power": 1,
                "mode":hvac_mode,
                "temp" : temperature
            }
        body_json = json.dumps(command_payload)
        body_dict = json.loads(body_json)
        

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
