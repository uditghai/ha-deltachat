import logging

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
    if "(" in text and ")" in text:
        return to_int(text.strip().split('(')[-1].strip(')'))
    else:
        return None

def to_int(value: str | None) -> int | None:
    """Converts string to int, returns None if it fails."""
    try:
        return int(value)
    except (ValueError, TypeError):
        return None