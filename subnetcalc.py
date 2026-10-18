"""CIDR info and VLSM planner using the standard ipaddress module."""
import argparse
import ipaddress
import json
import math


def info(cidr):
    n = ipaddress.ip_network(cidr, strict=False)
    usable = max(n.num_addresses - 2, 0) if n.prefixlen < n.max_prefixlen - 1 else n.num_addresses
    hosts = list(n.hosts()) if n.num_addresses <= 2 ** 16 else []
    return {
        "network": str(n.network_address), "prefix": n.prefixlen, "netmask": str(n.netmask),
        "broadcast": str(n.broadcast_address) if n.version == 4 else None,
        "first_host": str(hosts[0]) if hosts else None,
        "last_host": str(hosts[-1]) if hosts else None,
        "total_addresses": n.num_addresses, "usable_hosts": usable,
    }


def prefix_for_hosts(hosts, version=4):
    """Smallest subnet (largest prefix) that fits `hosts` usable hosts (+network, +broadcast)."""
    if hosts < 1:
        raise ValueError("hosts must be >= 1")
    bits = max(math.ceil(math.log2(hosts + 2)), 2)  # /30 minimum for IPv4 host subnets
    return 32 - bits


def plan_vlsm(block, requirements):
    """Allocate subnets from `block` for {name: hosts}. Largest first to avoid fragmentation."""
    parent = ipaddress.ip_network(block, strict=False)
    if parent.version != 4:
        raise ValueError("VLSM planner supports IPv4 only")
    free = [parent]
    plan = []
    for name, hosts in sorted(requirements.items(), key=lambda kv: -kv[1]):
        prefix = prefix_for_hosts(hosts)
        if prefix < parent.prefixlen:
            raise ValueError(f"{name}: needs /{prefix}, larger than {parent}")
        free.sort(key=lambda n: (n.prefixlen, int(n.network_address)))
        # choose the smallest free block that fits
        candidates = [n for n in free if n.prefixlen <= prefix]
        if not candidates:
            raise ValueError(f"Not enough space in {parent} for {name} ({hosts} hosts)")
        chosen = max(candidates, key=lambda n: (n.prefixlen, -int(n.network_address)))
        free.remove(chosen)
        while chosen.prefixlen < prefix:
            left, right = chosen.subnets(prefixlen_diff=1)
            free.append(right)
            chosen = left
        plan.append({"name": name, "requested_hosts": hosts, "subnet": str(chosen),
                     "usable_hosts": chosen.num_addresses - 2,
                     "range": f"{chosen[1]} - {chosen[-2]}", "gateway": str(chosen[1])})
    return plan


def format_plan(plan):
    head = f"{'Name':<12}{'Need':>6}  {'Subnet':<18}{'Usable':>7}  Host range"
    rows = [f"{p['name']:<12}{p['requested_hosts']:>6}  {p['subnet']:<18}{p['usable_hosts']:>7}  {p['range']}" for p in plan]
    return "\n".join([head] + rows)


def parse_reqs(items):
    reqs = {}
    for it in items:
        name, _, n = it.partition("=")
        if not name.strip() or not n.isdigit() or not 1 <= int(n) <= 2 ** 24:
            raise ValueError(f"bad requirement '{it}', use NAME=HOSTS (HOSTS between 1 and 16777216)")
        if name in reqs:
            raise ValueError(f"duplicate requirement name '{name}'")
        reqs[name] = int(n)
    return reqs


def main(argv=None):
    ap = argparse.ArgumentParser(description="Subnet calculator and VLSM planner")
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("info", help="show details for a CIDR")
    i.add_argument("cidr")
    p = sub.add_parser("plan", help="split a block by host requirements")
    p.add_argument("block")
    p.add_argument("requirements", nargs="+", help="NAME=HOSTS, e.g. Servers=50")
    p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "info":
            for k, v in info(a.cidr).items():
                print(f"{k:<16}{v}")
        else:
            plan = plan_vlsm(a.block, parse_reqs(a.requirements))
            print(json.dumps(plan, indent=2) if a.json else format_plan(plan))
    except ValueError as e:
        ap.exit(1, f"error: {e}\n")


if __name__ == "__main__":
    main()
