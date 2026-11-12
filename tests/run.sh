#!/usr/bin/env bash
# version: 1
# Copied from nokia-steward-validator pattern/. Do not edit: the linter checks this file is unchanged.
#
#    run.sh - containerlab lab plus categorized Ansible playbooks, results as JUnit XML
#
#    Usage:
#      tests/run.sh <command> [options]
#
#    Commands:
#      integration  deploy, run, destroy; destroy also runs after a failure
#      deploy       deploy the lab from a clean state
#      run          run the playbook categories against the deployed lab
#      destroy      destroy the lab
#      help         show this help
#
#    Options:
#      -t, --topo <file>        containerlab topology (default: ./topo.clab.yml)
#      -p, --playbooks <file>   playbook categories (default: ./playbooks.yml)
#      -s, --suite <name>       suite name for the results (default: $STEWARD_SUITE, else integration)
#      -c, --category <name>    run one category only (default: all)
#      -x, --exitfirst          stop at the first failed playbook
#      -q, --quiet              playbook output goes to the log files only
#
#    Results, relative to tests/:
#      output/junit/<suite>.xml      one testcase per playbook: passed, failed with a
#                                    one-line message, or skipped with the reason
#      output/logs/<suite>/*.log     full ansible-playbook output, one file per playbook
#      output/logs/<suite>/nodes/    container logs of the lab nodes (integration only)
#
#    playbooks.yml lists categories; a category names the inventory group it needs
#    (hosts, default all). A category whose group has no hosts is reported as skipped.
#    Playbook entries may carry ansible-playbook options, e.g. "playbooks/x.yml --diff".
#
#    SRSIM_LICENSE_FILE, when set, is copied to ./license.txt for the topology and removed
#    again by destroy. Without it, a license.txt placed by hand is used and kept.
#    The exit code is 1 when the lab failed to deploy or any playbook failed.
#
#    Examples:
#      tests/run.sh integration --topo topo.clab.yml --suite integration-sros
#      tests/run.sh deploy && tests/run.sh run --category netconf && tests/run.sh destroy
#

set -euo pipefail

cd "$(dirname "$0")"

# --- Defaults ----------------------------------------------------------------

TOPOLOGY_FILE="./topo.clab.yml"
PLAYBOOK_FILE="./playbooks.yml"
SUITE="${STEWARD_SUITE:-integration}"
CATEGORY=""
EXIT_FIRST=false
QUIET=false

OUTPUT_DIR="./output"
RESULTS=()
FAILED=false

# --- Logging -----------------------------------------------------------------

log() {
  local level="$1"; shift
  case "$level" in
    INFO) echo "[INFO] $*" ;;
    OK) echo "[OK] $*" ;;
    SKIP) echo "[SKIPPED] $*" ;;
    FAIL) echo "[FAIL] $*" ;;
    *) echo "$*" ;;
  esac
}

# --- YAML helpers (PyYAML ships with ansible-core) ---------------------------

yaml_categories() {
  python3 -c 'import sys, yaml; [print(c) for c in (yaml.safe_load(open(sys.argv[1])) or {}).get("categories", {})]' \
    "$PLAYBOOK_FILE"
}

yaml_category_hosts() {
  python3 -c 'import sys, yaml; print(((yaml.safe_load(open(sys.argv[1])) or {}).get("categories", {}).get(sys.argv[2]) or {}).get("hosts", "all"))' \
    "$PLAYBOOK_FILE" "$1"
}

yaml_playbooks() {
  python3 -c 'import sys, yaml; [print(p) for p in ((yaml.safe_load(open(sys.argv[1])) or {}).get("categories", {}).get(sys.argv[2]) or {}).get("playbooks", [])]' \
    "$PLAYBOOK_FILE" "$1"
}

host_count() {
  local count
  count="$(ansible "$1" --list-hosts 2>/dev/null | sed -n 's/^ *hosts (\([0-9]*\)):.*/\1/p')"
  echo "${count:-0}"
}

# --- Results -----------------------------------------------------------------

# Each result: category|name|status|seconds|message
record() {
  RESULTS+=("$1|$2|$3|$4|${5:-}")
  [[ "$3" == "failed" ]] && FAILED=true
  return 0
}

xml_escape() {
  local s
  s="$(printf '%s' "$1" | tr -d '\000-\010\013\014\016-\037')"
  s="${s//&/&amp;}"
  s="${s//</&lt;}"
  s="${s//>/&gt;}"
  s="${s//\"/&quot;}"
  printf '%s' "$s"
}

write_junit() {
  local junit="$OUTPUT_DIR/junit/$SUITE.xml"
  local total=0 failures=0 skipped=0 entry category name status seconds message
  mkdir -p "$OUTPUT_DIR/junit"
  for entry in ${RESULTS[@]+"${RESULTS[@]}"}; do
    IFS='|' read -r category name status seconds message <<< "$entry"
    total=$((total + 1))
    [[ "$status" == "failed" ]] && failures=$((failures + 1))
    [[ "$status" == "skipped" ]] && skipped=$((skipped + 1))
  done
  {
    echo '<?xml version="1.0" encoding="UTF-8"?>'
    echo "<testsuites><testsuite name=\"$(xml_escape "$SUITE")\" tests=\"$total\" failures=\"$failures\" skipped=\"$skipped\">"
    for entry in ${RESULTS[@]+"${RESULTS[@]}"}; do
      IFS='|' read -r category name status seconds message <<< "$entry"
      printf '  <testcase classname="%s" name="%s" time="%s">' \
        "$(xml_escape "$category")" "$(xml_escape "$name")" "$seconds"
      case "$status" in
        failed) printf '<failure message="%s"/>' "$(xml_escape "$message")" ;;
        skipped) printf '<skipped message="%s"/>' "$(xml_escape "$message")" ;;
      esac
      echo "</testcase>"
    done
    echo "</testsuite></testsuites>"
  } > "$junit"
  log INFO "Results: tests/${junit#./} ($total tests, $failures failed, $skipped skipped)"
}

# The first error a reader needs, on one line: "<host>: <msg>", an Ansible ERROR!, or the exit code.
failure_message() {
  local logfile="$1" rc="$2" line host msg
  line="$(grep -m1 -E '(fatal|failed): \[' "$logfile" 2>/dev/null || true)"
  if [[ -n "$line" ]]; then
    host="$(sed -nE 's/.*(fatal|failed): \[([^]]+)\].*/\2/p' <<< "$line")"
    msg="$(grep -m1 -oE '"msg": "([^"\\]|\\.)*"' <<< "$line" | sed -E 's/^"msg": "//; s/"$//; s/\\"/"/g' || true)"
    if [[ -z "$msg" ]]; then
      msg="$(grep -A30 -m1 -E '(fatal|failed): \[' "$logfile" | grep -m1 -E '^ *"?msg"?: ' \
        | sed -E 's/^ *"?msg"?: *//; s/^"//; s/",?$//' || true)"
    fi
    echo "${host:-host}: ${msg:-task failed} (exit code $rc)" | head -c 300
    return
  fi
  line="$(grep -m1 '^ERROR!' "$logfile" 2>/dev/null || true)"
  if [[ -n "$line" ]]; then
    echo "$line" | head -c 300
    return
  fi
  echo "ansible-playbook exited with $rc"
}

# --- Containerlab lifecycle --------------------------------------------------

copy_license() {
  if [[ -n "${SRSIM_LICENSE_FILE:-}" ]]; then
    if [[ ! -r "$SRSIM_LICENSE_FILE" ]]; then
      log FAIL "SRSIM_LICENSE_FILE=$SRSIM_LICENSE_FILE is not readable"
      return 1
    fi
    cp "$SRSIM_LICENSE_FILE" license.txt
    chmod 600 license.txt
    touch license.copied
  fi
}

start_lab() {
  copy_license || return 1
  log INFO "Destroying a lab left behind by an earlier run, if any"
  sudo -E containerlab destroy -t "$TOPOLOGY_FILE" --cleanup > /dev/null 2>&1 || true
  log INFO "Deploying containerlab topology: $TOPOLOGY_FILE"
  sudo -E containerlab deploy -t "$TOPOLOGY_FILE" --reconfigure || return 1
  log OK "Lab deployed"
}

collect_node_logs() {
  local lab node dir="$OUTPUT_DIR/logs/$SUITE/nodes"
  lab="$(python3 -c 'import sys, yaml; print((yaml.safe_load(open(sys.argv[1])) or {}).get("name", ""))' \
    "$TOPOLOGY_FILE" 2>/dev/null || true)"
  [[ -n "$lab" ]] || return 0
  mkdir -p "$dir"
  for node in $(sudo docker ps -a --filter "label=containerlab=$lab" --format '{{.Names}}' 2>/dev/null); do
    { sudo docker logs "$node" 2>&1; } > "$dir/$node.log" || true
  done
}

stop_lab() {
  log INFO "Destroying containerlab topology: $TOPOLOGY_FILE"
  sudo -E containerlab destroy -t "$TOPOLOGY_FILE" --cleanup || true
  if [[ -f license.copied ]]; then
    rm -f license.txt license.copied
  fi
  log OK "Lab destroyed"
}

# --- Playbooks ---------------------------------------------------------------

run_playbook() {
  local category="$1" entry="$2" start rc=0 seconds logfile args
  read -ra args <<< "$entry"
  logfile="$OUTPUT_DIR/logs/$SUITE/${category}__$(basename "${args[0]}" .yml).log"
  start=$(date +%s)

  set +e
  if $QUIET; then
    log INFO "Running: ansible-playbook $entry"
    ansible-playbook "${args[@]}" > "$logfile" 2>&1
    rc=$?
  else
    log INFO "Running: ansible-playbook $entry"
    ansible-playbook "${args[@]}" 2>&1 | tee "$logfile" | sed 's/^/    /'
    rc=${PIPESTATUS[0]}
  fi
  set -e
  seconds=$(( $(date +%s) - start ))

  if [[ $rc -eq 130 ]]; then
    log FAIL "Interrupted"
    record "$category" "$entry" failed "$seconds" "interrupted"
    write_junit
    exit 130
  elif [[ $rc -ne 0 ]]; then
    log FAIL "$entry failed after ${seconds}s (log: tests/${logfile#./})"
    record "$category" "$entry" failed "$seconds" "$(failure_message "$logfile" "$rc")"
    if $EXIT_FIRST; then
      write_junit
      exit 1
    fi
  else
    log OK "$entry passed in ${seconds}s"
    record "$category" "$entry" passed "$seconds"
  fi
}

run_tests() {
  local category hosts count playbook
  mkdir -p "$OUTPUT_DIR/logs/$SUITE"
  log INFO "Running playbooks from $PLAYBOOK_FILE"
  for category in $(yaml_categories); do
    if [[ -n "$CATEGORY" && "$CATEGORY" != all && "$CATEGORY" != "$category" ]]; then
      continue
    fi
    log INFO "=== CATEGORY: $category ==="
    hosts="$(yaml_category_hosts "$category")"
    count="$(host_count "$hosts")"
    if [[ "$count" -eq 0 ]]; then
      log SKIP "$category: no hosts in inventory group '$hosts'"
      while IFS= read -r playbook; do
        record "$category" "$playbook" skipped 0 "no hosts in inventory group $hosts"
      done < <(yaml_playbooks "$category")
      continue
    fi
    while IFS= read -r playbook; do
      [[ -n "$playbook" ]] && run_playbook "$category" "$playbook"
    done < <(yaml_playbooks "$category")
  done
  write_junit
  if $FAILED; then
    return 1
  fi
}

integration() {
  local status=0
  if ! start_lab; then
    record lab deploy failed 0 "containerlab deploy failed for $TOPOLOGY_FILE"
    write_junit
    collect_node_logs
    stop_lab
    exit 1
  fi
  # A subshell, so that --exitfirst and Ctrl-C still reach stop_lab.
  ( run_tests ) || status=$?
  collect_node_logs
  stop_lab
  exit "$status"
}

# --- CLI ---------------------------------------------------------------------

COMMAND="${1:-help}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--topo) TOPOLOGY_FILE="$2"; shift 2 ;;
    -p|--playbooks) PLAYBOOK_FILE="$2"; shift 2 ;;
    -s|--suite) SUITE="$2"; shift 2 ;;
    -c|--category) CATEGORY="$2"; shift 2 ;;
    -x|--exitfirst) EXIT_FIRST=true; shift ;;
    -q|--quiet) QUIET=true; shift ;;
    *) echo "Unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$COMMAND" in
  integration) integration ;;
  deploy) start_lab ;;
  run) run_tests ;;
  destroy) stop_lab ;;
  help) awk 'NR > 3 { if (!/^#/) exit; sub(/^#    /, ""); sub(/^#/, ""); print }' "$(basename "$0")"; exit 0 ;;
  *) echo "Usage: $0 {integration|deploy|run|destroy|help}" >&2; exit 2 ;;
esac
