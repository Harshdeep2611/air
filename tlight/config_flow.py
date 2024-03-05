from homeassistant import config_entries
import requests
import logging
from pprint import pformat
import voluptuous as vol
from homeassistant.const import CONF_NAME, CONF_DEVICE_ID, CONF_CLIENT_SECRET
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
import homeassistant.helpers.config_validation as cv
from homeassistant.components.light import PLATFORM_SCHEMA

DOMAIN = "tlight"

_LOGGER = logging.getLogger("tlight")

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional(CONF_NAME, default="Tuya Light"): cv.string,
    vol.Required(CONF_DEVICE_ID): cv.string,
    vol.Required(CONF_CLIENT_SECRET): cv.string
})

class TuyaLightConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    async def async_step_user(self, user_input=None):
        """Handle the initial step when the user adds a new Tuya Light device."""
        if user_input is not None:
            # Handle the user input and create an entry for the configuration
            return self.async_create_entry(title="Tuya Light", data=user_input)

        # Show the user a form to input the necessary details
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required("device_id"): str,
                vol.Required("client_secret"): str,
                # Add any other configuration options specific to your Tuya light here
            }),
        )
