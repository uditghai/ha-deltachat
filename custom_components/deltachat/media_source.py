import logging
from typing import List
from pathlib import Path; 
from homeassistant.helpers.storage import STORAGE_DIR
from homeassistant.components.media_player import BrowseError, MediaClass, MediaType
from homeassistant.components.media_source import (
    BrowseMediaSource,
    MediaSource,
    MediaSourceItem,
    PlayMedia,
    Unresolvable
)
from homeassistant.core import HomeAssistant
from deltachat_rpc_client import AttrDict, Rpc, DeltaChat,Account,Chat,Message,JsonRpcError
from .const import (
    DOMAIN,
    DC_DISPLAY_NAME,
    DC_MSG_FILE_MIME,
    DC_MSG_FILE_NAME,
    DC_MSG_FILE_PATH,
    DC_CHAT_PROFILE_IMG,
    DELTACHAT_MEDIA_CATEGORY)

from .common import get_category_get_account_chat_message_id, create_id

_LOGGER = logging.getLogger(__name__)

MEDIA_SOURCE_NAME = "Delta Chat"
async def async_get_media_source(hass: HomeAssistant) -> DeltaChatMediaSource:
    """Set up my media source."""
    return DeltaChatMediaSource(hass)

class DeltaChatMediaSource(MediaSource):
    """Provide media from my integration."""

    name = MEDIA_SOURCE_NAME

    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the media source."""
        super().__init__(DOMAIN)
        self.hass = hass
        self.dc = hass.data[DOMAIN]["dc"]

    async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Resolve a media item to a playable URL."""
        category, account_id, chat_or_message_id = get_category_get_account_chat_message_id(item.identifier)
        if category == DELTACHAT_MEDIA_CATEGORY.MESSAGE and account_id and chat_or_message_id:
            account = Account(self.dc,account_id)
            m = Message(account,chat_or_message_id)
            message_snapshot = m.get_snapshot()
            return PlayMedia(f"/api/deltachat/media/{item.identifier}", message_snapshot[DC_MSG_FILE_MIME])
        raise Unresolvable(f"Could not resolve: {item.identifier}")

    
    def get_all_accounts(self) -> List[BrowseMediaSource]:
        """Get top level accounts for browsing"""

        dc_accounts = self.dc.get_all_accounts()

        return [BrowseMediaSource(
                domain = DOMAIN,
                identifier = create_id(DELTACHAT_MEDIA_CATEGORY.ACCOUNT,ac.id),
                media_class = MediaClass.DIRECTORY ,
                media_content_type = "",
                title = ac.get_config(DC_DISPLAY_NAME),
                thumbnail = f"/api/deltachat/media/{create_id(DELTACHAT_MEDIA_CATEGORY.ACCOUNT,ac.id)}",
                can_play = False,
                can_expand = True,
                children_media_class = MediaClass.DIRECTORY
            )
            for ac in dc_accounts]
    
    def get_all_chats_for_account(self,account_id:int) -> List[BrowseMediaSource]:
        """Get chats for an account for browsing"""

        assert account_id
        try:
            ac = Account(self.dc,account_id)
            chats = ac.get_chatlist(snapshot=True)

            chatlist= [BrowseMediaSource(
                domain = DOMAIN,
                identifier = create_id(DELTACHAT_MEDIA_CATEGORY.CHAT,account_id,c.get('id')),
                media_class = MediaClass.DIRECTORY,
                media_content_type = "",
                title = c.get('name') or c.get('title') or c.get('subtitle') or "Direct Message",
                thumbnail = f"/api/deltachat/media/{create_id(DELTACHAT_MEDIA_CATEGORY.CHAT,account_id,c.get('id'))}",
                can_play = False,
                can_expand = True)
            for c in chats]
            return chatlist
        except JsonRpcError as e:
            return []
    def get_all_media_for_chats(self,account_id:int,chat_id:int) -> List[BrowseMediaSource]:
        """Get all media files for an account + chat for browsing"""

        assert account_id and chat_id

        ac = Account(self.dc,account_id)
        chat = Chat(ac,chat_id)
        messages = chat.get_messages()
        dc_images = []
        for m in messages:
            snap = m.get_snapshot()
            if 'file' in snap and DC_MSG_FILE_MIME in snap and snap[DC_MSG_FILE_MIME]:
                m_id = create_id(DELTACHAT_MEDIA_CATEGORY.MESSAGE,account_id,snap['id'])
                dc_images.append(BrowseMediaSource(
                domain = DOMAIN,
                identifier = m_id,
                media_class = MediaClass.IMAGE,
                media_content_type = snap[DC_MSG_FILE_MIME],
                title = snap[DC_MSG_FILE_NAME],
                thumbnail = f"/api/deltachat/media/{m_id}",
                can_play = (snap[DC_MSG_FILE_MIME]).split("/")[0] == "video",
                can_expand = False))
        return dc_images

    async def async_browse_media(self, item: MediaSourceItem) -> BrowseMediaSource:
        """Browse media.
        will return one of the following based on hierarchy.
        account-<account_id>
        chat-<account_id>:<chat_id>
        message-<account_id>:<message_id>"""

        title = MEDIA_SOURCE_NAME
        if item.identifier:
            children = []
            category, account_id, chat_or_message_id = get_category_get_account_chat_message_id(item.identifier)
            if category == DELTACHAT_MEDIA_CATEGORY.ACCOUNT:
                children = self.get_all_chats_for_account(account_id)
                account = Account(self.dc,account_id)
                title = account.get_config(DC_DISPLAY_NAME)

            elif category == DELTACHAT_MEDIA_CATEGORY.CHAT:
                if chat_or_message_id:
                    children = self.get_all_media_for_chats(account_id = account_id,chat_id = chat_or_message_id)
                    c = Chat(Account(self.dc,account_id),chat_or_message_id)
                    snapshot = c.get_basic_snapshot()
                    title = snapshot.get('name') or snapshot.get('title') or snapshot.get('subtitle') or "Direct Message"
                else:
                    raise BrowseError(f"Unknown item - {item.identifier}, Missing chat_id")
            else:
                raise BrowseError(f"Unknown item - {item.identifier}")
            
            return BrowseMediaSource(
                domain = DOMAIN,
                identifier = item.identifier,
                media_class = MediaClass.DIRECTORY,
                media_content_type = "",
                title = title,
                can_play = False,
                can_expand = True,
                children = children,
                children_media_class = MediaClass.DIRECTORY
            )

        return BrowseMediaSource(
            domain = DOMAIN,
            identifier = None,
            media_class = MediaClass.APP,
            media_content_type = "",
            title = title,
            can_play = False,
            can_expand = True,
            children = self.get_all_accounts(),
            children_media_class = MediaClass.DIRECTORY
        )
    
from aiohttp import web
from homeassistant.components import http

class DeltaChatMediaView(http.HomeAssistantView):
    url = "/api/deltachat/media/{image_id}"
    name = "api:deltachat:media"
    requires_auth = True
    def __init__(self, hass: HomeAssistant) -> None:
        """Initialize the media view."""
        self.hass = hass
        self.dc = hass.data[DOMAIN]["dc"]
    async def get(self, request, image_id):
        _LOGGER.debug(f"{DOMAIN} - DeltaChatMediaView.get image_id={image_id}")
        category, account_id, chat_or_message_id = get_category_get_account_chat_message_id(image_id)
        def get_media_resource():
            try:
                if category == DELTACHAT_MEDIA_CATEGORY.ACCOUNT:
                    assert account_id
                    account = Account(self.dc,account_id)

                    media_path_str = account.get_avatar()
                    if media_path_str:
                        media_path = Path(media_path_str)
                        return web.FileResponse(media_path)

                elif category == DELTACHAT_MEDIA_CATEGORY.CHAT:
                    assert account_id and chat_or_message_id
                    account = Account(self.dc,account_id)
                    c = Chat(account,chat_or_message_id)
                    snapshot = c.get_basic_snapshot()
                    if snapshot and DC_CHAT_PROFILE_IMG in snapshot:
                        media_path_str = snapshot[DC_CHAT_PROFILE_IMG]
                        if media_path_str:
                            media_path = Path(media_path_str)
                            return web.FileResponse(media_path)

                elif category == DELTACHAT_MEDIA_CATEGORY.MESSAGE:
                    assert account_id and chat_or_message_id
                    account = Account(self.dc,account_id)
                    m = Message(account,chat_or_message_id)
                    message_snapshot = m.get_snapshot()
                    if message_snapshot and message_snapshot[DC_MSG_FILE_PATH]:
                        media_path = Path(message_snapshot[DC_MSG_FILE_PATH])
                        return web.FileResponse(media_path)

                # Exit Path for all neg conditions
                raise web.HTTPNotFound
            except JsonRpcError as x:
                _LOGGER.error(x)
                raise web.HTTPNotFound

        return await self.hass.async_add_executor_job(get_media_resource)