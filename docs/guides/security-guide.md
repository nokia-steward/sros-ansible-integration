# Security Guide

## Credentials

Store router passwords and keys outside plain-text inventory:

```bash
ansible-vault create group_vars/all/vault.yml
```

Reference vault variables in inventory:

```yaml
ansible_password: "{{ vault_sros_password }}"
```

Run playbooks with `--ask-vault-pass` or a vault password file according to your policy.

Prefer **SSH keys** where the platform allows them:

```yaml
ansible_user: admin
ansible_private_key_file: ~/.ssh/sros_admin
```

The CLI plugins use **ansible-pylibssh** for SSH. Install it in the same Python environment as Ansible (`requirements.txt`).

## Transport

- Use **SSH** to the management interface; restrict who can reach it on the network.
- For **NETCONF** (`ansible.netcommon.netconf` on `nokia.sros.md`), enable the NETCONF server only where needed and protect it like SSH.

Do not commit real credentials, license files or private keys to Git. The integration suite uses `tests/license.txt`, which is not part of the published collection artifact.

## Controller

- Run Ansible from a **virtual environment** or [execution environment](https://docs.ansible.com/automation-controller/latest/html/userguide/execution_environments.html) with pinned dependencies (`requirements.txt`).
- Report vulnerabilities through [GitHub Security Advisories](https://github.com/nokia-steward/sros-ansible-integration/security/advisories), not public issues.

## Related collections

For gRPC TLS, certificates and gNSI on SR OS or SR Linux, see the [OpenConfig Security Guide](https://nokia-steward.github.io/openconfig-ansible-integration/guides/security-guide/).
