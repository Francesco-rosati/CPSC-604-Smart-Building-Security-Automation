# srl/srl_validator.py

from colorama import Fore, Style

def validate_srl(srl_data):
    """
    Performs basic validation of the SRL JSON structure.
    Raises ValueError if the structure is invalid.
    """
    if not isinstance(srl_data, dict):
        raise ValueError("SRL must be a JSON object")

    if "areas" not in srl_data or not isinstance(srl_data["areas"], list):
        raise ValueError("SRL must contain a list of 'areas'")

    for area in srl_data["areas"]:
        if "name" not in area or "devices" not in area:
            raise ValueError(f"Each area must have a 'name' and a 'devices' field: {area}")
        if not isinstance(area["devices"], list):
            raise ValueError(f"'devices' must be a list in area {area['name']}")

        for device in area["devices"]:
            if "id" not in device or "type" not in device or "ip" not in device:
                raise ValueError(f"Each device must have 'id', 'type', and 'ip': {device}")

        if "requested_policies" in area:
            for policy in area["requested_policies"]:
                if "rule" not in policy or "source" not in policy or "target" not in policy:
                    raise ValueError(f"Policy must have 'rule', 'source', and 'target': {policy}")

    # Global network validation (if present)
    if "global_network" in srl_data:
        connections = srl_data["global_network"].get("connections", [])
        if not isinstance(connections, list):
            raise ValueError("'connections' in global_network must be a list")
        for conn in connections:
            if "from" not in conn or "to" not in conn or "rule" not in conn:
                raise ValueError(f"Each connection must have 'from', 'to', and 'rule': {conn}")

    print(f"{Fore.GREEN}SRL validation passed!{Style.RESET_ALL}\n")