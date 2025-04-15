# aggregator/aggregator.py

from __future__ import print_function, division
import os
import sys
from collections import deque
import xmltodict
from colorama import Fore, Style

if sys.version_info[0] < 3:  # Python 2
    STR_TYPES = (basestring,)  # noqa: F821 – it exists only in Py2
else:
    STR_TYPES = (str, bytes)

# Map functional types (upper‑case) → configuration tag that contains the
# real settings for that device.
FTYPE_TAG_MAP = {
    "WEBSERVER": "webserver",
    "WEBCLIENT": "webclient",
    "LOADBALANCER": "loadbalancer",
    "FORWARDER": "forwarder",
    "NAT": "nat",
    "FIREWALL": "firewall",
    "STATEFUL_FIREWALL": "statefulFirewall",
    "PRIORITY_FIREWALL": "priorityFirewall",
    "WEB_APPLICATION_FIREWALL": "webApplicationFirewall",
    "ENDHOST": "endhost",
    "ENDPOINT": "endpoint",
    "CACHE": "cache",
    "DPI": "dpi",
    "ANTISPAM": "antispam",
    "MAILCLIENT": "mailclient",
    "MAILSERVER": "mailserver",
    "VPNACCESS": "vpnaccess",
    "VPNEXIT": "vpnexit",
    "TRAFFIC_MONITOR": "trafficMonitor",
}


def _attr(dct, key):
    return dct.get('@' + key) or dct.get(key)


def _collect_nodes(xml_dict):
    """Return *all* <node> elements contained in the parsed XML dict."""
    nodes = []
    queue = deque([xml_dict])

    while queue:
        current = queue.popleft()
        if isinstance(current, dict):
            for k, v in current.items():
                if k == 'node':
                    if isinstance(v, list):
                        nodes.extend(v)
                    else:
                        nodes.append(v)
                if isinstance(v, (dict, list)):
                    queue.append(v)
        elif isinstance(current, list):
            queue.extend(current)
    return nodes


def _has_meaningful_config(ftype, config):
    """True if the functional block for *ftype* contains any real data."""
    tag = FTYPE_TAG_MAP.get(ftype.upper())
    if not tag:
        return False

    block = config.get(tag)
    if block is None:
        return False

    if isinstance(block, STR_TYPES):
        return bool(block.strip())
    if isinstance(block, list):
        return len(block) > 0
    if isinstance(block, dict):
        for val in block.values():
            if val not in (None, ''):
                return True
    return False


def parse_verefoo_output(xml_path):
    """Parse one VEREFOO XML output file – return (devices, policies)."""
    with open(xml_path, 'r') as fh:
        raw = xmltodict.parse(fh.read())

    # ---- devices -------------------------------------------------------
    devices = []
    for node in _collect_nodes(raw):
        name = _attr(node, 'name')
        ftype = (_attr(node, 'functionalType') or '').upper()
        config = node.get('configuration', {})

        if not config or not _has_meaningful_config(ftype, config):
            continue  # skip empty

        dev = {
            'id': _attr(config, 'name') or 'dev_' + name.replace('.', '_'),
            'ip': name,
            'type': ftype or 'ENDHOST',
        }

        # Special‑case extra fields
        if ftype == 'WEBCLIENT' and 'webclient' in config:
            target = _attr(config['webclient'], 'nameWebServer')
            if target:
                dev['target'] = target
        elif ftype == 'NAT' and 'nat' in config:
            srcs = config['nat'].get('source')
            if isinstance(srcs, list):
                dev['sources'] = [s.get('#text', s) if isinstance(s, dict) else s for s in srcs]
            elif srcs:
                dev['sources'] = [srcs.get('#text', srcs) if isinstance(srcs, dict) else srcs]
        elif ftype == 'LOADBALANCER' and 'loadbalancer' in config:
            pools = config['loadbalancer'].get('pool')
            if isinstance(pools, list):
                dev['pools'] = [p.get('#text', p) if isinstance(p, dict) else p for p in pools]
            elif pools:
                dev['pools'] = [pools.get('#text', pools) if isinstance(pools, dict) else pools]

        devices.append(dev)

    # ---- policies ------------------------------------------------------
    def _collect_props(tree):
        if isinstance(tree, list):
            for item in tree:
                for p in _collect_props(item):
                    yield p
        elif isinstance(tree, dict):
            if 'property' in tree:
                for p in _collect_props(tree['property']):
                    yield p
            elif _attr(tree, 'src') or _attr(tree, 'dst'):
                yield tree
            else:
                for v in tree.values():
                    for p in _collect_props(v):
                        yield p

    policies = []
    for p in _collect_props(raw):
        rule = 'deny' if 'ISOLATION' in (_attr(p, 'name') or '').upper() else 'allow'
        pol = {
            'rule': rule,
            'source': _attr(p, 'src'),
            'target': _attr(p, 'dst'),
        }
        proto = _attr(p, 'lv4Proto') or _attr(p, 'lv4proto')
        if proto:
            pol['protocol'] = proto
        dport = _attr(p, 'dstPort') or _attr(p, 'dst_port')
        if dport:
            pol['dst_port'] = dport
        policies.append(pol)

    return devices, policies


def aggregate_outputs(output_paths, input_srl):
    """Merge multiple VEREFOO outputs into the final SRL‑style JSON."""
    result = {
        'global_network': input_srl.get('global_network', {}),
        'areas': [],
    }

    for path in output_paths:
        area_name = os.path.splitext(os.path.basename(path))[0].replace('_output', '')
        print(Fore.YELLOW + 'Aggregating area: ' + Style.RESET_ALL + area_name)
        devices, policies = parse_verefoo_output(path)
        result['areas'].append({
            'name': area_name,
            'devices': devices,
            'verified_policies': policies,
        })

    return result
