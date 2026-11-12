# Support

The Nokia SR OS Ansible Collection is an open-source project led by Nokia. It is published under the [nokia-steward](https://github.com/nokia-steward) organization on GitHub and is actively maintained.

The collection is a community project. There is no commercial support and no service level agreement (SLA). Help comes from the documentation, the maintainers and the community, and contributions from third parties are welcome. See [CONTRIBUTING](https://github.com/nokia-steward/sros-ansible-integration/blob/master/CONTRIBUTING.md) to get involved.

## Getting help

- [Documentation](index.md) — installation, guides and the [reference](reference/index.md)
- [Nokia Network Developer Portal](https://network.developer.nokia.com/sr/learn/sr-os-ansible) — tutorials
- [GitHub Issues](https://github.com/nokia-steward/sros-ansible-integration/issues) — bugs and questions
- [Ansible Galaxy](https://galaxy.ansible.com/ui/repo/published/nokia/sros/) — released versions

## Validated in CI

The Nokia Ansible collections `nokia.openconfig`, `nokia.nsp` and `nokia.sros` share one support policy for the Ansible controller. The minimum is the oldest `ansible-core` release that still receives security fixes, so that a supported installation also receives fixes for known vulnerabilities (CVEs).

| | ansible-core | Python on the controller |
| --- | --- | --- |
| Minimum | 2.20 | 3.12 |
| Recommended | 2.22 | 3.13 |

[`.github/test-matrix.yml`](https://github.com/nokia-steward/sros-ansible-integration/blob/master/.github/test-matrix.yml) lists every CI case: ansible-core and Python **pairs** under `sanity`, and SR-SIM integration on **x.10** SR OS releases plus the **latest** release under `integration-sros` (see the file header).

`ansible-core` 2.20 and newer run on Python 3.12 to 3.14, see the [ansible-core support matrix](https://docs.ansible.com/projects/ansible/latest/reference_appendices/release_and_maintenance.html#ansible-core-support-matrix). The modules of this collection run on the controller, so the routers need no Python.

Older releases, `ansible-core` 2.19 and earlier, no longer receive security fixes. The collection may still work with them, but they are not tested, Ansible prints a warning that the collection does not support the running version, and issues reported against them are handled on a best-effort basis. Upgrade to a supported release instead.

The minimum follows the `ansible-core` release cycle: it is raised when an `ansible-core` release reaches end of life, in May and November.

Other SR OS releases may work but are not validated in CI.

## Before production

Production networks bring challenges that a lab does not show. Test your playbooks on lab routers or in a [containerlab](https://containerlab.dev) topology first:

- Idempotency: do repeated runs produce the same result?
- Check mode: does the `--check --diff` preview match the intended change? In classic mode, check mode briefly applies the change, see the [User Guide](guides/user-guide.md#classic-mode).
- Error handling: are CLI errors, timeouts and rejected commits handled?
- Scale: do configuration sizes, command timeouts and the number of concurrent hosts work at production scale?

## Reporting issues

- Bugs: open a [GitHub Issue](https://github.com/nokia-steward/sros-ansible-integration/issues) with the Ansible, collection and Python versions, the router platform and SR OS release, the network OS and connection settings without passwords, and the failing task output.
- Features: open an issue that describes the use case.
- Security: do not open a public issue. Use [GitHub Security Advisories](https://github.com/nokia-steward/sros-ansible-integration/security/advisories) instead.

---

Questions? Start with the [User Guide](guides/user-guide.md) or open an [issue](https://github.com/nokia-steward/sros-ansible-integration/issues).
