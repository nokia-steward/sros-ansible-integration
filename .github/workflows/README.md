# Testing Infrastructure

This directory contains the test automation for the SR OS Ansible Collection.

## Workflows

- `ci.yml` - sanity and containerlab integration tests for pull requests and pushes
- `docs.yml` - builds the MkDocs site and publishes it to GitHub Pages
- `release.yml` - builds, smoke-tests and publishes the collection for a GitHub release
- `../test-matrix.yml` - Test matrix configuration (single source of truth)

## Test Matrix Configuration

The `test-matrix.yml` file defines which versions are tested. The controller versions follow the support policy shared with `nokia.openconfig` and `nokia.nsp`: the `ansible-core` releases that still receive security fixes.

- Controller pairs: ansible-core 2.20 with Python 3.12, 2.21 with Python 3.14, 2.22 with Python 3.13
- Recommended controller: ansible-core 2.22 with Python 3.13
- SR OS versions: 25.7.R2, 25.10.R1

To add or remove test versions, edit the lists in `../test-matrix.yml`. Both GitHub Actions and external CI systems read from this single source of truth.

## GitHub Actions Workflow

The `ci.yml` workflow:
1. Reads the test matrix from `test-matrix.yml`
2. Runs `ansible-test sanity` for every controller pair
3. Runs the containerlab integration tests for every controller pair against the newest SR OS version, and for the recommended controller against every SR OS version
4. Uses containerlab to deploy the SR OS test topology, with the image tag taken from `SROS_VERSION`
5. Reports results in PR checks
