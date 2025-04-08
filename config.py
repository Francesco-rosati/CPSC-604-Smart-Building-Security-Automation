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
DEVICE_TYPE_MAPPING = {
    "CAMERA": "WEBCLIENT",
    "SENSOR": "WEBCLIENT",
    "SMARTBULB": "WEBCLIENT",
    "PC": "WEBCLIENT",
    "PRINTER": "WEBCLIENT",
    "GATEWAY": "FIREWALL"
}

# Supported protocols
SUPPORTED_PROTOCOLS = ["TCP", "UDP", "ANY"]
