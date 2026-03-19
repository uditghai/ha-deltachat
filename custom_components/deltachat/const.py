DOMAIN = "deltachat"

# Config Flow Attributes
CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_DISPLAY_NAME = "display_name"
CONF_AVATAR_PATH = "avatar_path"
CONF_BIO = "bio"
CONF_SERVER = "server"

CONF_AUTO_DELETE = "auto_delete_seconds"
CONF_DEFAULT_CHAT = "default_chat_id"
# Attributes in DC RPC
DC_EMAIL = "addr"
DC_PASSWORD = "mail_pw"
DC_DISPLAY_NAME = "displayname"
DC_BIO = "selfstatus"
# Chatmail servers allow "instant" account creation via a specific URL format
DEFAULT_NEW_ACCOUNT_URL = "dcaccount:https://nine.testrun.org/new"

FLOW_TYPE = "flow_type"
FLOW_TYPE_CREATE = "create"
FLOW_TYPE_EXISTING = "existing"

# Default to 0 (disabled)
DEFAULT_AUTO_DELETE = 0