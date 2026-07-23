import os
import tempfile
import mimetypes
import httpx
import logging
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.typing import ConfigType

from homeassistant.components.media_source import async_resolve_media
from homeassistant.components.media_player.browse_media import async_process_play_media_url
from deltachat_rpc_client import Rpc, DeltaChat, Bot, events, Account


from .media_source import DeltaChatMediaView
from .common import get_chats,extract_id_from_string
from .const import (
    DOMAIN,
    DEFAULT_NEW_ACCOUNT_URL,
    CONF_EMAIL,
    CONF_PASSWORD,
    CONF_DISPLAY_NAME,
    CONF_BIO,CONF_SERVER,
    FLOW_TYPE,
    FLOW_TYPE_CREATE,
    FLOW_TYPE_EXISTING,
    DC_EMAIL, 
    DC_PASSWORD,
    DC_DISPLAY_NAME,
    DC_BIO, CONF_ACCOUNT_ID,
    CONF_DEFAULT_CHAT_TITLE,
    CONF_DEFAULT_CHAT_ID,
    DEFAULT_DISPLAY_NAME,
    DEFAULT_BIO,
    CONF_DC_VERSION)

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "select","text","notify","image"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    # 1. Setup paths
    data_dir = hass.config.path(STORAGE_DIR, DOMAIN)
    if not os.path.exists(data_dir):
        await hass.async_add_executor_job(os.makedirs, data_dir)

    def start_rpc():
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        if "rpc" not in hass.data[DOMAIN]:
            rpc = Rpc(accounts_dir = data_dir)
            rpc.start()
            hass.data[DOMAIN]["rpc"] = rpc
        else:
            rpc = hass.data[DOMAIN]["rpc"]

        if "dc" not in hass.data[DOMAIN]:
            dc = DeltaChat(rpc)
            hass.data[DOMAIN]["dc"] = dc

    await hass.async_add_executor_job(start_rpc)
    setup_services(hass)
    hass.http.register_view(DeltaChatMediaView(hass))
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Delta Chat from a config entry."""

    _LOGGER.debug(f"[async_setup_entry] DeltaChat entry.title={entry.title}, entry.data={entry.data}, entry.options = {entry.options}")

    # TODO add auto discovery of already configured accounts
    def configure_account():
        rpc = hass.data[DOMAIN]["rpc"]
        dc = hass.data[DOMAIN]["dc"]

        accounts = dc.get_all_accounts()
        # check if account in this entry is already configured
        if CONF_ACCOUNT_ID in entry.data:
            account_id = entry.data.get(CONF_ACCOUNT_ID)
            account = next((x for x in accounts if x.id == account_id), None)
            if account:
                return rpc, account
            else:
                _LOGGER.warning(f"{DOMAIN} - {CONF_ACCOUNT_ID} entry found but no account in DeltaChat, resetting {CONF_ACCOUNT_ID}: {account_id}")
                account_id = None

        # Create Account based on flow selected
        flow_type = entry.data.get(FLOW_TYPE,FLOW_TYPE_CREATE)
        
        if flow_type == FLOW_TYPE_CREATE:

            account = dc.add_account()
            qr_config = entry.data.get(CONF_SERVER, DEFAULT_NEW_ACCOUNT_URL)
            account.set_config_from_qr(qr_config)
            #TODO Add async_set_unique_id and _abort_if_unique_id_configured checks if unique id is not already configured.

        elif flow_type == FLOW_TYPE_EXISTING:
            email = entry.data.get(CONF_EMAIL)
            pwd = entry.data.get(CONF_PASSWORD)
            
            # recheck if any account with this email already exists in dc
            if account := next((ac for ac in accounts if ac.get_config(DC_EMAIL) == email), None):
                _LOGGER.error(f"Account already exists with email {email}.")
            else:
                account = dc.add_account()
                account.set_config(DC_EMAIL, email)
                account.set_config(DC_PASSWORD, pwd)

        # Configure display name, bio and bot value in both create and existing creds scenario
        if not account.get_config(DC_BIO):
            account.set_config(DC_BIO, DEFAULT_BIO)
        
        if not account.get_config(DC_DISPLAY_NAME):
            account.set_config(DC_DISPLAY_NAME,DEFAULT_DISPLAY_NAME)

        account.set_config("bot", "1")
        account.configure()

        return rpc, account

    rpc, account = await hass.async_add_executor_job(configure_account)
    # Get dynamic data to store in runtime_data
    account_info = account.get_info()
    runtime_display_name = account.get_config(DC_DISPLAY_NAME)
    runtime_bio = account.get_config(DC_BIO)

    # This will trigger only first time when no account ID is configured against the entry created
    if CONF_ACCOUNT_ID not in entry.data:
        new_data = {**entry.data, CONF_ACCOUNT_ID: account.id}
        hass.config_entries.async_update_entry(entry, data=new_data,title=runtime_display_name)
    elif runtime_display_name != entry.title:
        hass.config_entries.async_update_entry(entry, title=runtime_display_name)

    # Setup Hooks (Event Listeners)
    hooks = events.HookCollection()

    @hooks.on(events.NewMessage)
    def on_new_message(event: events.NewMessage):
        snap = event.message_snapshot
        account_address = account.get_config(DC_EMAIL)
        account_name = account.get_config(DC_DISPLAY_NAME)
        _LOGGER.debug(f"New message from {snap.from_id}: {snap}")
        
        # Ignore info / system messages.
        if snap.is_info:
            _LOGGER.debug(f"System Message Info: to:{account_address}, text:{snap.text}, chat_id:{snap.chat_id}, sender:from_id")
            return
        # TODO ignore blocked senders
        dc_mr_event = {
            "to": account_address,
            "to_name": account_name,
            "sender": snap.from_id
        }
        # Add Additional keys to the event for handling files
        keys = ['text','chat_id','original_msg_id', 'file', 'file_mime','file_name','file_bytes','received_timestamp','subject','timestamp']
        dc_mr_event.update((k, snap[k]) for k in keys)

        hass.add_job(
            hass.bus.async_fire,
            "deltachat_message_received",
            dc_mr_event
        )

    bot = Bot(account, hooks)

    entry.runtime_data = {
        "rpc": rpc,
        "bot": bot,
        "account": account,
        CONF_DISPLAY_NAME: runtime_display_name,
        CONF_BIO: runtime_bio,
        CONF_DC_VERSION: account_info.deltachat_core_version
    }
    _LOGGER.debug("Starting Delta Chat bot event loop")
 
    # Start the bot loop in a background thread
    hass.loop.run_in_executor(None, bot.run_forever)

    # Register platforms (sensor.py) and services
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

def setup_services(hass: HomeAssistant):
    """Register Delta Chat services."""

    async def handle_send_message(call: ServiceCall):
        entry_id = call.data["from_account"]
        entry = hass.config_entries.async_get_entry(entry_id)
        def send():
            try:
                chat_id = int(target)
                chat = account.get_chat_by_id(chat_id)
            except (ValueError, TypeError):
                # TODO validate target is like email
                chat = account.create_contact(target).create_chat()
            try:
                if chat:
                    chat.send_message(text = message,file = final_path)
            except Exception as err:
                _LOGGER.exception(f"{DOMAIN} - failed to send message: {err}. Message: {message}, File Path used: {file}, final_path:{final_path}")
                raise

        if not entry:
            raise ValueError(f"Config entry {entry_id} not found")

        account = entry.runtime_data["account"]

        target = call.data["target"]
        message = call.data.get("message")
        file = call.data.get("file")
        final_path = None

        if isinstance(file, dict):
            uri = file.get("media_content_id")
            mime_type = file.get("media_content_type", "")

            # Determine the suffix (e.g., .mp3) from the mime type
            suffix = mimetypes.guess_extension(mime_type)
            if uri and uri.startswith("media-source://"):
                sourced_media = await async_resolve_media(hass, uri, None)
                url = async_process_play_media_url(hass,sourced_media.url)

                with tempfile.NamedTemporaryFile(suffix = suffix) as temp_buffer:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(url)
                        temp_buffer.write(resp.content)
                    final_path = temp_buffer.name
                    await hass.async_add_executor_job(send)
            else:
                final_path = uri
                await hass.async_add_executor_job(send)
        else:
            final_path = file
            await hass.async_add_executor_job(send)

    async def handle_list_chats(call: ServiceCall) -> ServiceResponse:
        entry_id = call.data["from_account"]
        
        entry = hass.config_entries.async_get_entry(entry_id)
        
        if not entry:
            raise ValueError(f"Config entry {entry_id} not found")

        account = entry.runtime_data["account"]
        
        chats = await hass.async_add_executor_job(get_chats, account)
        return {
            "chats": chats
        }

    async def handle_list_accounts(call: ServiceCall) -> ServiceResponse:
        get_info = call.data.get("get_info",False)
        dc = hass.data[DOMAIN]["dc"]
        
        def get_accounts():
            accounts = dc.get_all_accounts()

            if get_info:
                return [dict(ac.get_info()) for ac in accounts]
            else:
                return [{"id":ac.id,"email":ac.get_config(DC_EMAIL)} for ac in accounts]

        output = await hass.async_add_executor_job(get_accounts)
        return {
            "accounts": output
        }

    async def handle_delete_account(call: ServiceCall) -> ServiceResponse:
        account_id = call.data.get(CONF_ACCOUNT_ID)
        dc = hass.data[DOMAIN]["dc"]

        def remove_account():
            account = Account(dc, account_id)
            account.remove()

        await hass.async_add_executor_job(remove_account)

    hass.services.async_register(DOMAIN, "send_message", handle_send_message)
    hass.services.async_register(DOMAIN, "list_chats", handle_list_chats, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "list_accounts", handle_list_accounts, supports_response=SupportsResponse.ONLY)
    hass.services.async_register(DOMAIN, "delete_account", handle_delete_account)

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Stop the platforms (sensors, etc.)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    return unload_ok

async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove a single account from a shared Delta Chat RPC environment."""
    account_id = entry.data.get(CONF_ACCOUNT_ID)
    dc = hass.data[DOMAIN]["dc"]
    
    def remove_account():
        account = Account(dc, account_id)
        account.remove()

    if dc and account_id:
        try:
            await hass.async_add_executor_job(remove_account)
            _LOGGER.info(f"Account {entry.title} removed from shared RPC server")
        except Exception as err:
            _LOGGER.error(f"Failed to remove account {entry.title}: {err}")


async def async_migrate_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Migrate old entry."""
    _LOGGER.debug(f"{DOMAIN} - Migrating configuration from version {config_entry.version}.{config_entry.minor_version}")

    if config_entry.version == 1:

        old_data = {**config_entry.data}
        old_options = {**config_entry.options}
        # Remove Title, Bio in config and options flow both
        # Translate default chat text to default chat text and title keys in config
        new_data = {}

        new_data[CONF_ACCOUNT_ID] = old_data[CONF_ACCOUNT_ID]
        new_data[FLOW_TYPE] = old_data[FLOW_TYPE]
        
        if CONF_EMAIL in old_data:
            new_data[CONF_EMAIL] = old_data[CONF_EMAIL]

        if CONF_PASSWORD in old_data:
            new_data[CONF_PASSWORD] = old_data[CONF_PASSWORD]

        if CONF_SERVER in old_data:
            new_data[CONF_SERVER] = old_data[CONF_SERVER]

        if old_options and CONF_DEFAULT_CHAT_ID in old_options and type(old_options[CONF_DEFAULT_CHAT_ID]) == str:
            new_data[CONF_DEFAULT_CHAT_TITLE] = old_options[CONF_DEFAULT_CHAT_ID]

            new_data[CONF_DEFAULT_CHAT_ID] = extract_id_from_string(old_options[CONF_DEFAULT_CHAT_ID])
            
        hass.config_entries.async_update_entry(
            config_entry, data = new_data, minor_version = 1, version = 2
        )
        _LOGGER.debug(f"{DOMAIN} - Migrated data: {new_data}")

        return True
    
    return False