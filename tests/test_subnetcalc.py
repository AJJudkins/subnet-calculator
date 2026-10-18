import ipaddress, os, sys
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import subnetcalc as s


def test_info():
    i = s.info("192.168.1.0/24")
    assert i["netmask"] == "255.255.255.0" and i["broadcast"] == "192.168.1.255"
    assert i["usable_hosts"] == 254 and i["first_host"] == "192.168.1.1"


def test_prefix_for_hosts():
    assert s.prefix_for_hosts(2) == 30
    assert s.prefix_for_hosts(50) == 26
    assert s.prefix_for_hosts(254) == 24
    assert s.prefix_for_hosts(255) == 23


def test_plan_no_overlap_and_fits():
    reqs = {"LAN": 100, "Servers": 50, "Mgmt": 10, "Link": 2}
    plan = s.plan_vlsm("10.0.0.0/24", reqs)
    nets = [ipaddress.ip_network(p["subnet"]) for p in plan]
    for p in plan:
        assert p["usable_hosts"] >= p["requested_hosts"]
    for i, a in enumerate(nets):
        assert a.subnet_of(ipaddress.ip_network("10.0.0.0/24"))
        for b in nets[i + 1:]:
            assert not a.overlaps(b)


def test_plan_known_result():
    plan = s.plan_vlsm("192.168.0.0/24", {"A": 100, "B": 50})
    assert [p["subnet"] for p in plan] == ["192.168.0.0/25", "192.168.0.128/26"]


def test_plan_out_of_space():
    with pytest.raises(ValueError):
        s.plan_vlsm("192.168.0.0/26", {"A": 40, "B": 40})


def test_parse_reqs_bad():
    with pytest.raises(ValueError):
        s.parse_reqs(["oops"])
