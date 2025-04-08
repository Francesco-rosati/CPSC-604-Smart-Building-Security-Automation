# aggregator/aggregator.py

import os
import xmltodict

def parse_output_file(path):
    """
    Parses a VEREFOO XML output file and extracts relevant information.
    Returns a dictionary representing the area.
    """
    with open(path, 'r', encoding='utf-8') as f:
        data = xmltodict.parse(f.read())

    area_name = os.path.basename(path).replace('_output.xml', '')
    graph = data['NFV']['graphs']['graph']
    nodes = graph.get('node', [])
    if isinstance(nodes, dict):
        nodes = [nodes]

    area_dict = {
        "name": area_name,
        "devices": [],
        "verified_policies": []
    }

    for node in nodes:
        area_dict["devices"].append({
            "id": node["@name"],
            "type": node.get("@functional_type", "UNKNOWN"),
            "configuration": node.get("configuration", {})
        })

    properties = data['NFV'].get('PropertyDefinition', {}).get('Property', [])
    if isinstance(properties, dict):
        properties = [properties]

    for prop in properties:
        entry = {
            "rule": "deny" if prop["@name"] == "IsolationProperty" else "allow",
            "source": prop["@src"],
            "target": prop["@dst"]
        }
        if "@dst_port" in prop:
            entry["dst_port"] = prop["@dst_port"]
        if "@lv4proto" in prop:
            entry["protocol"] = prop["@lv4proto"]
        area_dict["verified_policies"].append(entry)

    return area_dict

def aggregate_outputs(output_paths):
    """
    Aggregates all VEREFOO output files into a single final JSON configuration.
    """
    final_config = {
        "global_configuration": {
            "areas": []
        }
    }

    for path in output_paths:
        area_config = parse_output_file(path)
        final_config["global_configuration"]["areas"].append(area_config)

    print("✅ Aggregation complete")
    return final_config
