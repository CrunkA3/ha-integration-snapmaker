"""Constants for the Snapmaker integration."""

DOMAIN = "snapmaker"
MANUFACTURER = "Snapmaker"

# Config entry data keys
CONF_TOKEN = "token"
CONF_IP = "ip"
CONF_MODEL = "model"
CONF_PRINTER_NAME = "printer_name"

# UDP discovery
UDP_PORT = 20054
UDP_BUFFER_SIZE = 1024
UDP_MSG = b'discover'
UDP_TIMEOUT = 5.0

# HTTP API
API_PORT = 8080
API_CONNECT_PATH = "/api/v1/connect"
API_STATUS_PATH = "/api/v1/status"
API_DISCONNECT_PATH = "/api/v1/disconnect"