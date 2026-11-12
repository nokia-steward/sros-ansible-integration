# Testing Infrastructure

This directory contains the test automation for the SR OS Ansible Collection.

## Workflows

- `ci.yml` - the test suites of `../test-matrix.yml` for pull requests, pushes and weekly
- `docs.yml` - builds the MkDocs site and publishes it to GitHub Pages
- `release.yml` - builds, smoke-tests and publishes the collection for a GitHub release
- `security.yml` - Trivy, bandit and pip-audit

`ci.yml`, `../scripts/matrix.py`, `../scripts/summary.py` and `../../tests/run.sh` are copied
unchanged from the nokia-steward test pattern (version 1, maintained in nokia-steward-validator).
Change the test matrix, not these files.

## Test matrix

`../test-matrix.yml` is the single source of truth for what is tested:

- `sanity`: `ansible-test sanity` for every supported controller (ansible-core 2.20 with
  Python 3.12, 2.21 with 3.14, 2.22 with 3.13), plus ansible-core devel as an experimental case
- `integration-sros`: the containerlab playbooks of `tests/playbooks.yml` against SR OS (SR-SIM),
  every controller against 25.10.R1 and the recommended controller (2.22, Python 3.13) against
  25.7.R2

Each case runs `make test-setup` and `make test-<suite>`. The versions arrive as
`ANSIBLE_VERSION` and `SROS_VERSION`. To add a version, add a row under `cases`. `make test`
runs the suites that need no lab (`sanity`) on a workstation.

## Where the SR OS cases run

`integration-sros` needs the SR OS simulator license. GitHub runs it only when the repository
has an `SRSIM_LICENSE` secret. Otherwise the job summary lists those cases as "not run on
GitHub, needs srsim", and a maintainer runs them with nokia-steward-validator, which posts the
results to the pull request (after the `nokia-validate` label) or to an issue for `master`.
