import os
import shutil
import tempfile
import mimetypes
import httpx
import logging
from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.helpers.typing import ConfigType

from homeassistant.components import media_source
from deltachat_rpc_client import Rpc, DeltaChat, Bot, events, Account
# Add these to your other imports at the top
from . import select as deltachat_select
from . import sensor as deltachat_sensor
from . import const
from .common import get_chats
from .const import DOMAIN, DEFAULT_NEW_ACCOUNT_URL, CONF_EMAIL, CONF_PASSWORD,CONF_BIO,CONF_SERVER, FLOW_TYPE, FLOW_TYPE_CREATE, FLOW_TYPE_EXISTING, DC_EMAIL, DC_PASSWORD, DC_DISPLAY_NAME, DC_BIO

_LOGGER = logging.getLogger(__name__)
PLATFORMS = ["sensor", "select","text","notify"]

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    # 1. Setup paths
    data_dir = hass.config.path(STORAGE_DIR, DOMAIN)
    if not os.path.exists(data_dir):
        await hass.async_add_executor_job(os.makedirs, data_dir)

    def start_rpc():
        if DOMAIN not in hass.data:
            hass.data[DOMAIN] = {}

        if "rpc" not in hass.data[DOMAIN]:
            rpc = Rpc(accounts_dir=data_dir)
            rpc.start()
            hass.data[DOMAIN]["rpc"] = rpc
        else:
            rpc = hass.data[DOMAIN]["rpc"]

        if "dc" not in hass.data[DOMAIN]:
            dc = DeltaChat(rpc)
            hass.data[DOMAIN]["dc"] = dc

    await hass.async_add_executor_job(start_rpc)
    setup_services(hass)
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Delta Chat from a config entry."""

    # TODO add a feature to allow already configured accounts in DC to be added to HA
    def configure_account():
        rpc = hass.data[DOMAIN]["rpc"]
        dc = hass.data[DOMAIN]["dc"]

        accounts = dc.get_all_accounts()
        # check if account in this entry is already configured
        if "account_id" in entry.data:
            account_id = entry.data.get("account_id")
            account = next((x for x in accounts if x.id == account_id), None)
            if account:
                return rpc, account
            else:
                _LOGGER.warning(f"account_id entry found but no account in DeltaChat, resetting account_id: {account_id}")
                account_id = None

        # Create Account based on flow selected
        flow_type = entry.data.get(FLOW_TYPE)
        
        if flow_type == FLOW_TYPE_CREATE:

            account = dc.add_account()
            qa_config = entry.data.get(CONF_SERVER, DEFAULT_NEW_ACCOUNT_URL)
            account.set_config_from_qr(qa_config)
        elif flow_type == FLOW_TYPE_EXISTING:
            email = entry.data.get(CONF_EMAIL)
            pwd = entry.data.get(CONF_PASSWORD)
            
            # recheck if any account with this email already exists in dc
            if account := next((ac for ac in accounts if ac.get_config(DC_EMAIL) == email), None):
                _LOGGER.warning(f"Skip adding the account with email {email} again.")
            else:
                account = dc.add_account()
                account.set_config(DC_EMAIL, email)
                account.set_config(DC_PASSWORD, pwd)

        # configure bio and bot value in both create and existing creds scenario
        if bio := entry.data.get(CONF_BIO):
            account.set_config(DC_BIO, bio)
        
        account.set_config("bot", "1")
        account.configure()

        return rpc, account

    rpc, account = await hass.async_add_executor_job(configure_account)
    if "account_id" not in entry.data:
        hass.config_entries.async_update_entry(entry, data={**entry.data, "account_id": account.id})

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
            return

        hass.add_job(
            hass.bus.async_fire,
            "deltachat_message_received",
            {
                "to": account_address,
                "to_name": account_name,
                "text": snap.text,
                "sender": snap.from_id,
                "chat_id": snap.chat_id
            }
        )

    bot = Bot(account, hooks)

    # Store everything in runtime_data
    entry.runtime_data = {"rpc": rpc, "bot": bot, "account": account}
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
        
        if not entry:
            raise ValueError(f"Config entry {entry_id} not found")

        account = entry.runtime_data["account"]
        
        target = call.data["target"]
        message = call.data.get("message")
        file = call.data.get("file")
        final_path = None
        temp_path = None


        if isinstance(file, dict):
            uri = file.get("media_content_id")
            mime_type = file.get("media_content_type", "")

            # Determine the suffix (e.g., .mp3) from the mime type
            suffix = mimetypes.guess_extension(mime_type)
            if not suffix:
                MIME_MAP = {
                    "audio/mp3": ".mp3",
                    "audio/mpeg": ".mp3",
                    "image/jpg": ".jpg",
                }
                suffix = MIME_MAP.get(mime_type, "")
            _LOGGER.debug(f"uri={uri}, mime_type={mime_type}, suffix={suffix}")
            if uri and uri.startswith("media-source://"):
                sourced_media = await media_source.async_resolve_media(hass, uri, None)
                url = sourced_media.url
                if url.startswith("/"):
                    url = f"http://127.0.0.1:8123{url}"
                with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as temp_buffer:
                    temp_path = temp_buffer.name
                    async with httpx.AsyncClient() as client:
                        # Home Assistant provides a URL, we fetch it locally
                        resp = await client.get(url)
                        temp_buffer.write(resp.content)
                final_path = temp_path
                _LOGGER.warning("Creating temporary file {final_path}")
            else:
                final_path = uri
        else:
            final_path = file

        def send():
            try:
                chat_id = int(target)
                chat = account.get_chat_by_id(chat_id)
            except (ValueError, TypeError):
                chat = account.create_contact(target).create_chat()
            try:
                chat.send_message(text=message,file=final_path)
            except Exception as err:
                _LOGGER.exception(f"Delta Chat failed to send message: {err}. Message: {message}, File Path used: {file}, final_path:{final_path}")
                raise
            finally:
                # Cleanup: Delete the temp file after the sync task is done
                if temp_path and os.path.exists(temp_path) and "tmp" in temp_path:
                    os.remove(temp_path)
                    _LOGGER.warning("Removed temporary file {temp_path}")
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
        account_id = call.data.get("account_id")
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
    account_id = entry.data.get("account_id")
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
