# main.py

import os
import json
from colorama import Fore, Style
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
    print(f"\n{Fore.YELLOW}Starting Smart Building Configuration Pipeline...{Style.RESET_ALL}\n")

    # Ensure the necessary directories exist
    ensure_directories()

    # Load and validate the SRL JSON
    print(f"{Fore.MAGENTA}Loading and validating SRL JSON...{Style.RESET_ALL}")
    srl = load_srl()
    validate_srl(srl)

    # Translate smart building SRL to VEREFOO XML inputs
    print(f"{Fore.MAGENTA}Translating SRL to VEREFOO XML inputs...{Style.RESET_ALL}")
    xml_paths = translate_srl_to_xml(srl)
    print(f"{Fore.GREEN}VEREFOO XML inputs successfully created!{Style.RESET_ALL}\n")

    # Run VEREFOO in parallel
    print(f"{Fore.MAGENTA}Running VEREFOO in parallel...{Style.RESET_ALL}")
    output_paths = run_verefoo_parallel(xml_paths)

    # Check for any failed executions
    if None in output_paths:
        print(f"\n{Fore.RED}One or more VEREFOO executions failed. Please check the logs.{Style.RESET_ALL}")
        return

    # Aggregate the outputs from VEREFOO
    print(f"{Fore.MAGENTA}Aggregating outputs from VEREFOO...{Style.RESET_ALL}")
    aggregated = aggregate_outputs(output_paths)

    # Save the final configuration
    print(f"{Fore.MAGENTA}Saving final configuration...{Style.RESET_ALL}")
    save_final_output(aggregated)

    print(f"{Fore.MAGENTA}Pipeline successfully completed!{Style.RESET_ALL}")


if __name__ == '__main__':
    main()
