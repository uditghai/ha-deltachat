from homeassistant.components.notify import NotifyEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.exceptions import ServiceValidationError
from .const import CONF_DEFAULT_CHAT_ID, DOMAIN, DC_DISPLAY_NAME

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Delta Chat notify entities."""

    bot = entry.runtime_data["bot"]
    
    async_add_entities([DeltaChatNotificationEntity(bot, entry)])

class DeltaChatNotificationEntity(NotifyEntity):
    """Notification entity for a Delta Chat account."""

    def __init__(self, bot, entry):
        self.bot = bot
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_notifier"
        self._attr_name = f"Delta Chat ({bot.account.get_config(DC_DISPLAY_NAME)})"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)}
        )

    async def async_send_message(self, message: str, title: str | None = None, target: list[str] | None = None, data: dict | None = None) -> None:
        """Send a message to a specific target chat."""
        if title:
            message = f"{title}\n\n{message}"

        default_chat_id = self._entry.data.get(CONF_DEFAULT_CHAT_ID)
        if not target and not default_chat_id:
            raise ServiceValidationError("No Default chat id defined for this device")
        # If no target is provided, get the default chat id
        chat_ids = target or [default_chat_id]

        for chat_id in chat_ids:
            await self.hass.async_add_executor_job(
                self.bot.account.get_chat_by_id(chat_id).send_text, 
                message
            )
