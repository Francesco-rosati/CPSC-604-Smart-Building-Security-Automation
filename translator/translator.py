# translator/translator.py

import os
from lxml import etree
from colorama import Fore, Style
from config import VEREFOO_INPUT_DIR, map_device_type
from utils.xml_utils import build_graph_element


def translate_srl_to_xml(srl_data):
    """
    Translates each area in the SRL JSON into a separate VEREFOO-compatible XML input.
    Returns a list of file paths to the generated XML files.
    """
    xml_paths = []

    for area in srl_data["areas"]:
        area_name = area["name"].replace(" ", "_").lower()
        filename = f"{area_name}.xml"
        filepath = os.path.join(VEREFOO_INPUT_DIR, filename)

        # Create XML root
        nfv_elem = etree.Element("NFV")
        graphs_elem = etree.SubElement(nfv_elem, "graphs")
        graph_elem = etree.SubElement(graphs_elem, "graph", id="0")

        # Add nodes, links, and configurations to graph
        build_graph_element(graph_elem, area, device_type_map=map_device_type)

        # Add empty constraints and policy definitions
        constraints_element = etree.SubElement(nfv_elem, "Constraints")
        etree.SubElement(constraints_element, "NodeConstraints")
        etree.SubElement(constraints_element, "LinkConstraints")
        prop_def = etree.SubElement(nfv_elem, "PropertyDefinition")

        for policy in area.get("requested_policies", []):
            prop = etree.SubElement(prop_def, "Property", graph="0")
            prop.set("name", "IsolationProperty" if policy["rule"] == "deny" else "ReachabilityProperty")
            prop.set("src", policy["source"])
            prop.set("dst", policy["target"])
            if "dst_port" in policy:
                prop.set("dst_port", str(policy["dst_port"]))
            if "protocol" in policy:
                prop.set("lv4proto", policy["protocol"].upper())

        # Write to file
        tree = etree.ElementTree(nfv_elem)
        tree.write(filepath, pretty_print=True, xml_declaration=True, encoding="UTF-8")
        xml_paths.append(filepath)

        print(f"{Fore.YELLOW}Translated area {Fore.BLUE}'{area_name}'{Style.RESET_ALL} → {filepath}")

    return xml_paths
