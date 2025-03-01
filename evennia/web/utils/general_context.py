"""
This file defines global variables that will always be available in a view
context without having to repeatedly include it.

For this to work, this file is included in the settings file, in the
TEMPLATES["OPTIONS"]["context_processors"] list.

"""


import os

from django.conf import settings

from evennia.utils.utils import get_evennia_version

# Setup lists of the most relevant apps so
# the adminsite becomes more readable.

GAME_NAME = None
GAME_SLOGAN = None
SERVER_VERSION = None
SERVER_HOSTNAME = None

TELNET_ENABLED = None
TELNET_PORTS = None
TELNET_SSL_ENABLED = None
TELNET_SSL_PORTS = None

SSH_ENABLED = None
SSH_PORTS = None

WEBCLIENT_ENABLED = None
WEBSOCKET_CLIENT_ENABLED = None
WEBSOCKET_PORT = None
WEBSOCKET_URL = None

REST_API_ENABLED = False

ACCOUNT_RELATED = ["Accounts"]
GAME_ENTITIES = ["Objects", "Scripts", "Comms", "Help"]
GAME_SETUP = ["Permissions", "Config"]
CONNECTIONS = ["Irc"]
WEBSITE = ["Flatpages", "News", "Sites"]


def load_game_settings():
    """
    Load and cache game settings.

    """
    global GAME_NAME, GAME_SLOGAN, SERVER_VERSION, SERVER_HOSTNAME
    global TELNET_ENABLED, TELNET_PORTS
    global TELNET_SSL_ENABLED, TELNET_SSL_PORTS
    global SSH_ENABLED, SSH_PORTS
    global WEBCLIENT_ENABLED, WEBSOCKET_CLIENT_ENABLED, WEBSOCKET_PORT, WEBSOCKET_URL
    global REST_API_ENABLED

    try:
        GAME_NAME = settings.SERVERNAME.strip()
    except AttributeError:
        GAME_NAME = "Evennia"
    SERVER_VERSION = get_evennia_version()
    try:
        GAME_SLOGAN = settings.GAME_SLOGAN.strip()
    except AttributeError:
        GAME_SLOGAN = SERVER_VERSION
    SERVER_HOSTNAME = settings.SERVER_HOSTNAME

    TELNET_ENABLED = settings.TELNET_ENABLED
    TELNET_PORTS = settings.TELNET_PORTS
    TELNET_SSL_ENABLED = settings.SSL_ENABLED
    TELNET_SSL_PORTS = settings.SSL_PORTS

    SSH_ENABLED = settings.SSH_ENABLED
    SSH_PORTS = settings.SSH_PORTS

    WEBCLIENT_ENABLED = settings.WEBCLIENT_ENABLED
    WEBSOCKET_CLIENT_ENABLED = settings.WEBSOCKET_CLIENT_ENABLED
    # if we are working through a proxy or uses docker port-remapping, the webclient port encoded
    # in the webclient should be different than the one the server expects. Use the environment
    # variable WEBSOCKET_CLIENT_PROXY_PORT if this is the case.
    WEBSOCKET_PORT = int(
        os.environ.get("WEBSOCKET_CLIENT_PROXY_PORT", settings.WEBSOCKET_CLIENT_PORT)
    )
    # this is determined dynamically by the client and is less of an issue
    WEBSOCKET_URL = settings.WEBSOCKET_CLIENT_URL

    REST_API_ENABLED = settings.REST_API_ENABLED


load_game_settings()


# The main context processor function
def general_context(request):
    """
    Returns common Evennia-related context stuff, which is automatically added
    to context of all views.

    """
    account = None
    if request.user.is_authenticated:
        account = request.user

    puppet = None
    if account and request.session.get("puppet"):
        pk = int(request.session.get("puppet"))
        puppet = next((x for x in account.characters if x.pk == pk), None)

    return {
        "account": account,
        "puppet": puppet,
        "game_name": GAME_NAME,
        "game_slogan": GAME_SLOGAN,
        "server_hostname": SERVER_HOSTNAME,
        "evennia_userapps": ACCOUNT_RELATED,
        "evennia_entityapps": GAME_ENTITIES,
        "evennia_setupapps": GAME_SETUP,
        "evennia_connectapps": CONNECTIONS,
        "evennia_websiteapps": WEBSITE,
        "telnet_enabled": TELNET_ENABLED,
        "telnet_ports": TELNET_PORTS,
        "telnet_ssl_enabled": TELNET_SSL_ENABLED,
        "telnet_ssl_ports": TELNET_SSL_PORTS,
        "ssh_enabled": SSH_ENABLED,
        "ssh_ports": SSH_ENABLED,
        "webclient_enabled": WEBCLIENT_ENABLED,
        "websocket_enabled": WEBSOCKET_CLIENT_ENABLED,
        "websocket_port": WEBSOCKET_PORT,
        "websocket_url": WEBSOCKET_URL,
        "rest_api_enabled": REST_API_ENABLED,
    }
