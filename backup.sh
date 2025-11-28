#!/usr/bin/env bash
###############################################################################
# Backup Script for MPD Web Control
#
# Creates a compressed tar.gz archive of the project root while excluding
# transient or unnecessary directories. Places a copy in the project `backups/`
# directory AND a copy in the user's home directory. Retains only the most
# recent N (default 2) matching backups in EACH location and deletes older
# ones automatically.
#
# Usage:
#   ./backup.sh                        # Create backup with default retention (2)
#   RETENTION_COUNT=3 ./backup.sh      # Keep 3 most recent instead of 2
#   DESCRIPTION=pre_upgrade ./backup.sh  # Append a label before .tar.gz
#   HOME_BACKUP_DIR=/custom/path ./backup.sh  # Override home destination
#   SKIP_HOME_COPY=1 ./backup.sh       # Only create project backup
#
# Environment Variables:
#   RETENTION_COUNT    Number of backups to retain per location (default: 2)
#   DESCRIPTION        Optional label appended to archive name
#   HOME_BACKUP_DIR    Destination for second copy (default: $HOME)
#   EXTRA_BACKUP_DIRS  Optional additional destinations (comma- or colon-separated)
#                      e.g. "/mnt/nas_backups,/media/usb/backups" (retention applies to each)
#   SKIP_HOME_COPY     If set (non-empty), skip creating home copy
#
# Archive Naming Convention:
#   mpd_web_control_backup_YYYYmmdd_HHMMSS[_DESCRIPTION].tar.gz
#
# Exit Codes:
#   0 Success
#   1 Failure (script will abort on first error due to 'set -e')
###############################################################################
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/backups"
RETENTION_COUNT="${RETENTION_COUNT:-2}"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
PROJECT_NAME="mpd_web_control"
DESCRIPTION_SUFFIX="${DESCRIPTION:+_${DESCRIPTION}}"
ARCHIVE_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}${DESCRIPTION_SUFFIX}.tar.gz"
ARCHIVE_PATH="${BACKUP_DIR}/${ARCHIVE_NAME}"
HOME_BACKUP_DIR="${HOME_BACKUP_DIR:-${HOME}}"
SKIP_HOME_COPY="${SKIP_HOME_COPY:-}" # empty means do copy
EXTRA_BACKUP_DIRS_RAW="${EXTRA_BACKUP_DIRS:-}"

mkdir -p "${BACKUP_DIR}"

echo "[INFO] Creating project backup: ${ARCHIVE_PATH}" >&2
echo "[INFO] Retention count (per location): ${RETENTION_COUNT}" >&2
if [[ -n "${DESCRIPTION_SUFFIX}" ]]; then
  echo "[INFO] Description suffix applied: ${DESCRIPTION_SUFFIX}" >&2
fi
if [[ -n "${SKIP_HOME_COPY}" ]]; then
  echo "[INFO] Home copy will be skipped (SKIP_HOME_COPY set)." >&2
else
  echo "[INFO] Home backup destination: ${HOME_BACKUP_DIR}" >&2
fi

# Normalize EXTRA_BACKUP_DIRS as an array (supports comma or colon separators)
IFS=',:' read -r -a EXTRA_DIRS <<< "${EXTRA_BACKUP_DIRS_RAW}"
if [[ -n "${EXTRA_BACKUP_DIRS_RAW}" ]]; then
  echo "[INFO] Extra backup destinations detected (${#EXTRA_DIRS[@]}):" >&2
  for d in "${EXTRA_DIRS[@]}"; do
    [[ -n "$d" ]] && echo "       - $d" >&2 || true
  done
fi

# Build list of tar exclude patterns. Adjust as needed.
EXCLUDES=(
  "--exclude=./backups"          # Don't nest backups
  "--exclude=./__pycache__"      # Python bytecode cache
  "--exclude=./venv"             # Virtual environment (can be recreated)
)

# Create archive from project root.
tar "${EXCLUDES[@]}" -czf "${ARCHIVE_PATH}" -C "${PROJECT_ROOT}" .

echo "[INFO] Project backup created successfully." >&2

# Optional second copy to home (or overridden) directory.
if [[ -z "${SKIP_HOME_COPY}" ]]; then
  mkdir -p "${HOME_BACKUP_DIR}"
  HOME_ARCHIVE_PATH="${HOME_BACKUP_DIR}/${ARCHIVE_NAME}"
  cp "${ARCHIVE_PATH}" "${HOME_ARCHIVE_PATH}"
  echo "[INFO] Home copy created: ${HOME_ARCHIVE_PATH}" >&2
fi

# Optional extra copies to additional destinations.
for EXTRA_DIR in "${EXTRA_DIRS[@]}"; do
  if [[ -z "${EXTRA_DIR}" ]]; then continue; fi
  echo "[INFO] Creating extra copy in: ${EXTRA_DIR}" >&2
  mkdir -p "${EXTRA_DIR}" || { echo "[WARN] Could not create ${EXTRA_DIR}, skipping." >&2; continue; }
  EXTRA_ARCHIVE_PATH="${EXTRA_DIR}/${ARCHIVE_NAME}"
  if cp "${ARCHIVE_PATH}" "${EXTRA_ARCHIVE_PATH}" 2>/dev/null; then
    echo "[INFO] Extra copy created: ${EXTRA_ARCHIVE_PATH}" >&2
  else
    echo "[WARN] Failed to copy to ${EXTRA_DIR} (permission or space issue?), skipping." >&2
  fi
done

manage_retention() {
  local dir="$1"
  echo "[INFO] Applying retention in: ${dir}" >&2
  # Pattern restricted to mpd_web_control_backup_*.tar.gz
  mapfile -t BK < <(ls -1t "${dir}"/mpd_web_control_backup_*.tar.gz 2>/dev/null || true)
  if (( ${#BK[@]} == 0 )); then
    echo "[INFO] No matching backups found in ${dir}." >&2
    return 0
  fi
  if (( ${#BK[@]} > RETENTION_COUNT )); then
    echo "[INFO] Found ${#BK[@]} backups; pruning to ${RETENTION_COUNT}." >&2
    for (( i=RETENTION_COUNT; i<${#BK[@]}; i++ )); do
      echo "[INFO] Removing old backup: ${BK[$i]}" >&2
      rm -f "${BK[$i]}"
    done
  else
    echo "[INFO] Backup count (${#BK[@]}) within retention limit (${RETENTION_COUNT})." >&2
  fi
  echo "[INFO] Remaining backups in ${dir}:" >&2
  ls -1 "${dir}"/mpd_web_control_backup_*.tar.gz >&2 || true
}

# Retention in project backups directory.
manage_retention "${BACKUP_DIR}"
# Retention in home (or overridden) directory when copy performed.
if [[ -z "${SKIP_HOME_COPY}" ]]; then
  manage_retention "${HOME_BACKUP_DIR}"
fi

# Apply retention policy to all extra destinations as well
for EXTRA_DIR in "${EXTRA_DIRS[@]}"; do
  if [[ -z "${EXTRA_DIR}" ]]; then continue; fi
  manage_retention "${EXTRA_DIR}"
done

echo "[SUCCESS] Backup process complete (dual-location)." >&2
