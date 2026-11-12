#!/usr/bin/env bash
#
#    import_galaxy.sh — Validate a built collection tarball with galaxy-importer
#
#    Usage:
#      tools/import_galaxy.sh <nokia-sros-X.Y.Z.tar.gz>
#
#    Same checks Ansible Galaxy runs on publish (ansible-doc, ansible-lint, contents).
#

set -euo pipefail

TARBALL="${1:?usage: import_galaxy.sh <collection tarball>}"
if [[ ! -f "$TARBALL" ]]; then
  echo "tarball not found: $TARBALL" >&2
  exit 1
fi

python3 -m galaxy_importer.main "$TARBALL"
