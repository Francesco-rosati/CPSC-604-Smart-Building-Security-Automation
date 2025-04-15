import pytest
import os
from lxml import etree
from translator.translator import translate_srl_to_xml
from utils.xml_utils import build_graph_element


@pytest.fixture(scope="function")
def temp_input_dir(tmp_path, monkeypatch):
    verefoo_input = tmp_path / "verefoo_inputs"
    verefoo_input.mkdir()
    monkeypatch.setattr("config.VEREFOO_INPUT_DIR", verefoo_input)
    yield verefoo_input


@pytest.fixture
def minimal_srl():
    return {
        "areas": [
            {
                "name": "DemoZone",
                "devices": [
                    {"id": "dev1", "ip": "10.0.0.1", "type": "WEBSERVER", "neighbors": ["10.0.0.2"]},
                    {"id": "dev2", "ip": "10.0.0.2", "type": "WEBCLIENT", "neighbors": ["10.0.0.1"],
                     "target": "10.0.0.1"}
                ],
                "requested_policies": [
                    {"rule": "allow", "source": "10.0.0.2", "target": "10.0.0.1", "dst_port": "80", "protocol": "TCP"}
                ]
            }
        ]
    }


def test_translate_srl_to_xml_generates_file(minimal_srl, temp_input_dir):
    xml_paths = translate_srl_to_xml(minimal_srl)
    assert len(xml_paths) == 1
    path = xml_paths[0]
    assert os.path.exists(path)
    tree = etree.parse(path)
    root = tree.getroot()
    assert root.tag == "NFV"
    assert root.find("graphs") is not None
    assert root.find("Constraints") is not None
    assert root.find("PropertyDefinition") is not None


def test_graph_structure_from_build_graph_element():
    devices = [
        {"id": "cam1", "ip": "192.168.0.10", "type": "CAMERA", "neighbors": ["192.168.0.11"]},
        {"id": "bulb1", "ip": "192.168.0.11", "type": "SMARTBULB", "neighbors": ["192.168.0.10"]}
    ]
    area = {"name": "TestArea", "devices": devices}

    def mock_mapper(dev_type):
        return dev_type

    graph_elem = etree.Element("graph", id="0")
    build_graph_element(graph_elem, area, device_type_map=mock_mapper)

    nodes = graph_elem.findall("node")
    assert len(nodes) == 2
    names = [n.get("name") for n in nodes]
    assert "192.168.0.10" in names
    assert "192.168.0.11" in names

    configs = [n.find("configuration") for n in nodes]
    for config in configs:
        assert config is not None

    camera_config = graph_elem.xpath("//node[@name='192.168.0.10']/configuration/camera")
    smartbulb_config = graph_elem.xpath("//node[@name='192.168.0.11']/configuration/smartbulb")
    assert len(camera_config) == 1
    assert len(smartbulb_config) == 1


def test_translate_with_multiple_policies():
    from config import VEREFOO_INPUT_DIR

    srl = {
        "areas": [
            {
                "name": "MultiPolicyZone",
                "devices": [
                    {"id": "d1", "ip": "1.1.1.1", "type": "WEBSERVER", "neighbors": []},
                    {"id": "d2", "ip": "1.1.1.2", "type": "WEBCLIENT", "neighbors": [], "target": "1.1.1.1"}
                ],
                "requested_policies": [
                    {"rule": "deny", "source": "1.1.1.2", "target": "1.1.1.1"},
                    {"rule": "allow", "source": "1.1.1.1", "target": "1.1.1.2"}
                ]
            }
        ]
    }

    translate_srl_to_xml(srl)
    output_file = os.path.join(VEREFOO_INPUT_DIR, "multipolicyzone.xml")

    assert os.path.exists(output_file)
    tree = etree.parse(output_file)
    props = tree.findall(".//Property")
    assert len(props) == 2
    assert any(p.get("name") == "IsolationProperty" for p in props)
    assert any(p.get("name") == "ReachabilityProperty" for p in props)

    os.remove(output_file)  # clean up


def test_loadbalancer_pool_inference():
    devices = [
        {"id": "lb1", "ip": "10.0.0.1", "type": "LOADBALANCER", "neighbors": ["10.0.0.2"]},
        {"id": "ws1", "ip": "10.0.0.2", "type": "WEBSERVER", "neighbors": ["10.0.0.1"]}
    ]
    area = {"name": "LBPoolTest", "devices": devices}

    def map_type(dev_type): return dev_type

    graph_elem = etree.Element("graph", id="0")
    build_graph_element(graph_elem, area, device_type_map=map_type)
    lb_pool = graph_elem.xpath("//node[@name='10.0.0.1']/configuration/loadbalancer/pool")
    assert len(lb_pool) == 1
    assert lb_pool[0].text == "10.0.0.2"


def test_empty_neighbors():
    devices = [
        {"id": "dev", "ip": "192.168.1.1", "type": "CAMERA", "neighbors": []}
    ]
    area = {"name": "NoNeighbors", "devices": devices}

    graph_elem = etree.Element("graph", id="0")
    build_graph_element(graph_elem, area, device_type_map=lambda t: t)
    node = graph_elem.find("node")
    assert node is not None
    assert len(node.findall("neighbour")) == 0
