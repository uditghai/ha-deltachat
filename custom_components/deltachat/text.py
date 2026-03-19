from homeassistant.components.text import TextEntity
from .const import DOMAIN, DC_DISPLAY_NAME, DC_BIO

async def async_setup_entry(hass, entry, async_add_entities):
    account = entry.runtime_data["account"]
    async_add_entities([
        DeltaChatProfileText(account, entry, DC_DISPLAY_NAME, "Profile Name", "mdi:account-edit"),
        DeltaChatProfileText(account, entry, DC_BIO, "Profile Bio", "mdi:card-text-outline")
    ])

class DeltaChatProfileText(TextEntity):
    """Text entity to change Delta Chat Profile settings."""

    def __init__(self, account, entry, key, name, icon):
        self._account = account
        self._key = key  # 'displayname' or 'selfstatus'
        self._attr_name = name
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        # Links it to the same device card
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }
        self._attr_native_value = ""

    async def async_update(self) -> None:
        """Fetch current name/bio from RPC."""
        self._attr_native_value = await self.hass.async_add_executor_job(
            self._account.get_config, self._key
        )

    async def async_set_value(self, value: str) -> None:
        """Update the name/bio on the Delta Chat server."""
        await self.hass.async_add_executor_job(
            self._account.set_config, self._key, value
        )
        self._attr_native_value = value
        self.async_write_ha_state()