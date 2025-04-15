# executor/verefoo_runner.py

import os
import subprocess
from colorama import Fore, Style
from multiprocessing import Pool
from lxml import etree
from config import VEREFOO_COMMAND, VEREFOO_OUTPUT_DIR, VEREFOO_TIMEOUT


def run_single_verefoo(input_path):
    """
    Runs VEREFOO on a single XML input file.
    Returns the path to the generated output file.
    """
    filename = os.path.basename(input_path)
    output_path = os.path.join(VEREFOO_OUTPUT_DIR, filename.replace(".xml", "_output.xml"))

    cmd = [arg.replace("{input_path}", input_path).replace("{output_path}", output_path)
           for arg in VEREFOO_COMMAND]

    try:

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=VEREFOO_TIMEOUT, check=True)
        status_code = result.stdout.strip()

        if status_code == "200":
            # Try to parse and pretty-print the XML
            with open(output_path, "rb") as f:
                root = etree.fromstring(f.read())
            formatted = etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")
            with open(output_path, "wb") as f:
                f.write(formatted)

            print(f"{Fore.YELLOW}VEREFOO executed: {Style.RESET_ALL}{filename}")
            return output_path
        else:
            print(f"{Fore.RED}VEREFOO failed ({status_code}) for {Style.RESET_ALL}{filename}")

            try:
                with open(output_path, "rb") as f:
                    root = etree.fromstring(f.read())
                    message = root.findtext("message")
                    if message:
                        print(f"{Fore.LIGHTRED_EX}Error message: {Style.RESET_ALL}{message}")
            except Exception as e:
                print(f"{Fore.LIGHTBLACK_EX}Could not parse error XML: {e}{Style.RESET_ALL}")

            return None
    except subprocess.TimeoutExpired:
        print(f"{Fore.RED}Timeout while running VEREFOO for {Style.RESET_ALL}{filename}\n")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}Error executing VEREFOO for {Style.RESET_ALL}{filename}\n")

    return output_path


def run_verefoo_parallel(input_paths, num_workers=4):
    """
    Runs VEREFOO in parallel on a list of input XML files.
    Returns a list of output file paths.
    """
    with Pool(processes=num_workers) as pool:
        return pool.map(run_single_verefoo, input_paths)
