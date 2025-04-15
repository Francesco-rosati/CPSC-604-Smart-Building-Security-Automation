import pytest
from srl.srl_validator import validate_srl


def test_validate_valid_srl():
    valid_srl = {
        "areas": [
            {
                "name": "Office_1",
                "devices": [
                    {"id": "d1", "type": "CAMERA", "ip": "192.168.1.1"},
                    {"id": "d2", "type": "SMARTBULB", "ip": "192.168.1.2"}
                ],
                "requested_policies": [
                    {"rule": "allow", "source": "192.168.1.1", "target": "192.168.1.2"}
                ]
            }
        ],
        "global_network": {
            "connections": [
                {"from": "Office_1", "to": "Office_2", "rule": "deny"}
            ]
        }
    }
    validate_srl(valid_srl)


def test_missing_areas():
    invalid = {
        "global_network": {"connections": []}
    }
    with pytest.raises(ValueError, match="SRL must contain a list of 'areas'"):
        validate_srl(invalid)


def test_area_missing_fields():
    invalid = {
        "areas": [{"devices": []}],
        "global_network": {}
    }
    with pytest.raises(ValueError, match="Each area must have a 'name' and a 'devices' field"):
        validate_srl(invalid)


def test_devices_not_list():
    invalid = {
        "areas": [{"name": "Lab", "devices": "not-a-list"}],
        "global_network": {}
    }
    with pytest.raises(ValueError, match="'devices' must be a list"):
        validate_srl(invalid)


def test_device_missing_fields():
    invalid = {
        "areas": [
            {
                "name": "Lab",
                "devices": [{"type": "CAMERA", "ip": "10.0.0.1"}]
            }
        ]
    }
    with pytest.raises(ValueError, match="Each device must have 'id', 'type', and 'ip'"):
        validate_srl(invalid)


def test_policy_missing_fields():
    invalid = {
        "areas": [
            {
                "name": "Office",
                "devices": [
                    {"id": "d1", "type": "CAMERA", "ip": "10.0.0.1"}
                ],
                "requested_policies": [
                    {"rule": "deny", "source": "10.0.0.1"}  # missing 'target'
                ]
            }
        ]
    }
    with pytest.raises(ValueError, match="Policy must have 'rule', 'source', and 'target'"):
        validate_srl(invalid)


def test_global_network_connections_not_list():
    invalid = {
        "areas": [
            {
                "name": "Office",
                "devices": [
                    {"id": "d1", "type": "CAMERA", "ip": "10.0.0.1"}
                ]
            }
        ],
        "global_network": {"connections": "not-a-list"}
    }
    with pytest.raises(ValueError, match="'connections' in global_network must be a list"):
        validate_srl(invalid)


def test_connection_missing_fields():
    invalid = {
        "areas": [
            {
                "name": "Office",
                "devices": [
                    {"id": "d1", "type": "CAMERA", "ip": "10.0.0.1"}
                ]
            }
        ],
        "global_network": {"connections": [{"from": "A", "to": "B"}]}  # missing 'rule'
    }
    with pytest.raises(ValueError, match="Each connection must have 'from', 'to', and 'rule'"):
        validate_srl(invalid)


def test_device_extra_fields():
    srl_data = {
        "areas": [
            {
                "name": "Lab",
                "devices": [
                    {"id": "d1", "type": "SENSOR", "ip": "10.0.0.1", "extra": "ok"}
                ]
            }
        ]
    }
    validate_srl(srl_data)  # extra fields should be ignored


def test_policy_no_protocol_or_ports():
    srl_data = {
        "areas": [
            {
                "name": "Office",
                "devices": [
                    {"id": "dev1", "type": "PC", "ip": "10.0.0.1"},
                    {"id": "dev2", "type": "PC", "ip": "10.0.0.2"}
                ],
                "requested_policies": [
                    {"rule": "allow", "source": "10.0.0.1", "target": "10.0.0.2"}  # no port, no protocol
                ]
            }
        ]
    }
    validate_srl(srl_data)


def test_empty_requested_policies():
    srl_data = {
        "areas": [
            {
                "name": "ZoneA",
                "devices": [
                    {"id": "devA", "type": "CAMERA", "ip": "192.168.0.10"}
                ],
                "requested_policies": []
            }
        ]
    }
    validate_srl(srl_data)


def test_connection_rule_case_sensitive():
    invalid = {
        "areas": [
            {
                "name": "A",
                "devices": [
                    {"id": "d1", "type": "CAMERA", "ip": "10.1.1.1"}
                ]
            }
        ],
        "global_network": {
            "connections": [
                {"from": "A", "to": "B", "rule": "ALLOW"}  # valid structurally even if semantically incorrect
            ]
        }
    }
    validate_srl(invalid)  # passes structurally, semantics left to other layers
