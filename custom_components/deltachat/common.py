import logging
from .const import CONF_ID_CAT_SEP, CONF_ID_ACC_CM_SEP, DELTACHAT_MEDIA_CATEGORY
from homeassistant.core import callback

_LOGGER = logging.getLogger(__name__)

def get_chats(account):
    chat_list = []
    clist = account.get_chatlist(snapshot=True)
    for c in clist:
        chat_list.append(
            {
                "id": c.id,
                "title": c.get('name') or c.get('title') or c.get('subtitle') or "Direct Message",
                "type_id": c.get('type') or "Direct Message"
            })
    return chat_list


def extract_id_from_string(text: str) -> int | None:
    """
        Extracts Id from a String in format str(id) like "Chat Name (2)"
        Only used in migration for older version
    """
    if "(" in text and ")" in text:
        return to_int(text.strip().split('(')[-1].strip(')'))
    else:
        return None

def to_int(value: str | None) -> int | None:
    """
        Converts string to int, returns None if it fails.
        Only used in extract_id_from_string which is used for migration purposes only.
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

@callback
def get_account_chat_message_id(combined_id) -> tuple[int,int|None]:
    """
        Used to convert Message format id / id:id into tuples
    """
    ids = combined_id.split(CONF_ID_ACC_CM_SEP)
    if len(ids) < 1 or len(ids) > 2:
        raise ValueError(f"incorrect ID {combined_id}")
    else:
        account_id = int(ids[0])
        chat_message_id = int(ids[1]) if len(ids) >1 and ids[1] else None
        return account_id, chat_message_id

@callback
def get_category_get_account_chat_message_id(id) ->tuple[str,int,int|None]:
    """
        Used to convert Message format category-id / category-id:id into tuples
    """
    category, _, sub_id = (id or "").partition(CONF_ID_CAT_SEP)
    account_id, chat_or_message_id = get_account_chat_message_id(sub_id)
    return category, account_id, chat_or_message_id

@callback
def create_id(category:str, account_id:int, chat_or_message_id:int|None = None) -> str:
    """
        Create Id in format category-id / category-id:id from their tuples
    """
    if category == DELTACHAT_MEDIA_CATEGORY.ACCOUNT:
        return f"{category.lower()}{CONF_ID_CAT_SEP}{account_id}"
    elif category in [DELTACHAT_MEDIA_CATEGORY.CHAT, DELTACHAT_MEDIA_CATEGORY.MESSAGE] and account_id and chat_or_message_id:
        return f"{category.lower()}{CONF_ID_CAT_SEP}{account_id}{CONF_ID_ACC_CM_SEP}{chat_or_message_id}"
    else:
        raise ValueError(f"Incorrect category={category}, account_id={account_id}, chat_or_message_id={chat_or_message_id}")