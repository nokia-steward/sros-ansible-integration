#!/usr/bin/env bash
#
#    run.sh — Manage containerlab lifecycle and run categorized Ansible playbooks
#
#    Usage:
#      ./run.sh <command> [options]
#
#    Commands:
#      deploy      Deploy containerlab topology
#      run         Run categorized playbooks
#      destroy     Destroy containerlab topology
#      sanity      Full sequence: deploy, run, destroy
#      help        Show this help message
#
#    Options:
#      -t, --topo <file>        Containerlab topology file (default: ./topo.clab.yml)
#      -p, --playbooks <file>   Playbook YAML inventory (default: ./playbooks.yml)
#      -c, --category <name>    Run only a specific category (default: all)
#      -q, --quiet              Suppress Ansible playbook console output
#      -a, --all                Run all tests aka continue on error
#      -l, --log <file>         Log file path for detailed test results
#      -n, --lab-name <name>    Override lab name (default: from topo.clab.yml)
#
#    Environment Variables:
#      LAB_NAME                 Override lab name for parallel execution
#      LOG_FILE                 Path to log file for test results
#      SROS_VERSION             SR OS version for containerlab (e.g., 25.7.R2)
#
#    Example:
#      ./run.sh deploy
#      ./run.sh run --category all --quiet --all --log results.log
#      ./run.sh destroy
#      LAB_NAME="test-123" ./run.sh sanity --all
#

set -euo pipefail

# --- Defaults ----------------------------------------------------------------

TOPOLOGY_FILE="./topo.clab.yml"
PLAYBOOK_FILE="./playbooks.yml"
CATEGORY=""
RUN_ALL=false
QUIET=false
LOG_FILE="${LOG_FILE:-}"
LAB_NAME="${LAB_NAME:-}"

# --- Logging -----------------------------------------------------------------

# Initialize test summary counters
TESTS_PASSED=0
TESTS_FAILED=0
FAILED_TESTS=()

log() {
  local bold="\033[1m"
  local color_red="\033[31m"
  local color_green="\033[32m"
  local color_yellow="\033[33m"
  local reset="\033[0m"

  local level="$1"; shift
  local msg="$*"
  local timestamp
  timestamp=$(date '+%Y-%m-%d %H:%M:%S')
  
  case "$level" in
    BOLD) 
      echo -e "${bold}${color_yellow}[INFO]${reset} ${bold}$msg${reset}"
      [[ -n "$LOG_FILE" ]] && echo "[$timestamp] [INFO] $msg" >> "$LOG_FILE"
      ;;
    INFO) 
      echo -e "${color_yellow}[INFO]${reset} $msg"
      [[ -n "$LOG_FILE" ]] && echo "[$timestamp] [INFO] $msg" >> "$LOG_FILE"
      ;;
    OK) 
      echo -e "${color_green}[OK]${reset} $msg"
      [[ -n "$LOG_FILE" ]] && echo "[$timestamp] [OK] $msg" >> "$LOG_FILE"
      ;;
    FAIL) 
      echo -e "${color_red}[FAIL]${reset} $msg"
      [[ -n "$LOG_FILE" ]] && echo "[$timestamp] [FAIL] $msg" >> "$LOG_FILE"
      ;;
    *) 
      echo "$msg"
      [[ -n "$LOG_FILE" ]] && echo "[$timestamp] $msg" >> "$LOG_FILE"
      ;;
  esac
}

print_summary() {
  local total=$((TESTS_PASSED + TESTS_FAILED))
  log INFO "========================================="
  log INFO "Test Summary"
  log INFO "========================================="
  log INFO "Total tests:  $total"
  log INFO "Passed:       $TESTS_PASSED"
  if [[ $TESTS_FAILED -gt 0 ]]; then
    log FAIL "Failed:       $TESTS_FAILED"
  else
    log INFO "Failed:       $TESTS_FAILED"
  fi
  
  if [[ $TESTS_FAILED -gt 0 ]]; then
    log INFO ""
    log INFO "Failed tests:"
    for test in "${FAILED_TESTS[@]}"; do
      log FAIL "  - $test"
    done
  fi
  log INFO "========================================="
}

# --- YAML Helpers ------------------------------------------------------------

yaml_categories() {
python3 - "$PLAYBOOK_FILE" << EOF
import sys, yaml
data = yaml.safe_load(open(sys.argv[1]))
for c in data.get("categories", {}): print(c)
EOF
}

yaml_playbooks() {
python3 - "$PLAYBOOK_FILE" "$1" << EOF
import sys, yaml
data = yaml.safe_load(open(sys.argv[1]))
cat = sys.argv[2]
for p in data.get("categories", {}).get(cat, {}).get("playbooks", []): print(p)
EOF
}

# --- Containerlab Lifecycle --------------------------------------------------

start_lab() {
  local topo_args=(-t "$TOPOLOGY_FILE" --reconfigure)
  
  # If LAB_NAME is set, override the lab name
  if [[ -n "$LAB_NAME" ]]; then
    log INFO "Deploying containerlab with custom lab name: $LAB_NAME"
    topo_args+=(--name "$LAB_NAME")
  else
    log INFO "Deploying containerlab topology: $TOPOLOGY_FILE"
  fi
  
  sudo --preserve-env=SROS_VERSION containerlab deploy "${topo_args[@]}"
  log OK "Containerlab deployed successfully"
}

stop_lab() {
  local topo_args=(-t "$TOPOLOGY_FILE")
  
  # If LAB_NAME is set, use it for destroy
  if [[ -n "$LAB_NAME" ]]; then
    log INFO "Destroying containerlab: $LAB_NAME"
    topo_args+=(--name "$LAB_NAME")
  else
    log INFO "Destroying containerlab topology"
  fi
  
  sudo --preserve-env=SROS_VERSION containerlab destroy "${topo_args[@]}" || true
  log OK "Containerlab destroyed"
}

# --- Playbook Runner ---------------------------------------------------------

run_playbook() {
  local pb="${1:-}"
  local start_time
  start_time=$(date +%s)
  local result=0

  # Playbook entries may carry extra ansible-playbook options, e.g. "--diff"
  local pb_args
  read -ra pb_args <<< "$pb"

  # Create a temporary log file for this playbook execution
  local pb_log_file=""
  if [[ -n "$LOG_FILE" ]]; then
    pb_log_file="${LOG_FILE%.log}-$(basename "${pb_args[0]}").log"
  fi

  # Execute quietly or verbosely
  set +e
  if $QUIET; then
    log INFO "Running: ansible-playbook $pb"
    if [[ -n "$pb_log_file" ]]; then
      ansible-playbook "${pb_args[@]}" > "$pb_log_file" 2>&1
      result=$?
    else
      ansible-playbook "${pb_args[@]}" >/dev/null 2>&1
      result=$?
    fi
  else
    log BOLD "Running: ansible-playbook $pb"
    if [[ -n "$pb_log_file" ]]; then
      ANSIBLE_FORCE_COLOR=true ansible-playbook "${pb_args[@]}" 2>&1 | tee "$pb_log_file" | sed 's/^/    /'
      result=${PIPESTATUS[0]}
    else
      ANSIBLE_FORCE_COLOR=true ansible-playbook "${pb_args[@]}" 2>&1 | sed 's/^/    /'
      result=${PIPESTATUS[0]}
    fi
  fi
  set -e

  local duration=$(( $(date +%s) - start_time ))

  if [[ ${result} -eq 120 ]]; then
    log FAIL "Execution interrupted by user (Ctrl-C)"
    exit "$result"
  elif [[ ${result} -ne 0 ]]; then
    TESTS_FAILED=$((TESTS_FAILED + 1))
    FAILED_TESTS+=("$pb")
    log FAIL "$pb failed after ${duration}s"
    [[ -n "$pb_log_file" ]] && log INFO "  Details in: $pb_log_file"
    if ! $RUN_ALL; then
      # terminate script
      exit 1
    fi
  else
    TESTS_PASSED=$((TESTS_PASSED + 1))
    log OK "$pb succeeded in ${duration}s"
  fi
}

# --- Test Orchestration ------------------------------------------------------

run_tests() {
  log INFO "Running playbooks from $PLAYBOOK_FILE"
  
  # Initialize log file if specified
  if [[ -n "$LOG_FILE" ]]; then
    log INFO "Test logs will be written to: $LOG_FILE"
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Test Execution Log - Started at $(date)" > "$LOG_FILE"
    echo "==========================================" >> "$LOG_FILE"
  fi
  
  for cat in $(yaml_categories); do
    if [[ -n "$CATEGORY" && "$CATEGORY" != "all" && "$CATEGORY" != "$cat" ]]; then
      continue
    fi
    
    log INFO "=== CATEGORY: $cat ==="

    while IFS= read -r playbook; do
      [[ -n "$playbook" ]] || continue
      run_playbook "$playbook"
    done < <(yaml_playbooks "$cat")
  done
  
  # Print summary at the end
  print_summary
  
  # Exit with error if any tests failed
  if [[ $TESTS_FAILED -gt 0 ]]; then
    exit 1
  fi
}

# --- Sanity Sequence ---------------------------------------------------------

sanity_run() {
  log INFO "Starting full sanity sequence"
  start_lab
  run_tests
  stop_lab
  log OK "Sanity sequence completed"
}

# --- CLI ---------------------------------------------------------------------

COMMAND="${1:-sanity}"
shift || true

while [[ $# -gt 0 ]]; do
  case "$1" in
    -t|--topo) TOPOLOGY_FILE="$2"; shift 2 ;;
    -p|--playbooks) PLAYBOOK_FILE="$2"; shift 2 ;;
    -c|--category) CATEGORY="$2"; shift 2 ;;
    -q|--quiet) QUIET=true; shift ;;
    -a|--all) RUN_ALL=true; shift ;;
    -l|--log) LOG_FILE="$2"; shift 2 ;;
    -n|--lab-name) LAB_NAME="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

case "$COMMAND" in
  deploy) start_lab ;;
  run) run_tests ;;
  destroy) stop_lab ;;
  sanity) sanity_run ;;
  help) grep '^#  ' "$0" | sed 's/^# \{0,4\}//'; exit 0 ;;
  *) echo "Usage: $0 {deploy|run|destroy|sanity|help}"; exit 1 ;;
esac
