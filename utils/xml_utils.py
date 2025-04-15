# utils/xml_utils.py

from lxml import etree


def build_graph_element(graph_elem, area, device_type_map):
    """
    Adds nodes and neighbors to the XML graph based on the area definition.
    Supports functional and non-functional devices, and multiple load balancer pools.
    Autocompletes load balancer pools using neighbor WEBSERVERs if not specified.
    """
    devices = area["devices"]
    ip_to_neighbors = {d["ip"]: d.get("neighbors", []) for d in devices}
    ip_to_device = {d["ip"]: d for d in devices}

    for device in devices:
        ip = device["ip"]
        dev_type = device.get("type", "").upper()
        verefoo_type = device_type_map(dev_type)

        # Add node element
        node_elem = etree.SubElement(graph_elem, "node", name=ip)
        if verefoo_type:
            node_elem.set("functional_type", verefoo_type)

        # Add neighbors
        for neighbor_ip in ip_to_neighbors.get(ip, []):
            etree.SubElement(node_elem, "neighbour", name=neighbor_ip)

        # Add a configuration block
        description = device.get("id", "autogen")
        config_elem = etree.SubElement(node_elem, "configuration", description=description, name=description)

        # Configuration tags per device type
        if verefoo_type == "WEBCLIENT":
            wc = etree.SubElement(config_elem, "webclient")
            wc.set("nameWebServer", device.get("target", "0.0.0.0"))

        elif verefoo_type == "WEBSERVER":
            ws = etree.SubElement(config_elem, "webserver")
            etree.SubElement(ws, "name").text = ip

        elif verefoo_type == "FIREWALL" or verefoo_type in ["STATEFUL_FIREWALL", "PRIORITY_FIREWALL",
                                                            "WEB_APPLICATION_FIREWALL"]:
            fw = etree.SubElement(config_elem, "firewall", defaultAction="DENY")
            etree.SubElement(fw, "elements")

        elif verefoo_type == "NAT":
            nat = etree.SubElement(config_elem, "nat")
            sources = device.get("sources", [ip])
            for src in sources:
                etree.SubElement(nat, "source").text = src

        elif verefoo_type == "LOADBALANCER":
            lb = etree.SubElement(config_elem, "loadbalancer")
            pool_list = device.get("pools")
            if not pool_list:
                # Infer pool from neighbors that are WEBSERVERs
                pool_list = [nbr for nbr in ip_to_neighbors.get(ip, []) if
                             ip_to_device.get(nbr, {}).get("type", "").upper() == "WEBSERVER"]
                if not pool_list:
                    pool_list = [ip]  # fallback to self
            for pool_ip in pool_list:
                etree.SubElement(lb, "pool").text = pool_ip

        elif verefoo_type == "FORWARDER":
            fwd = etree.SubElement(config_elem, "forwarder")
            etree.SubElement(fwd, "name").text = "Forwarder"

        elif verefoo_type in [
            "ENDPOINT", "ENDHOST", "MAILCLIENT", "MAILSERVER",
            "ANTISPAM", "CACHE", "DPI", "DPI_S",
            "VPNACCESS", "VPNEXIT", "FIELDMODIFIER", "TRAFFIC_MONITOR"
        ]:
            comp_elem = etree.SubElement(config_elem, verefoo_type.lower())
            comp_elem.set("name", ip)

        elif not dev_type:
            # No functional type: leave config block empty
            continue

        else:
            # Fallback configuration element for unknown/other types
            fallback = etree.SubElement(config_elem, verefoo_type.lower())
            fallback.set("name", ip)
