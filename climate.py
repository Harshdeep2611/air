from tuya_connector import TuyaOpenAPI
import json
import logging
from homeassistant.components.climate import ClimateEntity, PLATFORM_SCHEMA
from homeassistant.const import (
    STATE_ON, STATE_OFF, TEMP_CELSIUS, ATTR_TEMPERATURE, PRECISION_WHOLE
)
from homeassistant.components.climate.const import (
    HVAC_MODE_OFF, SUPPORT_TARGET_TEMPERATURE, SUPPORT_PRESET_MODE,
    SUPPORT_TARGET_TEMPERATURE_RANGE, SUPPORT_FAN_MODE, SUPPORT_SWING_MODE,ATTR_HVAC_MODE
)
from homeassistant.helpers import config_validation as cv
import voluptuous as vol
from homeassistant.const import (
    ATTR_TEMPERATURE, PRECISION_WHOLE
)

_LOGGER = logging.getLogger("air")
CONF_NAME = "name"
CONF_ACCESS_ID = 'access_id'
CONF_ACCESS_KEY = 'access_key'
API_ENDPOINT = "https://openapi.tuyain.com"
CONF_DEVICE_ID = 'device_id'
CONF_REMOTE_ID = 'remote_id'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_ACCESS_ID): cv.string,
    vol.Required(CONF_ACCESS_KEY): cv.string,
    vol.Required(CONF_REMOTE_ID): cv.string
})

SUPPORT_FLAGS = (
    SUPPORT_TARGET_TEMPERATURE
    | SUPPORT_PRESET_MODE
    | SUPPORT_TARGET_TEMPERATURE_RANGE
    | SUPPORT_FAN_MODE
    | SUPPORT_SWING_MODE
)

def setup_platform(hass, config, add_entities, discovery_info=None):
    access_id = config.get(CONF_ACCESS_ID)
    access_key = config.get(CONF_ACCESS_KEY)
    
    ac = {
        "name": config[CONF_NAME],
        "device_id": config[CONF_DEVICE_ID],
        "access_id": config[CONF_ACCESS_ID],
        "access_key": config[CONF_ACCESS_KEY],
        "remote_id": config[CONF_REMOTE_ID]
    }
    openapi = TuyaOpenAPI(API_ENDPOINT, access_id, access_key)
    openapi.connect()
    add_entities([TuyaClimate(openapi, ac)])

class TuyaClimate(ClimateEntity):
    def __init__(self, openapi, ac):
        self._openapi = openapi
        self._ac = ac
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
        self._attr_max_temp = 30
        self._attr_min_temp = 16
        self.preset_mode = 20
        self._current_temperature = None
        self._state = STATE_OFF

    mode_mapping = {"dry": 4, "fan_only": 3, "auto": 2, "cool": 0, "off": 0}

    @property
    def current_temperature(self) -> float | None:
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
        return self._target_temperature

    @property
    def min_temp(self):
        return self._attr_min_temp

    @property
    def max_temp(self):
        return self._attr_max_temp

    @property
    def target_temperature_step(self):
        return self._attr_precision

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def hvac_modes(self):
        return ["dry", "fan_only", "auto", "cool", "off"]

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
        try:
            result = await self.hass.async_add_executor_job(
                self._openapi.get, f"/v2.0/infrareds/{self._ac['device_id']}/remotes/{self._ac['remote_id']}/ac/status"
            )
            if result.get("success", False) and result.get("result", {}):
                status = result["result"].get("power")
                temperature = int(result["result"].get("temp"))
                mode = int(result["result"].get("mode"))

                if status == "on":
                    self._state = STATE_ON
                elif status == "off":
                    self._state = STATE_OFF
                
                if temperature is not None:
                    self._current_temperature = temperature
               
                mode_value = self.mode_mapping.get(mode)
                if mode_value is not None:
                    self._hvac_mode = mode_value
                self.async_write_ha_state()

        except Exception as e:
            _LOGGER.error(f"Error updating Tuya AC status: {e}")

    async def send_command(self, power):
        try:
            command_payload = {"power": power}
            result = await self.hass.async_add_executor_job(self._openapi.post,
                f"/v2.0/infrareds/{self._ac['device_id']}/air-conditioners/{self._ac['remote_id']}/scenes/command", command_payload
            )
            _LOGGER.debug(result)
        except Exception as e:
            _LOGGER.error(f"Error in send_command: {e}")

    async def async_set_hvac_mode(self, hvac_mode):
        mode_mapping = {"dry":4, "fan_only": 3, "auto": 2, "cool": 0, "off": 0}
        mode_value = mode_mapping.get(hvac_mode)
        if mode_value is not None:
            if hvac_mode == "off":
                power = 0
            else:
                power = 1
            
            command_payload = {"power": power, "mode": mode_value}
            try:
                result = await self.hass.async_add_executor_job(
                    self._openapi.post,
                    f"/v2.0/infrareds/{self._ac['device_id']}/air-conditioners/{self._ac['remote_id']}/scenes/command",
                    command_payload
                )
                _LOGGER.debug(result)
            except Exception as e:
                _LOGGER.error(f"Error in sending HVAC mode command: {e}")
            
            self._hvac_mode = hvac_mode
            self.async_write_ha_state()
        else:
            _LOGGER.warning("Unsupported HVAC mode: %s", hvac_mode)

    async def async_set_fan_mode(self, fan_mode):
        mode_mapping = {"low": 1, "medium": 2, "high": 3, "auto": 0}
        mode_value = mode_mapping.get(fan_mode)
        if mode_value is not None:
            command_payload = {"power": 1, "wind": mode_value}
            try:
                result = await self.hass.async_add_executor_job(
                    self._openapi.post,
                    f"/v2.0/infrareds/{self._ac['device_id']}/air-conditioners/{self._ac['remote_id']}/scenes/command",
                    command_payload
                )
                _LOGGER.debug(result)
            except Exception as e:
                _LOGGER.error(f"Error in sending fan mode command: {e}")
            
            self._fan_mode = fan_mode
            self.async_write_ha_state()
        else:
            _LOGGER.warning("Unsupported fan mode: %s", fan_mode)

    async def async_set_temperature(self, **kwargs):
        hvac_mode = kwargs.get(ATTR_HVAC_MODE)
        temperature = kwargs.get(ATTR_TEMPERATURE)
        command_payload = {"power": 1, "mode": hvac_mode, "temp": temperature}

        try:
            result = await self.hass.async_add_executor_job(self._openapi.post,
                f"/v2.0/infrareds/{self._ac['device_id']}/air-conditioners/{self._ac['remote_id']}/scenes/command",
                command_payload
            )
            _LOGGER.debug(result)
        except Exception as e:
            _LOGGER.error(f"Error in setting temperature: {e}")

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

        self.async_write_ha_state()
