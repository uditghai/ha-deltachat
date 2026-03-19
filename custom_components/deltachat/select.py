from homeassistant.components.select import SelectEntity
from homeassistant.helpers.device_registry import DeviceInfo
from .const import DOMAIN, CONF_DEFAULT_CHAT
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
        
        # Link to the same Device Card
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
        )
        self._attr_options = ["No Active Chats"]

    async def async_update(self) -> None:
        """Fetch new data from the RPC server safely."""
        chats = await self.hass.async_add_executor_job(
            lambda: get_chats(self._account)
        )
        self._attr_options = [f"{c.get("title")} ({c.get("id")})" for c in chats]

    @property
    def options(self) -> list[str]:
        """Return options from memory."""
        return self._attr_options

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        # Get from entity options
        value = self._entry.options.get(CONF_DEFAULT_CHAT)
        if value in self._attr_options:
            return value
        else:
            return ""

    async def async_select_option(self, option: str) -> None:
        """Handle UI selection."""
        # Save to entity options
        new_options = {**self._entry.options, CONF_DEFAULT_CHAT: option}
        self.hass.config_entries.async_update_entry(self._entry, options=new_options)