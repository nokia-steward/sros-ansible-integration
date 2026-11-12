# SR OS Ansible Collection – Developer & Contributor Guide

Thank you for your interest in improving the **`nokia.sros`** Ansible collection!
This guide explains how to set up your development environment, run tests, and contribute changes — following the [Ansible Community Guidelines](https://docs.ansible.com/ansible/devel/community/code_of_conduct.html).

---

## Overview

The `nokia.sros` collection provides network automation support for Nokia **SR OS** devices through **CLI** and **NETCONF** interfaces.
The `Makefile` covers the development environment, sanity tests and documentation. The `tests/run.sh` helper script manages the containerlab topology and runs the integration playbooks.

---

## Prerequisites

Before contributing, ensure your environment includes:

* **Python 3.12 or newer** (3.13 recommended)
* **Ansible Core 2.20 or newer** (2.22 recommended)
* **libssh** development headers to build `ansible-pylibssh` where no wheel is available (`libssh-dev` on Debian/Ubuntu, `brew install libssh` on macOS)
* **Docker** and [containerlab](https://containerlab.dev) for running SR OS container images
* **Access** to SR OS container images and a valid license file
* A Linux, macOS, or BSD-like system with common GNU tools (`bash`, `curl`, `make`, etc.)

See [Validated in CI](https://nokia-steward.github.io/sros-ansible-integration/support/#validated-in-ci).

---

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/nokia-steward/sros-ansible-integration.git
cd sros-ansible-integration
```

### 2. Set up a Python virtual environment and dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
make install-dev
```

`make install-dev` installs `requirements-dev.txt` (which includes `requirements.txt`) and the collections `ansible.netcommon`, `ansible.utils` and `community.general`.

### 3. Run the sanity tests

```bash
make sanity
```

`ansible-test` needs the collection under an `ansible_collections/nokia/sros` directory; `make sanity` copies the checkout into `.build/` and runs `ansible-test sanity` there.

### 4. Build and install the collection locally

```bash
make install
```

### 5. Prepare images and licenses

Pull the `nokia_srsim` container image(s) and place a valid SR OS license file at `tests/license.txt`
(or point `SRSIM_LICENSE_FILE` at it).
Install [containerlab](https://containerlab.dev):

```bash
bash -c "$(curl -sL https://get.containerlab.dev)"
```

### 6. Deploy the lab and run the integration tests

```bash
cd tests
./run.sh deploy
./run.sh run --quiet
./run.sh destroy
```

`make test-integration-sros` (or `tests/run.sh integration`) runs deploy, all playbooks and destroy
in one step. Results are written to `tests/output/junit/` and the playbook logs to `tests/output/logs/`.

✅ **Tip:**
This workflow is consistent across Linux, macOS, and BSD systems. Only the package-installation commands may vary.

---

## Coding Standards

Follow Ansible and Python best practices:

* Use the standard [Ansible module structure](https://docs.ansible.com/ansible/latest/dev_guide/developing_modules_general.html)
* Include `DOCUMENTATION`, `EXAMPLES`, and `RETURN` blocks in every module, and `DOCUMENTATION` in every plugin
* Keep `galaxy.yml` metadata accurate and up to date
* Update `CHANGELOG.md`, `README.md` and `docs/` for user-visible changes; run `make docs` after changing docstrings
* Validate your work with:

  * `make ci` (Python syntax, playbook syntax, flake8, pylint, yamllint, ansible-lint, bandit, pip-audit)
  * `make sanity` (`ansible-test sanity`, including pep8, pylint and validate-modules)
  * `make test-integration-sros` (containerlab integration tests)

---

## Commit & Pull Request Guidelines

* Write **clear, focused commits** that explain both *what* and *why*
* Reference related issues (e.g. `Fixes #42`)
* Ensure all tests pass before requesting review
* Add or update tests for new features or bug fixes
* Maintain consistent docstrings, examples, and return schemas

A pull request can be merged only when:

* All CI checks pass successfully
* A maintainer approves the change
* The update fits the project's goals and quality standards

---

## Contributing

We welcome all contributions — from small fixes to major enhancements. Whether you're reporting a bug, improving documentation, or extending functionality, we'd love your input.

Before submitting a pull request:

* Run `make sanity` and the integration tests (`make test-integration-sros`)
* Follow [PEP 8](https://peps.python.org/pep-0008/) and Ansible plugin guidelines
* Ensure changes are documented and clearly commented
* Update or add integration tests where relevant

---

## Getting Help

If you encounter problems or need support:

**Search existing threads**
Check [open issues](https://github.com/nokia-steward/sros-ansible-integration/issues) to see if your topic is already covered.

**Open a new issue**

Include the following information:

* Your **OS**, **Python**, and **Ansible** versions
* The **SR OS** version used
* A concise problem description or error log

The maintainers and community collaborators monitor these channels and respond as time permits.
