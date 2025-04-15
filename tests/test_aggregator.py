from pathlib2 import Path
from aggregator.aggregator import parse_verefoo_output, aggregate_outputs


def _write_xml(tmp_path: Path, name: str, xml: str) -> Path:
    """Write *xml* to *tmp_path/name* and return the Path object."""
    p = tmp_path / name
    p.write_text(xml, encoding="utf‑8")
    return p


def test_parse_basic_reachability(tmp_path):
    """WebClient → WebServer reachability should be parsed as rule=allow."""
    xml = """<?xml version='1.0'?>
<NFV><graphs><graph id='0'>
  <node name='10.0.0.1' functionalType='WEBSERVER'>
    <configuration name='srv'><webserver><name>10.0.0.1</name></webserver></configuration>
  </node>
  <node name='192.168.1.10' functionalType='WEBCLIENT'>
    <configuration name='cli'><webclient nameWebServer='10.0.0.1'/></configuration>
  </node>
</graph></graphs>
<PropertyDefinition>
  <Property name='ReachabilityProperty' src='192.168.1.10' dst='10.0.0.1' lv4proto='TCP'/>
</PropertyDefinition></NFV>"""
    p = _write_xml(tmp_path, "area_output.xml", xml)
    devices, policies = parse_verefoo_output(p)

    assert {d["ip"] for d in devices} == {"10.0.0.1", "192.168.1.10"}
    cli = next(d for d in devices if d["ip"] == "192.168.1.10")
    assert cli["target"] == "10.0.0.1"
    assert policies == [{"rule": "allow", "source": "192.168.1.10", "target": "10.0.0.1", "protocol": "TCP"}]


def test_parse_nat_and_lb(tmp_path):
    """NAT sources and LoadBalancer pools must be extracted as lists."""
    xml = """<NFV><graphs><graph id='0'>
  <node name='20.0.0.1' functionalType='NAT'>
    <configuration name='nat'>
      <nat><source>172.16.0.5</source><source>172.16.0.6</source></nat>
    </configuration>
  </node>
  <node name='30.0.0.1' functionalType='LOADBALANCER'>
    <configuration name='lb'>
      <loadbalancer><pool>10.0.0.1</pool><pool>10.0.0.2</pool></loadbalancer>
    </configuration>
  </node>
</graph></graphs><PropertyDefinition/></NFV>"""
    p = _write_xml(tmp_path, "nat_lb.xml", xml)
    devices, _ = parse_verefoo_output(p)

    nat = next(d for d in devices if d["type"] == "NAT")
    assert nat["sources"] == ["172.16.0.5", "172.16.0.6"]

    lb = next(d for d in devices if d["type"] == "LOADBALANCER")
    assert set(lb["pools"]) == {"10.0.0.1", "10.0.0.2"}


def test_parse_skips_empty_config(tmp_path):
    """Nodes without meaningful configuration should be ignored."""
    xml = """<NFV><graphs><graph id='0'>
  <node name='1.2.3.4' functionalType='WEBSERVER'>
    <configuration name='empty'><webserver/></configuration>
  </node>
</graph></graphs><PropertyDefinition/></NFV>"""
    p = _write_xml(tmp_path, "empty.xml", xml)
    devices, policies = parse_verefoo_output(p)
    assert devices == [] and policies == []


def test_parse_isolation_policy(tmp_path):
    """IsolationProperty must be parsed as rule=deny with proto+port."""
    xml = """<NFV><graphs><graph id='0'>
  <node name='5.5.5.5' functionalType='WEBCLIENT'>
    <configuration name='c'><webclient nameWebServer='6.6.6.6'/></configuration>
  </node>
</graph></graphs>
<PropertyDefinition>
  <Property name='IsolationProperty' src='5.5.5.5' dst='6.6.6.6' lv4Proto='UDP' dstPort='53'/>
</PropertyDefinition></NFV>"""
    p = _write_xml(tmp_path, "iso.xml", xml)
    _, policies = parse_verefoo_output(p)
    assert policies == [{"rule": "deny", "source": "5.5.5.5", "target": "6.6.6.6", "protocol": "UDP", "dst_port": "53"}]


def test_aggregate_outputs_devices_and_policies(tmp_path):
    """Aggregate two outputs, ensure devices, policies and global network kept."""
    xml1 = """<NFV><graphs><graph id='0'>
  <node name='1.1.1.1' functionalType='WEBSERVER'>
    <configuration name='srvA'><webserver><name>1.1.1.1</name></webserver></configuration>
  </node>
</graph></graphs>
<PropertyDefinition>
  <Property name='IsolationProperty' src='1.1.1.1' dst='2.2.2.2'/>
</PropertyDefinition></NFV>"""
    a1 = _write_xml(tmp_path, "areaA_output.xml", xml1)

    xml2 = """<NFV><graphs><graph id='0'>
  <node name='2.2.2.2' functionalType='WEBCLIENT'>
    <configuration name='cliB'><webclient nameWebServer='1.1.1.1'/></configuration>
  </node>
</graph></graphs><PropertyDefinition/></NFV>"""
    a2 = _write_xml(tmp_path, "areaB_output.xml", xml2)

    input_srl = {"global_network": {"connections": [{"from": "A", "to": "B", "rule": "deny"}]}}

    agg = aggregate_outputs([str(a1), str(a2)], input_srl)

    # Global network preserved
    assert agg["global_network"] == input_srl["global_network"]

    # Area names
    assert {a["name"] for a in agg["areas"]} == {"areaA", "areaB"}

    areaA = next(a for a in agg["areas"] if a["name"] == "areaA")
    assert any(d["ip"] == "1.1.1.1" for d in areaA["devices"]) and areaA["verified_policies"][0]["rule"] == "deny"

    areaB = next(a for a in agg["areas"] if a["name"] == "areaB")
    assert any(d["ip"] == "2.2.2.2" for d in areaB["devices"])  # client present


def test_aggregate_outputs_duplicate_area(tmp_path):
    """If two XML outputs share the same base filename the aggregator keeps **both** entries
    (current behaviour: no deduplication)."""
    xml = """<NFV><graphs><graph id='0'>
  <node name='9.9.9.9' functionalType='WEBSERVER'>
    <configuration name='srv'><webserver><name>9.9.9.9</name></webserver></configuration>
  </node>
</graph></graphs><PropertyDefinition/></NFV>"""
    p1 = _write_xml(tmp_path, "duplicate_output.xml", xml)
    p2 = _write_xml(tmp_path, "duplicate_output.xml", xml)  # same filename on purpose

    agg = aggregate_outputs([str(p1), str(p2)], {})

    # No deduplication => two identical area entries are expected
    assert len(agg["areas"]) == 2
