"""Config flow for Delta Chat integration."""
from __future__ import annotations
import logging
import os
import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import selector
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, CONF_EMAIL, CONF_PASSWORD, CONF_SERVER, FLOW_TYPE, FLOW_TYPE_CREATE, FLOW_TYPE_EXISTING, DEFAULT_NEW_ACCOUNT_URL, DEFAULT_DISPLAY_NAME
_LOGGER = logging.getLogger(__name__)
###
# Version 1:
# entry.data={'account_id': 1, 'bio': '', 'display_name': '', 'flow_type': 'create', 'server': ''}, entry.options = {'default_chat_id': 'Name (ID)'}
# 
# Version 2:
# entry.data={'account_id': 1, 'flow_type': 'create', 'server': '','default_chat_id':10,'default_chat_title':'Name (ID)','ephemeral_time':111}
# 
###
class DeltaChatConfigFlow(config_entries.ConfigFlow, domain = DOMAIN):
    """Handle a config flow for Delta Chat."""

    VERSION = 2
    MINOR_VERSION = 1

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
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            # Existing Email / Password flow
            user_input[FLOW_TYPE] = FLOW_TYPE_EXISTING

            return self.async_create_entry(
                title = user_input[CONF_EMAIL], 
                data = user_input
            )

        return self.async_show_form(
            step_id = FLOW_TYPE_EXISTING,
            data_schema = vol.Schema({
                vol.Required(CONF_EMAIL): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.EMAIL)
                ),
                vol.Required(CONF_PASSWORD): selector.TextSelector(
                    selector.TextSelectorConfig(type=selector.TextSelectorType.PASSWORD)
                ),
            }),
            errors = errors,
        )

    async def async_step_create(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        """Step to automate Chatmail profile creation."""
        if user_input is not None:
            self.data.update(user_input)
            return self.async_create_entry(
                title = DEFAULT_DISPLAY_NAME,
                data = {**self.data, FLOW_TYPE: FLOW_TYPE_CREATE}
            )

        return self.async_show_form(
            step_id = FLOW_TYPE_CREATE,
            data_schema = vol.Schema({
                vol.Required(CONF_SERVER, default = DEFAULT_NEW_ACCOUNT_URL): str
            })
        )
