import logging
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import EntityCategory
from .const import DOMAIN, DC_EMAIL, DC_DISPLAY_NAME, DC_BIO
from .common import get_chats


_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, 
    entry: ConfigEntry, 
    async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Delta Chat sensors."""
    data = entry.runtime_data
    bot = data["bot"]
    account = data["account"]
    email = account.get_config(DC_EMAIL)
    
    device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer="Delta Chat (Unofficial)",
        model="DeltaChat Bot",
        serial_number = email,
        hw_version = account.id,
        sw_version="2.44.0", # TODO pull sw version from get_system_info()
        configuration_url=f"https://delta.chat/",
    )

    sensors = [
        DeltaChatLastMessageSensor(bot,device_info,entry),
        DeltaChatLastCommandSensor(bot,device_info,entry),
        DeltaChatTotalChatsSensor(bot,device_info,entry),
        DeltaChatTotalContactsSensor(bot,device_info,entry),
        DeltaChatBotStatusSensor(bot,device_info,entry),
        DeltaChatBotAccountConfiguredSensor(bot,device_info,entry),
        DeltaChatFingerprintSensor(bot,device_info,entry)
    ]
    
    async_add_entities(sensors)

class DeltaChatLastMessageSensor(SensorEntity):
    """Sensor to show the last received message."""
    _attr_name = "Last Message"
    _attr_icon = "mdi:message-text"


    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_last_message"
        self._attr_native_value = "None"
        self._attr_extra_state_attributes = {"sender": None, "time": None}

        self._attr_device_info = device_info

    # Listener handler for deltachat_message_received
    def update_state(self, text, sender, timestamp):
        self._attr_native_value = text
        self._attr_extra_state_attributes["sender"] = sender
        self._attr_extra_state_attributes["time"] = timestamp
        self.async_write_ha_state()

    async def async_added_to_hass(self):
        """Subscribe to bot events when added to HA."""
        self.async_on_remove(
            self.hass.bus.async_listen("deltachat_message_received", self._handle_event)
        )

    @callback
    def _handle_event(self, event):
        """Update sensor when the bot fires an event."""
        data = event.data
        # fire event only when event is for current account
        if data.get("to", "") == entry.entry_id:
            self.update_state(
                        text=data.get("text", ""), 
                        sender=data.get("sender", "Unknown"), 
                        timestamp="Just now"
                    )

class DeltaChatLastCommandSensor(SensorEntity):
    """Sensor to show the last received command."""
    _attr_name = "Last Command"
    _attr_icon = "mdi:console-line"

    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_last_command"
        self._attr_native_value = "None"
        self._attr_device_info = device_info

    def update_state(self, command):
        self._attr_native_value = command
        self.async_write_ha_state()

class DeltaChatTotalChatsSensor(SensorEntity):
    """Sensor showing the total number of chats."""
    _attr_name = "Total Chats"
    _attr_icon = "mdi:forum"

    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_total_chats"
        self._attr_device_info = device_info
        self._chat_count = 0
    @property
    def native_value(self):
        """Fetch the total chat count synchronously."""
        return self._chat_count

    async def async_update(self) -> None:
        """Fetch the total contact count asynchronously."""
        try:
            chat_list = await self.hass.async_add_executor_job(
                get_chats, self.bot.account
            )
            self._chat_count = len(chat_list)
        except Exception as err:
            # Fallback to avoid crashing the integration
            _LOGGER.error(f"DeltaChatTotalChatsSensor: Error {err}")
            self._chat_count = 0

class DeltaChatTotalContactsSensor(SensorEntity):
    """Sensor showing the total number of contacts."""
    _attr_name = "Total Contacts"
    _attr_icon = "mdi:contacts"

    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_total_contacts"
        self._attr_device_info = device_info
        self._contact_count = 0
    @property
    def native_value(self):
        """Fetch the total contact from local var."""
        return self._contact_count
    async def async_update(self) -> None:
        """Fetch the total contact count asynchronously."""
        try:
            # get_info() is the modern way to get account metadata in 2.44
            contacts = await self.hass.async_add_executor_job(
                self.bot.account.get_contacts
            )
            self._contact_count = len(contacts)
        except Exception as err:
            # Fallback to avoid crashing the integration
            _LOGGER.error(f"DeltaChatTotalContactsSensor: Error {err}")
            self._contact_count = 0

class DeltaChatBotStatusSensor(SensorEntity):
    """Sensor showing bot connection status and QR URI."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Bot Status"
    _attr_icon = "mdi:robot-check"


    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_native_value = "Connected"

        # We store the URI in attributes so it doesn't clutter the state
        self._attr_extra_state_attributes = {
            "qr_uri": None,
            "address": bot.account.get_config("addr"),
            "info": bot.account.get_info()
        }
        self._attr_device_info = device_info

    async def async_added_to_hass(self):
        """Fetch the QR URI once the bot is ready."""
        # Fetching the QR URI is an I/O task, do it in executor
        qr_uri = await self.hass.async_add_executor_job(
            self.bot.account.get_qr_code
        )
        self._attr_extra_state_attributes["qr_uri"] = qr_uri
        self.async_write_ha_state()

class DeltaChatBotAccountConfiguredSensor(SensorEntity):
    """Sensor showing Account Configured status."""
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Account Configured"
    _attr_icon = "mdi:robot-check"

    def __init__(self, bot,device_info:DeviceInfo,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_configured"
        self._attr_native_value = bot.account.is_configured()
        self._attr_device_info = device_info

class DeltaChatFingerprintSensor(SensorEntity):
    """Sensor to display the bot's encryption fingerprint."""
    
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_name = "Self Fingerprint"
    _attr_icon = "mdi:fingerprint"

    def __init__(self, bot, device_info,entry):
        self.bot = bot
        self._attr_unique_id = f"{entry.entry_id}_fingerprint"
        self._attr_device_info = device_info

    async def async_update(self) -> None:
        """Fetch the fingerprint from the RPC server safely."""
        try:
            info = await self.hass.async_add_executor_job(
                self.bot.account.get_info
            )
            
            self._attr_native_value = info.get("fingerprint") or "Not Available"

        except Exception as err:
            # Fallback to avoid crashing the integration
            _LOGGER.error("Could not fetch Delta Chat fingerprint: %s", err)
            self._attr_native_value = "Error"
