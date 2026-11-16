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

`../test-matrix.yml` lists suites, cases and versions (see the file header). Each case runs
`make test-setup` and `make test-<suite>` with `ANSIBLE_VERSION`, `SROS_VERSION` and `REGISTRY`
where applicable. To add a version, add a row under `cases`. `make test` runs lab-free suites
locally.

The `integration` suite has one case per SR OS release. Each case deploys `tests/topo.clab.yml`,
one node in classic and one in model-driven configuration mode, and runs the one test list,
`tests/playbooks.yml`. Each category there names the platforms it applies to (`hosts`, platform
groups declared in `tests/platforms.yml`); a category with no host in the lab is reported as
skipped. Each case names the image path it pulls, without the tag, as `registry`. The suite needs
containerlab 0.83.0 or newer.

## Where the SR OS cases run

`integration` needs the SR OS simulator license. GitHub runs it only when the repository has an
`SRSIM_LICENSE` secret. Otherwise the job summary lists those cases as "not run on GitHub, needs
srsim", and a maintainer runs them with nokia-steward-validator, which posts one table of
results, a column per SR OS release, to the pull request (after the `ready-for-validation` label;
the result shows as `validation-passed` or `validation-failed`) or to an issue for `master`.
