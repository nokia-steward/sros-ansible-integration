# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.2.0]
### Changed
- Pinned to officially supported Ansible/Python releases, which still receive security (CVE) fixes: `ansible-core` 2.20+ (was 2.17+) and Python 3.12+, recommended 2.22 with Python 3.13. Older releases are best-effort only, see [Support](https://nokia-steward.github.io/sros-ansible-integration/support/#supported-ansible-and-python-versions).
- Galaxy metadata and links point to the `nokia-steward` repository; collection description mentions workflow playbooks
- Tests follow the new consistent test pattern: `.github/test-matrix.yml` defines the suites (`sanity`, `integration-sros`), run with `make test-setup` and `make test-<suite>`, with JUnit results. `tests/run.sh integration` replaces `run.sh sanity --all`; `--all` is now the default (`--exitfirst` stops early). ansible-core devel runs as an experimental case.

### Added
- Local and CI code quality: `make lint`, `make security`, `make ci`; `.flake8`, `.pylintrc`, `.ansible-lint`; GitHub workflow `security.yml` (Bandit, pip-audit, Trivy, lint)
- MkDocs documentation site (Start Here, Inventory Patterns, Security Guide, Community Guide, expanded Examples)
- Shipped workflow playbook `device_inventory` under `playbooks/` with example inventory
- `ansible-test sanity` in CI, release smoke tests, `meta/execution-environment.yml` and `Makefile`
- `tests/inventory.example.yml`, `tests/README.md`, playbook syntax check in CI (`make validate-ansible`)
- Release workflow validates the collection artifact with `galaxy-importer` (`tools/import_galaxy.sh`, `make import-galaxy`)
- Ansible Galaxy version badge and quick-start example in the README

### Fixed
- Import `to_text` from `ansible.module_utils.common.text.converters` instead of deprecated `ansible.module_utils._text` (ansible-core 2.24), as in [PR #14](https://github.com/nokia-steward/sros-ansible-integration/pull/14)
- CI integration tests now use the SR OS version of the test matrix (always ran 25.7.R2)
- Plugin documentation, imports and `device_info` check mode, as required by `ansible-test sanity`

## [2.1.1]
### Changed
- Repository moved to the `nokia-steward` organization, no code changes

## [2.1.0]
### Added
- Support for `flat` and `xml` output formats in `get_config()`
- Support for `intended` as a valid configuration source in `get_config()`
- Support for `active` as a valid configuration source in `get_config()`
  Same as `running` but excludes index persistency.
- Support for commit comments in `edit_config()` using the `comment` parameter
- Support `replace` with local file in `edit_config()`

### Changed
- Inherid base-class RPCs, while adding the SROS specific ones
- Use `info /` and `compare /` to ensure all tree levels are included in output
- Construct `info` commands using `' '.join()` to prevent trailing/double spaces when optional parameters are not provided
- Added exception handling for rollback

### Fixed
- Ensure `load full-replace` and `rollback` commands are correctly executed in CLI context `configure`
- Ensure `quit-config` is correctly executed in CLI root context
- Release workflow to automatically set collection version meta and upload to galaxy

## [2.0.0]
### Added
- Containerlab topology as test-automation reference
- GitHub workflow to build collection for every new release

### Changed
- Single repo for `nokia.sros` collection for simplified release management

### Fixed
- Updated playbooks for compatibility with latest Ansible releases

[2.2.0]: https://github.com/nokia-steward/sros-ansible-integration/compare/2.1.1...2.2.0
[2.1.1]: https://github.com/nokia-steward/sros-ansible-integration/releases/tag/2.1.1
[2.1.0]: https://github.com/nokia-steward/sros-ansible-integration/releases/tag/2.1.0
[2.0.0]: https://github.com/nokia-steward/sros-ansible-integration/releases/tag/2.0.0
