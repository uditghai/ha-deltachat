from homeassistant.components.text import TextEntity
from .const import DOMAIN, DC_DISPLAY_NAME, DC_BIO, CONF_DISPLAY_NAME, CONF_BIO

async def async_setup_entry(hass, entry, async_add_entities):
    account = entry.runtime_data["account"]
    async_add_entities([
        DeltaChatProfileText(account, entry, DC_DISPLAY_NAME, "Profile Name", "mdi:account-edit", CONF_DISPLAY_NAME),
        DeltaChatProfileText(account, entry, DC_BIO, "Profile Bio", "mdi:card-text-outline", CONF_BIO)
    ])

class DeltaChatProfileText(TextEntity):
    """Text entity to change Delta Chat Profile settings."""

    def __init__(self, account, entry, dc_key, name, icon, runtime_config_key):
        self._account = account
        self._dc_key = dc_key  # 'displayname' or 'selfstatus'
        self._attr_name = name
        self._attr_icon = icon
        self._entry = entry
        self._runtime_config_key = runtime_config_key
        self._attr_unique_id = f"{entry.entry_id}_{dc_key}"
        
        # Links it to the same device card
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
        }
        self._attr_native_value = self._entry.runtime_data.get(self._runtime_config_key)

    async def async_update(self) -> None:
        """Fetch current name/bio from RPC."""
        self._attr_native_value = await self.hass.async_add_executor_job(
            self._account.get_config, self._dc_key
        )

    async def async_set_value(self, value: str) -> None:
        """Update the name/bio on the Delta Chat server."""
        await self.hass.async_add_executor_job(
            self._account.set_config, self._dc_key, value
        )
        self._entry.runtime_data[self._runtime_config_key] = value
        self._attr_native_value = value
        self.async_write_ha_state()