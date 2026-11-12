# Installation

!!! tip "Prerequisites"
    **Python:** `3.12+` (3.13 recommended), **Ansible Core:** `2.20+` (2.22 recommended), **SR OS:** SSH enabled; NETCONF enabled for `nokia.sros.md` NETCONF connections

    Ansible controllers run on Linux and macOS. On Windows, use WSL.
    Versions exercised in CI, see [Validated in CI](../support.md#validated-in-ci).

## External dependencies

The collection needs these Python packages on the Ansible controller:

| Package | Version | Purpose |
| --- | --- | --- |
| [ansible-pylibssh](https://pypi.org/project/ansible-pylibssh/) | `>=1.3.0` | SSH transport for `ansible.netcommon.network_cli` |
| [ncclient](https://pypi.org/project/ncclient/) | `>=0.6.19` | NETCONF transport for `ansible.netcommon.netconf` |
| [xmltodict](https://pypi.org/project/xmltodict/) | `>=0.13.0` | NETCONF replies as data (`display: native`) |

The collections [`ansible.netcommon`](https://galaxy.ansible.com/ui/repo/published/ansible/netcommon) (`>=5.2.0`) and [`ansible.utils`](https://galaxy.ansible.com/ui/repo/published/ansible/utils) (`>=3.0.0`) are installed automatically as dependencies of `nokia.sros`.

!!! warning "Not installed by ansible-galaxy"
    `ansible-galaxy collection install` installs Ansible content only. Python packages must be installed with `pip` into the same Python environment that runs Ansible.

    `ansible-pylibssh` ships wheels for common Linux platforms. Elsewhere pip builds it from source, which needs the libssh headers (`libssh-dev` on Debian/Ubuntu, `brew install libssh` on macOS).

## Option 1: Ansible environment (recommended)

This recipe builds a self-contained Ansible environment in a Python virtual environment, so the Python dependencies of the collection do not conflict with system packages.

### Step 1: Create and activate a virtual environment

```bash
python3 -m venv ansible-env
source ansible-env/bin/activate
```

### Step 2: Install Ansible and the Python dependencies

```bash
pip install --upgrade pip
pip install 'ansible-core>=2.20' 'ansible-pylibssh>=1.3.0' 'ncclient>=0.6.19' 'xmltodict>=0.13.0'
```

### Step 3: Install the collection

/// tab | Ansible Galaxy
```bash
ansible-galaxy collection install nokia.sros --upgrade
```
///
/// tab | GitHub Release
Each [GitHub release](https://github.com/nokia-steward/sros-ansible-integration/releases) has the collection tarball attached, the same artifact that is published on Galaxy:

```bash
VERSION=2.2.0
curl -LO https://github.com/nokia-steward/sros-ansible-integration/releases/download/${VERSION}/nokia-sros-${VERSION}.tar.gz
ansible-galaxy collection install nokia-sros-${VERSION}.tar.gz --force
```
///

The collection ships its `requirements.txt`. To install exactly the Python dependencies it declares, run this after the collection install:

```bash
pip install -r ~/.ansible/collections/ansible_collections/nokia/sros/requirements.txt
```

## Option 2: Execution environment

For [AWX, Ansible Automation Platform](https://docs.ansible.com/automation-controller/latest/html/userguide/execution_environments.html) or [ansible-navigator](https://ansible.readthedocs.io/projects/navigator/), build an execution environment with [ansible-builder](https://ansible.readthedocs.io/projects/builder/). The collection declares its Python dependencies in `meta/execution-environment.yml`, so `ansible-builder` installs them into the image:

```yaml
# execution-environment.yml
version: 3
dependencies:
  galaxy:
    collections:
      - name: nokia.sros
```

```bash
ansible-builder build --tag sros-ee
```

## Option 3: Development environment

To contribute or to test unreleased changes, install the collection from source:

```bash
git clone https://github.com/nokia-steward/sros-ansible-integration.git
cd sros-ansible-integration
python3 -m venv .venv
source .venv/bin/activate
make install-dev    # requirements-dev.txt and the collection dependencies
make install        # build and install the collection
```

See the [Developer Guide](../guides/developer-guide.md) for tests and documentation builds.

## Verify the installation

```bash
# List installed collections
ansible-galaxy collection list nokia.sros

# Confirm that the Python dependencies import
python -c 'import pylibsshext, ncclient, xmltodict; print("ok")'

# Show the plugin and module documentation
ansible-doc -t cliconf nokia.sros.md
ansible-doc nokia.sros.device_info
```

!!! success "Installation complete"
    Continue with the [Quick Start](quick-start.md) to set up the inventory and run a first playbook.
