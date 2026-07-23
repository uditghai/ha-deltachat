DOMAIN = "deltachat"

# Config Flow Attributes
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_DISPLAY_NAME = "display_name"
CONF_AVATAR_PATH = "avatar_path"
CONF_BIO = "bio"
CONF_SERVER = "server"
CONF_ACCOUNT_ID = "account_id"
CONF_EPHEMERAL_TIMER = "ephemeral_timer"
CONF_EPHEMERAL_TIMER_DEFAULT_VALUE:float = 0
CONF_AUTO_DELETE = "auto_delete_seconds"
CONF_DEFAULT_CHAT_ID = "default_chat_id"
CONF_DEFAULT_CHAT_TITLE = "default_chat_title"
CONF_DC_VERSION = "deltachat_core_version"

# Account Attributes in DC RPC
DC_EMAIL = "addr"
DC_PASSWORD = "mail_pw"
DC_DISPLAY_NAME = "displayname"
DC_BIO = "selfstatus"

# Chat Attributes
DC_CHAT_PROFILE_IMG = "profile_image"
# Message Attributes
DC_MSG_FILE_PATH = "file"
DC_MSG_FILE_MIME = "file_mime"
DC_MSG_FILE_NAME = "file_name"
#Flow Types
FLOW_TYPE = "flow_type"
FLOW_TYPE_CREATE = "create"
FLOW_TYPE_EXISTING = "existing"

# Chatmail servers allow "instant" account creation via a specific URL format
DEFAULT_NEW_ACCOUNT_URL = "dcaccount:https://nine.testrun.org/new"

# Default to 0 (disabled)
DEFAULT_DISPLAY_NAME = "HA DeltaChat Bot"
DEFAULT_BIO = "Default bio for bot..."
MAX_EPHEMERAL_TIME = 8640000 # 100 Days 

# Used for Media Identifier creation for fetching Media against Account / Chat / Message
CONF_ID_CAT_SEP = "-"
CONF_ID_ACC_CM_SEP = ":"

from enum import StrEnum
class DELTACHAT_MEDIA_CATEGORY(StrEnum):
    ACCOUNT = "account"
    CHAT = "chat"
    MESSAGE = "message"