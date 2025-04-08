# executor/verefoo_runner.py

import os
import subprocess
from multiprocessing import Pool
from config import VEREFOO_COMMAND, VEREFOO_OUTPUT_DIR, VEREFOO_TIMEOUT

def run_single_verefoo(input_path):
    """
    Runs VEREFOO on a single XML input file.
    Returns the path to the generated output file.
    """
    filename = os.path.basename(input_path)
    output_path = os.path.join(VEREFOO_OUTPUT_DIR, filename.replace(".xml", "_output.xml"))

    cmd = VEREFOO_COMMAND.format(input_file=input_path, output_file=output_path)

    try:
        subprocess.run(cmd, shell=True, timeout=VEREFOO_TIMEOUT, check=True)
        print(f"✅ VEREFOO executed: {filename}")
    except subprocess.TimeoutExpired:
        print(f"⏱️ Timeout while running VEREFOO for {filename}")
    except subprocess.CalledProcessError:
        print(f"❌ Error executing VEREFOO for {filename}")

    return output_path

def run_verefoo_parallel(input_paths, num_workers=4):
    """
    Runs VEREFOO in parallel on a list of input XML files.
    Returns a list of output file paths.
    """
    with Pool(processes=num_workers) as pool:
        return pool.map(run_single_verefoo, input_paths)
