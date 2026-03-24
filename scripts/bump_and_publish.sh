#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage: scripts/publish.sh [patch|minor|major] [--dry-run]

Bumps the package version based on the latest v* git tag, updates pyproject.toml,
refreshes uv.lock, creates a release commit, tags it, and pushes the tag.

Arguments:
  patch      Increment the patch version (default)
  minor      Increment the minor version and reset patch to 0
  major      Increment the major version and reset minor/patch to 0
  --dry-run  Print the commands without mutating git state or pushing
EOF
}

log() {
  printf '%s\n' "$*"
}

die() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

run() {
  log "+ $*"
  if [[ "${DRY_RUN}" == "true" ]]; then
    return 0
  fi
  "$@"
}

require_clean_worktree() {
  if [[ -n "$(git status --porcelain)" ]]; then
    die "working tree must be clean before publishing"
  fi
}

read_current_version() {
  local version
  version="$(sed -nE 's/^version = "([^"]+)"$/\1/p' pyproject.toml | head -n 1)"
  [[ -n "${version}" ]] || die "could not find project version in pyproject.toml"
  printf '%s\n' "${version}"
}

read_last_tag() {
  git tag --list 'v*' --sort=-v:refname | head -n 1
}

next_version_from_tag() {
  local version="$1"
  local bump_part="$2"
  local major minor patch

  IFS='.' read -r major minor patch <<<"${version}"
  [[ "${major}" =~ ^[0-9]+$ ]] || die "invalid major version: ${major}"
  [[ "${minor}" =~ ^[0-9]+$ ]] || die "invalid minor version: ${minor}"
  [[ "${patch}" =~ ^[0-9]+$ ]] || die "invalid patch version: ${patch}"

  case "${bump_part}" in
    patch)
      patch=$((patch + 1))
      ;;
    minor)
      minor=$((minor + 1))
      patch=0
      ;;
    major)
      major=$((major + 1))
      minor=0
      patch=0
      ;;
    *)
      die "unsupported bump type: ${bump_part}"
      ;;
  esac

  printf '%s\n' "${major}.${minor}.${patch}"
}

update_pyproject_version() {
  local new_version="$1"
  perl -0pi -e 's/^version = "[^"]+"$/version = "'"${new_version}"'"/m' pyproject.toml
}

BUMP_PART="patch"
DRY_RUN="false"

for arg in "$@"; do
  case "${arg}" in
    patch|minor|major)
      BUMP_PART="${arg}"
      ;;
    --dry-run)
      DRY_RUN="true"
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: ${arg}"
      ;;
  esac
done

command -v git >/dev/null 2>&1 || die "git is required"
command -v uv >/dev/null 2>&1 || die "uv is required"
command -v perl >/dev/null 2>&1 || die "perl is required"

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "${REPO_ROOT}"

[[ -f pyproject.toml ]] || die "pyproject.toml not found"

require_clean_worktree

LAST_TAG="$(read_last_tag || true)"
CURRENT_VERSION="$(read_current_version)"

if [[ -n "${LAST_TAG}" ]]; then
  BASE_VERSION="${LAST_TAG#v}"
  NEW_VERSION="$(next_version_from_tag "${BASE_VERSION}" "${BUMP_PART}")"
else
  BASE_VERSION="${CURRENT_VERSION}"
  NEW_VERSION="${CURRENT_VERSION}"
  log "No existing v* tag found; using pyproject version ${NEW_VERSION} for the first release."
fi

NEW_TAG="v${NEW_VERSION}"

if git rev-parse -q --verify "refs/tags/${NEW_TAG}" >/dev/null; then
  die "tag ${NEW_TAG} already exists"
fi

log "Last release tag: ${LAST_TAG:-<none>}"
log "Current pyproject version: ${CURRENT_VERSION}"
log "Next release version: ${NEW_VERSION}"

if [[ "${CURRENT_VERSION}" != "${NEW_VERSION}" ]]; then
  if [[ "${DRY_RUN}" == "true" ]]; then
    log "+ update pyproject.toml version -> ${NEW_VERSION}"
  else
    update_pyproject_version "${NEW_VERSION}"
  fi
fi

run uv lock
run git add pyproject.toml uv.lock

if git diff --cached --quiet; then
  log "No release file changes to commit; tagging the current HEAD."
else
  run git commit -m "Release ${NEW_TAG}"
fi

run git tag -a "${NEW_TAG}" -m "Release ${NEW_TAG}"
run git push origin "${NEW_TAG}"

if [[ "${DRY_RUN}" == "false" ]]; then
  log "Release tag ${NEW_TAG} pushed."
  log "If you want the release commit on the branch as well, run: git push origin HEAD"
fi
