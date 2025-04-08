# main.py

import os
import json
from srl.srl_validator import validate_srl
from translator.translator import translate_srl_to_xml
from executor.verefoo_runner import run_verefoo_parallel
from aggregator.aggregator import aggregate_outputs
from config import (
    INPUT_SRL_FILE,
    VEREFOO_INPUT_DIR,
    VEREFOO_OUTPUT_DIR,
    FINAL_OUTPUT_FILE
)

def ensure_directories():
    os.makedirs(VEREFOO_INPUT_DIR, exist_ok=True)
    os.makedirs(VEREFOO_OUTPUT_DIR, exist_ok=True)

def load_srl():
    with open(INPUT_SRL_FILE, 'r') as f:
        return json.load(f)

def save_final_output(data):
    with open(FINAL_OUTPUT_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def main():
    print("✅ Starting Smart Building Security Pipeline")

    ensure_directories()

    print("📥 Loading and validating SRL JSON...")
    srl = load_srl()
    validate_srl(srl)

    print("🔁 Translating SRL to VEREFOO XML inputs...")
    xml_paths = translate_srl_to_xml(srl)

    print("⚙️  Running VEREFOO in parallel...")
    output_paths = run_verefoo_parallel(xml_paths)

    print("🧠 Aggregating outputs...")
    aggregated = aggregate_outputs(output_paths)

    print("💾 Saving final configuration...")
    save_final_output(aggregated)

    print("✅ Pipeline completed successfully!")

if __name__ == '__main__':
    main()
