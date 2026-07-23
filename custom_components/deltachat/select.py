from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_DEFAULT_CHAT_ID,CONF_DEFAULT_CHAT_TITLE
from .common import get_chats

async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Delta Chat contact selector."""
    account = entry.runtime_data["account"]
    async_add_entities([DeltaChatContactSelect(entry, account)], True)

class DeltaChatContactSelect(SelectEntity):
    """Dropdown to select a Delta Chat contact."""

    def __init__(self, entry, account):
        self._entry = entry
        self._account = account
        self._attr_name = "Active Contact"
        self._attr_unique_id = f"{entry.entry_id}_contact_selector"

        self._attr_device_info = DeviceInfo(
            identifiers = {(DOMAIN, entry.entry_id)}
        )

        default_chat_text = "No Active Chats"
        self._attr_options = {default_chat_text:0}
        self._attr_options_list = [default_chat_text]

    async def async_update(self) -> None:
        """Fetch new data from the RPC server safely."""
        chats = await self.hass.async_add_executor_job(
            lambda: get_chats(self._account)
        )
        self._attr_options = {f"{c.get("title")} ({c.get("id")})":c.get("id") for c in chats}
        # List is only used to display the keys without re-iterating the dict for title on every access to the options property.
        self._attr_options_list = list(self._attr_options)

    @property
    def options(self) -> list[str]:
        """Return options from memory."""
        return self._attr_options_list

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        # Get from entity
        value = self._entry.data.get(CONF_DEFAULT_CHAT_TITLE)

        if value in self._attr_options and value in self._attr_options_list:
            return value
        else:
            return ""

    async def async_select_option(self, option: str) -> None:
        """Handle UI selection."""
        # Save to entity options
        if option in self._attr_options:
            chat_id = self._attr_options[option]
            new_data = {**self._entry.data, CONF_DEFAULT_CHAT_TITLE: option, CONF_DEFAULT_CHAT_ID: chat_id}
            self.hass.config_entries.async_update_entry(self._entry, data = new_data)