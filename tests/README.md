# Integration tests

The playbooks under `tests/playbooks/` are the integration test suite. Shipped workflows live in `../playbooks/` at the collection root. Categories are defined in `playbooks.yml`. The runner `run.sh` deploys a [containerlab](https://containerlab.dev) topology (`topo.clab.yml`), generates inventory under `clab-ansible/`, and runs the playbooks against Nokia SR-SIM.

## Prerequisites

- Docker and containerlab
- SR OS container image `registry.srlinux.dev/pub/nokia_srsim` (tag from `SROS_VERSION`, default from the topology)
- License file at `tests/license.txt`, or `SRSIM_LICENSE_FILE` pointing at one (required for deploy)

## Quick run

```bash
make test-integration-sros        # deploy, run all playbooks, destroy
```

Or step by step:

```bash
cd tests
./run.sh deploy
./run.sh run --quiet              # or --category netconf
./run.sh destroy
```

`SROS_VERSION=25.10.R1 ./run.sh deploy` selects the SR OS image tag. `./run.sh help` lists all options.
Results: `tests/output/junit/<suite>.xml` (one testcase per playbook) and `tests/output/logs/`.

## Local inventory (no containerlab)

For syntax checks or manual runs against your own routers:

```bash
cp tests/inventory.example.yml tests/inventory.yml
# edit tests/inventory.yml
make validate-ansible
```

The Makefile uses `tests/inventory.example.yml` when `tests/inventory.yml` is missing, so CI can validate playbook syntax without credentials.

## CI

`.github/workflows/ci.yml` runs the `sanity` and `integration-sros` suites on the versions in `.github/test-matrix.yml`. `run.sh` is the shared reference script of the nokia-steward test pattern; do not edit it here.

## Known upstream warnings

Integration playbooks that use `ansible.netcommon.cli_config` and report a change may show one `[WARNING]` line per character on the idempotency hint (for example on task `do some config`). That comes from [ansible.netcommon#828](https://github.com/ansible-collections/ansible.netcommon/pull/828) (`cli_config` puts the hint in `warnings` as a string instead of a list). It is not a `nokia.sros` plugin bug; upgrade `ansible.netcommon` once that fix is released.
