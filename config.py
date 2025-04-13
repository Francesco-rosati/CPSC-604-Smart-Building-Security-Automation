# config.py

import os

# Base data directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_SRL_FILE = os.path.join(DATA_DIR, "input_srl.json")
VEREFOO_INPUT_DIR = os.path.join(DATA_DIR, "verefoo_inputs")
VEREFOO_OUTPUT_DIR = os.path.join(DATA_DIR, "verefoo_outputs")
FINAL_OUTPUT_FILE = os.path.join(DATA_DIR, "final_config.json")

# VEREFOO command pattern
# You can customize this path to point to your actual VEREFOO JAR
VEREFOO_COMMAND = "java -jar verefoo.jar {input_file} > {output_file}"

# Timeout for VEREFOO execution (in seconds)
VEREFOO_TIMEOUT = 60

# Device type mapping to VEREFOO-compatible types
def map_device_type(device_type):
    """
    Returns the VEREFOO-compatible functional type for a given device type.
    Defaults to WEBCLIENT for all unspecified types.
    """
    direct_map = {
        "GATEWAY": "FIREWALL",
        "ENDPOINT": "ENDPOINT",
        "ENDHOST": "ENDHOST",
        "WEBCLIENT": "WEBCLIENT",
        "ANTISPAM": "ANTISPAM",
        "CACHE": "CACHE",
        "DPI": "DPI",
        "DPI_S": "DPI_S",
        "MAILCLIENT": "MAILCLIENT",
        "MAILSERVER": "MAILSERVER",
        "VPNACCESS": "VPNACCESS",
        "VPNEXIT": "VPNEXIT",
        "FIELDMODIFIER": "FIELDMODIFIER",
        "STATEFUL_FIREWALL": "STATEFUL_FIREWALL",
        "PRIORITY_FIREWALL": "PRIORITY_FIREWALL",
        "WEB_APPLICATION_FIREWALL": "WEB_APPLICATION_FIREWALL",
        "TRAFFIC_MONITOR": "TRAFFIC_MONITOR",
        "NAT": "NAT",
        "FORWARDER": "FORWARDER",
        "LOADBALANCER": "LOADBALANCER",
        "WEBSERVER": "WEBSERVER"
    }
    return direct_map.get(device_type.upper(), "ENDHOST")

# Supported protocols
SUPPORTED_PROTOCOLS = ["TCP", "UDP", "ANY"]
