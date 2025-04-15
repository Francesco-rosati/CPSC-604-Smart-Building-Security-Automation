# aggregator/aggregator.py

import os
import xmltodict
import json
from config import VEREFOO_OUTPUT_DIR
from colorama import Fore, Style


def parse_verefoo_output(xml_path):
    """
    Parses a VEREFOO XML output file and extracts valid device configurations and verified policies.
    Only devices with meaningful configuration (non-empty functional block) are retained.
    """
    with open(xml_path, 'r') as file:
        data = xmltodict.parse(file.read())

    devices = []
    policies = []

    try:
        raw_nodes = data['Resources']['content']['content']['graphs']['graph']['graph']['node']
        if isinstance(raw_nodes, dict):
            raw_nodes = [raw_nodes]

        for node in raw_nodes:
            name = node.get('name')
            ftype = node.get('functionalType', '').upper()
            config = node.get('configuration', {})

            # Dynamically check if the configuration block for this device is empty
            config_block = config.get(ftype.lower()) if ftype and isinstance(config, dict) else None
            if not config_block or (isinstance(config_block, dict) and len(config_block.keys()) == 0):
                continue

            device_entry = {
                "id": config.get('name', f"dev_{name.replace('.', '_')}") if isinstance(config,
                                                                                        dict) else f"dev_{name.replace('.', '_')}",
                "ip": name,
                "type": ftype
            }

            if ftype == "WEBCLIENT" and "webclient" in config:
                target = config["webclient"].get("nameWebServer")
                if target:
                    device_entry["target"] = target

            if ftype == "NAT" and "nat" in config:
                srcs = config["nat"].get("source")
                if isinstance(srcs, dict):
                    srcs = srcs.get("source")
                if isinstance(srcs, list):
                    device_entry["sources"] = srcs
                elif isinstance(srcs, str):
                    device_entry["sources"] = [srcs]

            if ftype == "LOADBALANCER" and "loadbalancer" in config:
                pool = config["loadbalancer"].get("pool")
                if isinstance(pool, dict):
                    pool = pool.get("pool")
                if isinstance(pool, list):
                    device_entry["pools"] = pool
                elif isinstance(pool, str):
                    device_entry["pools"] = [pool]

            devices.append(device_entry)

        # Properties
        props = data['Resources']['content']['content']['propertyDefinition']['property']
        if isinstance(props, dict):
            props = [props]

        for p in props:
            rule = "deny" if "ISOLATION" in p.get('name', '').upper() else "allow"
            policy_entry = {
                "rule": rule,
                "source": p.get('src'),
                "target": p.get('dst')
            }
            if p.get('lv4Proto'):
                policy_entry["protocol"] = p.get('lv4Proto')
            if p.get('dstPort'):
                policy_entry["dst_port"] = p.get('dstPort')
            policies.append(policy_entry)

    except Exception as e:
        print(f"{Fore.RED}Failed to parse {xml_path}: {Style.RESET_ALL}{e}")

    return devices, policies


def aggregate_outputs(output_paths, input_srl):
    """
    Aggregates multiple VEREFOO output XMLs into an updated SRL-style JSON.
    Includes only devices with meaningful configuration and verified policies.
    """
    result = {
        "global_network": input_srl.get("global_network", {}),
        "areas": []
    }

    for path in output_paths:
        area_name = os.path.splitext(os.path.basename(path))[0].replace("_output", "")
        print(f"{Fore.YELLOW}Aggregating area: {Style.RESET_ALL}{area_name}")
        devices, policies = parse_verefoo_output(path)
        result["areas"].append({
            "name": area_name,
            "devices": devices,
            "verified_policies": policies
        })

    return result
