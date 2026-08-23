#!/usr/bin/env bash
#
# Phase 0 — Git Versioning & Branch Strategy
# ------------------------------------------
# Establishes the safety net BEFORE the v2 refactor touches any file.
#
#   1. Tags the end-of-internship state as v1.0-internship (retroactive, annotated)
#   2. Preserves in-flight security work
#   3. Creates v2-ai-harness off the hardened HEAD
#
# Idempotent: safe to re-run. Never force-pushes. Never discards work.
#
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

INTERNSHIP_COMMIT="68e481b"   # 2026-02-19 — tip of main, last commit before the Mar–May gap
INTERNSHIP_TAG="v1.0-internship"
V2_BRANCH="v2-ai-harness"
BASE_BRANCH="security/day1-hardening"   # carries Day-1 hardening; ahead of main

info() { printf '\033[1;34m▶ %s\033[0m\n' "$*"; }
ok()   { printf '\033[1;32m✔ %s\033[0m\n' "$*"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$*"; }

# ── 1. Sanity: the target commit must exist ──────────────────────────────────
info "Verifying internship commit ${INTERNSHIP_COMMIT}"
git rev-parse --verify --quiet "${INTERNSHIP_COMMIT}^{commit}" >/dev/null || {
  echo "FATAL: commit ${INTERNSHIP_COMMIT} not found." >&2; exit 1;
}
ok "$(git log -1 --format='%h %ad %s' --date=short "$INTERNSHIP_COMMIT")"

# ── 2. Retroactive annotated tag ─────────────────────────────────────────────
# Annotated (-a) not lightweight: carries a message, a tagger, and a date, and
# is what `git describe` and GitHub Releases expect.
if git rev-parse --verify --quiet "refs/tags/${INTERNSHIP_TAG}" >/dev/null; then
  warn "Tag ${INTERNSHIP_TAG} already exists — leaving untouched."
else
  info "Tagging ${INTERNSHIP_COMMIT} as ${INTERNSHIP_TAG}"
  git tag -a "${INTERNSHIP_TAG}" "${INTERNSHIP_COMMIT}" -m \
"NLPForge v1.0 — Internship Delivery

Two-stage semantic retrieval prototype (Sep 2025 – Feb 2026).

  FastAPI + Next.js + Redis HNSW + Celery + Ollama
  8 LLM providers, multi-model embedding registry, Docker Compose
  ~33k LOC Python / ~35k LOC TypeScript

Known limitations addressed in v2 (see v2-ai-harness):
  - Stage 2 was score aggregation, not cross-encoder reranking
  - No retrieval evaluation harness
  - Blocking Redis I/O on the async hot path
  - Prometheus collectors defined but never invoked
  - Application-level tenancy (hand-written u_id filters)"
  ok "Created annotated tag ${INTERNSHIP_TAG}"
fi

# ── 3. Preserve in-flight work ───────────────────────────────────────────────
# `git checkout -b` carries uncommitted changes into the new branch, so nothing
# is lost — but we snapshot to a throwaway stash ref first as a belt-and-braces
# recovery point. `stash create` records without mutating the working tree.
DIRTY_COUNT="$(git status --porcelain | wc -l | tr -d ' ')"
if [ "$DIRTY_COUNT" -gt 0 ]; then
  warn "${DIRTY_COUNT} uncommitted change(s) present — creating recovery snapshot"
  SNAP="$(git stash create "phase0 pre-refactor snapshot")" || true
  if [ -n "${SNAP:-}" ]; then
    git update-ref refs/snapshots/phase0-pre-refactor "$SNAP"
    ok "Recovery snapshot at refs/snapshots/phase0-pre-refactor ($(echo "$SNAP" | cut -c1-8))"
    echo "  restore with:  git checkout refs/snapshots/phase0-pre-refactor -- ."
  fi
fi

# ── 4. Create / switch to the v2 branch ──────────────────────────────────────
CURRENT="$(git rev-parse --abbrev-ref HEAD)"
if git rev-parse --verify --quiet "refs/heads/${V2_BRANCH}" >/dev/null; then
  warn "Branch ${V2_BRANCH} exists — switching to it."
  git checkout "${V2_BRANCH}"
else
  if [ "$CURRENT" != "$BASE_BRANCH" ]; then
    info "Basing ${V2_BRANCH} on ${BASE_BRANCH} (currently on ${CURRENT})"
    git checkout "${BASE_BRANCH}"
  fi
  info "Creating ${V2_BRANCH} from $(git rev-parse --short HEAD)"
  git checkout -b "${V2_BRANCH}"   # uncommitted changes come along
  ok "On ${V2_BRANCH} — main and ${BASE_BRANCH} are now protected"
fi

# ── 5. Report ────────────────────────────────────────────────────────────────
echo
info "State:"
printf '  branch : %s\n' "$(git rev-parse --abbrev-ref HEAD)"
printf '  head   : %s\n' "$(git log -1 --format='%h %s')"
printf '  tags   : %s\n' "$(git tag -l | tr '\n' ' ')"
printf '  dirty  : %s file(s)\n' "$(git status --porcelain | wc -l | tr -d ' ')"
echo
warn "NOT pushed. Publish deliberately when ready:"
echo "    git push origin ${INTERNSHIP_TAG}"
echo "    git push -u origin ${V2_BRANCH}"
