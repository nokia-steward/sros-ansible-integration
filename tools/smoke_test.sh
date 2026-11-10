#!/usr/bin/env bash
#
#    smoke_test.sh — Install a built collection tarball and check it loads
#
#    Usage:
#      tools/smoke_test.sh <nokia-sros-X.Y.Z.tar.gz>
#
#    Fails if ansible-doc cannot load the cliconf and netconf plugins and the
#    modules of the installed collection.
#

set -euo pipefail

TARBALL="${1:?usage: smoke_test.sh <collection tarball>}"
DEST="$(mktemp -d)"
trap 'rm -rf "$DEST"' EXIT

ansible-galaxy collection install --force -p "$DEST" "$TARBALL"

export ANSIBLE_COLLECTIONS_PATH="$DEST"
for mode in md classic light; do
  ansible-doc -t cliconf "nokia.sros.$mode" > /dev/null
done
ansible-doc -t netconf nokia.sros.md > /dev/null
modules=()
for f in "$DEST/ansible_collections/nokia/sros/plugins/modules/"*.py; do
  base="$(basename "$f" .py)"
  [[ "$base" == __* ]] && continue
  modules+=("nokia.sros.$base")
done
ansible-doc -t module "${modules[@]}" > /dev/null
echo "ansible-doc loads the cliconf and netconf plugins and all ${#modules[@]} modules"
