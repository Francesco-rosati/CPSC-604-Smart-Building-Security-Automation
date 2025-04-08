# utils/xml_utils.py

from lxml import etree

def build_graph_element(graph_elem, area, device_type_map):
    """
    Adds nodes and neighbors to the XML graph based on the area definition.
    """
    devices = area["devices"]
    ip_to_neighbors = {d["ip"]: d.get("neighbors", []) for d in devices}

    for device in devices:
        ip = device["ip"]
        dev_type = device["type"].upper()
        verefoo_type = device_type_map.get(dev_type, dev_type)

        # Add node element
        node_elem = etree.SubElement(graph_elem, "node", name=ip)
        if verefoo_type:
            node_elem.set("functional_type", verefoo_type)

        # Add neighbors
        for neighbor_ip in ip_to_neighbors.get(ip, []):
            etree.SubElement(node_elem, "neighbour", name=neighbor_ip)

        # Add a default configuration block
        config_elem = etree.SubElement(node_elem, "configuration", name=f"autogen_{ip}")

        if verefoo_type == "WEBCLIENT":
            wc = etree.SubElement(config_elem, "webclient")
            wc.set("nameWebServer", "130.10.0.1")  # Placeholder

        elif verefoo_type == "WEBSERVER":
            ws = etree.SubElement(config_elem, "webserver")
            etree.SubElement(ws, "name").text = ip

        elif verefoo_type == "FIREWALL":
            fw = etree.SubElement(config_elem, "firewall", defaultAction="DENY")
            etree.SubElement(fw, "elements")  # empty for now

        elif verefoo_type == "NAT":
            nat = etree.SubElement(config_elem, "nat")
            etree.SubElement(nat, "source").text = ip

        elif verefoo_type == "LOADBALANCER":
            lb = etree.SubElement(config_elem, "loadbalancer")
            etree.SubElement(lb, "pool").text = ip

        elif verefoo_type == "FORWARDER":
            fwd = etree.SubElement(config_elem, "forwarder")
            etree.SubElement(fwd, "name").text = "Forwarder"

        else:
            etree.SubElement(config_elem, verefoo_type.lower())
