# Developer Guide

This guide covers the development environment, tests and documentation of `nokia.sros`. See [CONTRIBUTING](https://github.com/nokia-steward/sros-ansible-integration/blob/master/CONTRIBUTING.md) for the contribution workflow.

## Development environment

```bash
git clone https://github.com/nokia-steward/sros-ansible-integration.git
cd sros-ansible-integration
python3 -m venv .venv
source .venv/bin/activate
make install-dev
```

`make install-dev` installs `requirements-dev.txt` (which includes `requirements.txt`) and the collections `ansible.netcommon`, `ansible.utils` and `community.general`. Use a controller from the [supported versions](../support.md#supported-ansible-and-python-versions).

## Repository layout

| Path | Content |
| --- | --- |
| `plugins/terminal/`, `plugins/cliconf/`, `plugins/netconf/` | Network OS plugins `md`, `classic` and `light` |
| `plugins/modules/` | Modules |
| `tests/sanity/` | `ansible-test sanity` ignore files per ansible-core release |
| `playbooks/` | Workflow playbooks shipped with the collection |
| `tests/topo.clab.yml`, `tests/run.sh`, `tests/playbooks/` | Containerlab topology and integration playbooks |
| `docs/`, `mkdocs.yml`, `tools/generate_docs.py` | This documentation |
| `.github/test-matrix.yml` | Versions tested in CI |

## Sanity tests

```bash
make sanity
```

`ansible-test` needs the collection below an `ansible_collections/nokia/sros` directory, with its dependencies `ansible.netcommon` and `ansible.utils` in the same collection root. `make sanity` copies the checkout to `.build/ansible_collections/nokia/sros`, installs the dependencies next to it, and runs `ansible-test sanity --venv` with the active Python.

Add an entry to `tests/sanity/ignore-<ansible-core>.txt` only for findings that cannot be fixed, with a comment that explains why. Keep the ignore files of all tested ansible-core releases in sync.

## Integration tests

The integration tests run the playbooks of `tests/playbooks.yml` against SR OS (SR-SIM) containers deployed with [containerlab](https://containerlab.dev). They need Docker, the `nokia_srsim` image and a license file at `tests/license.txt`.

```bash
cd tests
./run.sh deploy                             # deploy the topology
./run.sh run --category all --quiet --all   # run all playbooks, continue on error
./run.sh destroy                            # remove the topology
```

`SROS_VERSION=25.10.R1 ./run.sh deploy` selects the SR OS image tag. `./run.sh help` lists all options.

## Continuous integration

`.github/workflows/ci.yml` reads `.github/test-matrix.yml` and runs:

1. `ansible-test sanity` for each supported ansible-core and Python pair.
2. The containerlab integration tests for each pair against the newest SR OS release, and for the recommended controller against every SR OS release.

`.github/workflows/release.yml` builds the collection for a GitHub release, validates it with `galaxy-importer`, smoke-tests the artifact with every controller pair (`tools/smoke_test.sh`) and publishes it to Ansible Galaxy.

## Code quality and security

```bash
make ci          # validate, lint (flake8, pylint, yamllint, ansible-lint), security (bandit, pip-audit)
make validate-ansible   # playbook syntax only
```

`security.yml` on GitHub also runs Trivy filesystem scans and the same checks on a schedule. Uses `tests/inventory.example.yml` when `tests/inventory.yml` is absent.

## Documentation

```bash
make docs         # generate docs/reference and build the site into site/
make docs-serve   # serve on http://127.0.0.1:8000
```

`tools/generate_docs.py` renders the reference pages from the `DOCUMENTATION`, `EXAMPLES` and `RETURN` blocks of the plugins and modules and updates the Reference navigation in `mkdocs.yml`. Run it after changing a docstring and commit the generated files. `.github/workflows/docs.yml` publishes the site to GitHub Pages on every push to `master`.

## Releases

Version numbers follow [Semantic Versioning](https://semver.org/). The release workflow sets the version in `galaxy.yml` from the release tag; keep `galaxy.yml`, `mkdocs.yml`, `CHANGELOG.md` and the version lines in `README.md` and `docs/` in sync before tagging.
