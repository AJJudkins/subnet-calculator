# Security policy

## Scope and safety
pure calculation: no network access, no files read or written.

## What was and was not tested
**Tested (automated, in CI and locally):** CIDR math, VLSM allocation and input validation (unit tests).

**Not tested:** cross-checking against vendor or router tooling, IPv6 planning (VLSM is IPv4 only), and very large address plans.

## Reporting a problem
This is a small personal portfolio project, not a supported product. If you find a security issue, please open a GitHub issue **without** secrets, credentials or real system details, or use GitHub's "Report a vulnerability" button on the Security tab if it is enabled.
