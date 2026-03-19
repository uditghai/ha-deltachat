"""Config flow for Delta Chat integration."""
from __future__ import annotations

import os
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, CONF_DISPLAY_NAME, CONF_BIO,CONF_SERVER, FLOW_TYPE, FLOW_TYPE_CREATE, FLOW_TYPE_EXISTING, DEFAULT_NEW_ACCOUNT_URL

OPTIONS_SCHEMA = vol.Schema({
    vol.Required(CONF_DISPLAY_NAME, default="HA Bot"): str,
    vol.Optional(CONF_BIO, default="bio"): str,
})

class DeltaChatConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Delta Chat."""

    VERSION = 1

    def __init__(self):
        """Initialize the flow."""
        self.data: dict[str, Any] = {}

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step: Choose login or create."""
        return self.async_show_menu(
            step_id="user",
            menu_options=[FLOW_TYPE_EXISTING, FLOW_TYPE_CREATE]
        )

    async def async_step_existing(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step for logging into a standard Email/Delta Chat account."""
        errors = {}
        if user_input is not None:
            # TODO Check if we can validate creds before proceeding
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            # Existing Email / Password flow
            user_input[FLOW_TYPE]= FLOW_TYPE_EXISTING

            return self.async_create_entry(
                title=user_input[CONF_EMAIL], 
                data=user_input
            )

        return self.async_show_form(
            step_id=FLOW_TYPE_EXISTING,
            data_schema=vol.Schema({
                vol.Required(CONF_EMAIL): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors=errors,
        )

    async def async_step_create(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step to automate Chatmail profile creation."""
        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_profile_extras()

        return self.async_show_form(
            step_id=FLOW_TYPE_CREATE,
            data_schema=vol.Schema({
                vol.Required(CONF_DISPLAY_NAME, default="HA DeltaChat Bot"): str,
                vol.Optional(CONF_SERVER, default = DEFAULT_NEW_ACCOUNT_URL): str,
            })
        )

    async def async_step_profile_extras(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Optional step for Avatar and Bio."""
        if user_input is not None:
            bio = user_input.get(CONF_BIO)
            
            return self.async_create_entry(
                title=self.data[CONF_DISPLAY_NAME],
                data={**self.data, CONF_BIO: bio, FLOW_TYPE: FLOW_TYPE_CREATE}
            )

        # TODO merge this with the options flow OPTIONS_SCHEMA
        return self.async_show_form(
            step_id="profile_extras",
            data_schema=vol.Schema({
                vol.Optional(CONF_BIO, default="Automated Home Assistant Bot"): selector.TextSelector(
                    selector.TextSelectorConfig(multiline=True)
                )
            })
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return DeltaChatOptionsFlowHandler()

class DeltaChatOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options (updating Bio) after setup."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA, self.config_entry.options
            ),
        )
