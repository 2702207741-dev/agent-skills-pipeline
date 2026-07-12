#!/usr/bin/env bash
# Full v1.0-v3.3 regression suite
# Usage: bash scripts/test_all.sh
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0
FAIL=0
if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "python3 or python is required" >&2
    exit 1
fi

pass() { echo "  [PASS] $1"; PASS=$((PASS + 1)); }
fail() { echo "  [FAIL] $1"; FAIL=$((FAIL + 1)); }

echo "============================================"
echo " our-skills Full Test Suite (v1.0 - v3.3)"
echo "============================================"
EXPECTED_SKILLS=$("$PYTHON" -c "import json; print(len(json.load(open('skills.json'))['skills']))")
RELEASE=$("$PYTHON" -c "import json; print('v' + json.load(open('skills.json'))['version'])")
EXPECTED_TRACES=$((EXPECTED_SKILLS * 3))

# ── 1. Registry & Format ──────────────────────
echo ""
echo "── 1. Registry & Format ──"

cd "$ROOT"
if "$PYTHON" scripts/check_registry.py; then
    pass "check_registry.py"
else
    fail "check_registry.py"
fi

if "$PYTHON" scripts/validate-skill.py */SKILL.md; then
    pass "validate-skill.py ($EXPECTED_SKILLS skills)"
else
    fail "validate-skill.py"
fi

if "$PYTHON" scripts/check_skill_graph.py; then
    pass "check_skill_graph.py"
else
    fail "check_skill_graph.py"
fi

if "$PYTHON" scripts/generate_platform_reports.py --check; then
    pass "generate_platform_reports.py --check"
else
    fail "generate_platform_reports.py --check"
fi

if "$PYTHON" scripts/generate_example_dataset.py --check; then
    pass "generate_example_dataset.py --check"
else
    fail "generate_example_dataset.py --check"
fi

if "$PYTHON" scripts/run_model_eval.py --check; then
    pass "run_model_eval.py --check"
else
    fail "run_model_eval.py --check"
fi

if "$PYTHON" scripts/check_ecosystem.py; then
    pass "check_ecosystem.py"
else
    fail "check_ecosystem.py"
fi

if "$PYTHON" scripts/check_release_archive.py; then
    pass "check_release_archive.py"
else
    fail "check_release_archive.py"
fi

if "$PYTHON" scripts/check_publication_ready.py; then
    pass "check_publication_ready.py"
else
    fail "check_publication_ready.py"
fi

if "$PYTHON" scripts/review_bot.py --all --check --output "$(mktemp -t our-skills-review-bot-XXXXXX.json)"; then
    pass "review_bot.py --all --check"
else
    fail "review_bot.py --all --check"
fi

# ── 2. Fixtures & Matrix ──────────────────────
echo ""
echo "── 2. Fixtures & Platform Matrix ──"

if "$PYTHON" scripts/run_fixture_checks.py; then
    pass "run_fixture_checks.py"
else
    fail "run_fixture_checks.py"
fi

# ── 3. Security ───────────────────────────────
echo ""
echo "── 3. Security Scan ──"

if "$PYTHON" scripts/security_scan.py; then
    pass "security_scan.py"
else
    fail "security_scan.py"
fi

if "$PYTHON" scripts/check_supply_chain.py; then
    pass "check_supply_chain.py (OIDC, Sigstore, SLSA, standard OSS tools)"
else
    fail "check_supply_chain.py"
fi

if "$PYTHON" scripts/check_maintenance_evidence.py; then
    pass "check_maintenance_evidence.py (12 records, four workflows)"
else
    fail "check_maintenance_evidence.py"
fi

# ── 4. RigorBench E2E ─────────────────────────
echo ""
echo "── 4. RigorBench E2E Replay ──"

if "$PYTHON" scripts/run_rigorbench.py; then
    pass "run_rigorbench.py ($EXPECTED_TRACES traces, $EXPECTED_SKILLS skills)"
else
    fail "run_rigorbench.py"
fi

# ── 5. Packaging ──────────────────────────────
echo ""
echo "── 5. Package ──"

PKG_DIR=$(mktemp -d -t our-skills-pkg-XXXXXX)
if "$PYTHON" scripts/package_skill.py --all "$PKG_DIR"; then
    COUNT=$(find "$PKG_DIR" -name '*.zip' | wc -l)
    if [ "$COUNT" -eq "$EXPECTED_SKILLS" ]; then
        pass "package_skill.py --all ($EXPECTED_SKILLS zips)"
    else
        fail "package_skill.py --all (expected $EXPECTED_SKILLS, got $COUNT)"
    fi
else
    fail "package_skill.py --all"
fi
rm -rf "$PKG_DIR"

# ── 6. Release Artifacts ──────────────────────
echo ""
echo "── 6. Release Creation ──"

# 6a: dry-run
if "$PYTHON" scripts/create_release.py --dry-run; then
    pass "create_release.py --dry-run"
else
    fail "create_release.py --dry-run"
fi

# 6b: full generation
REL_DIR=$(mktemp -d -t our-skills-rel-XXXXXX)
if "$PYTHON" scripts/create_release.py --output "$REL_DIR"; then
    MISSING=""
    for f in "our-skills-$RELEASE.zip" "our-skills-$RELEASE.manifest.json" "our-skills-$RELEASE.sha256" \
             "our-skills-$RELEASE.sbom.json" "our-skills-$RELEASE.provenance.json" "our-skills-$RELEASE.sig" \
             "our-skills-$RELEASE.marketplace-index.json" "our-skills-$RELEASE.quality-dashboard.json" \
             "our-skills-$RELEASE.skill-graph-report.json" "our-skills-$RELEASE.model-eval-report.json"; do
        [ -f "$REL_DIR/$f" ] || MISSING="$MISSING $f"
    done
    if [ -z "$MISSING" ]; then
        pass "create_release.py (platform sidecars present)"
    else
        fail "create_release.py (missing:$MISSING)"
    fi
else
    fail "create_release.py --output"
fi
rm -rf "$REL_DIR"

# ── 7. Release Verification (one-command) ─────
echo ""
echo "── 7. verify_release.py (one-command gate) ──"

if "$PYTHON" scripts/verify_release.py; then
    pass "verify_release.py (full chain)"
else
    fail "verify_release.py"
fi

# ── 8. Marketplace ────────────────────────────
echo ""
echo "── 8. Marketplace ──"

MKT_HOME=$(mktemp -d -t our-skills-mkt-XXXXXX)

# 8a: list
if "$PYTHON" scripts/marketplace.py list > /dev/null; then
    pass "marketplace.py list"
else
    fail "marketplace.py list"
fi

# 8b: dry-run default (must NOT write)
BEFORE=$(find "$MKT_HOME" -type f 2>/dev/null | wc -l)
"$PYTHON" scripts/marketplace.py install --platform codex --target-root "$MKT_HOME" > /dev/null 2>&1 || true
AFTER=$(find "$MKT_HOME" -type f 2>/dev/null | wc -l)
if [ "$BEFORE" -eq "$AFTER" ]; then
    pass "marketplace.py default dry-run (no files written)"
else
    fail "marketplace.py default dry-run (wrote files!)"
fi

# 8c: apply mode (must write)
"$PYTHON" scripts/marketplace.py install --platform codex --target-root "$MKT_HOME" --apply > /dev/null 2>&1
if [ -f "$MKT_HOME/.codex/skills/skill-review-workflow/SKILL.md" ]; then
    pass "marketplace.py install --apply"
else
    fail "marketplace.py install --apply"
fi

# 8d: doctor
if "$PYTHON" scripts/marketplace.py doctor --platform codex --target-root "$MKT_HOME" --strict > /dev/null; then
    pass "marketplace.py doctor --strict"
else
    fail "marketplace.py doctor --strict"
fi

# 8e: update + rollback
"$PYTHON" scripts/marketplace.py update --platform codex --target-root "$MKT_HOME" --skill skill-review-workflow --apply > /dev/null 2>&1
"$PYTHON" scripts/marketplace.py rollback --platform codex --target-root "$MKT_HOME" --skill skill-review-workflow --apply > /dev/null 2>&1

# 8f: audit log
AUDIT_LOG="$MKT_HOME/.our-skills-audit/events.jsonl"
if [ -f "$AUDIT_LOG" ]; then
    if grep -q '"action": "install"' "$AUDIT_LOG" && grep -q '"action": "update"' "$AUDIT_LOG" && grep -q '"action": "rollback"' "$AUDIT_LOG"; then
        pass "marketplace audit log (install+update+rollback recorded)"
    else
        fail "marketplace audit log (missing expected actions)"
    fi
else
    fail "marketplace audit log (events.jsonl missing)"
fi

rm -rf "$MKT_HOME"

# ── 9. install.sh ─────────────────────────────
echo ""
echo "── 9. install.sh ──"

SH_HOME=$(mktemp -d -t our-skills-sh-XXXXXX)
mkdir -p "$SH_HOME/.codex/skills"

# 9a: dry-run (must NOT write)
BEFORE=$(find "$SH_HOME/.codex/skills" -type f 2>/dev/null | wc -l)
HOME="$SH_HOME" bash scripts/install.sh --dry-run > /dev/null 2>&1 || true
AFTER=$(find "$SH_HOME/.codex/skills" -type f 2>/dev/null | wc -l)
if [ "$BEFORE" -eq "$AFTER" ]; then
    pass "install.sh --dry-run (no files written)"
else
    fail "install.sh --dry-run (wrote files!)"
fi

# 9b: --yes (must write + backup existing)
HOME="$SH_HOME" bash scripts/install.sh --yes > /dev/null 2>&1
INSTALLED=$(find "$SH_HOME/.codex/skills" -name 'SKILL.md' 2>/dev/null | wc -l)
if [ "$INSTALLED" -ge "$EXPECTED_SKILLS" ]; then
    pass "install.sh --yes ($INSTALLED skills installed)"
else
    fail "install.sh --yes (expected >=$EXPECTED_SKILLS, got $INSTALLED)"
fi

rm -rf "$SH_HOME"

# ── 10. Negative Tests ────────────────────────
echo ""
echo "── 10. Negative Tests ──"

# 10a: tampered trace hash
TMP_TRACE=$("$PYTHON" -c "import tempfile; f = tempfile.NamedTemporaryFile(prefix='trace-', suffix='.json', delete=False); print(f.name.replace('\\\\', '/')); f.close()")
"$PYTHON" -c "
import json
with open('eval-runs/rigorbench-v1.3/traces.json') as f:
    data = json.load(f)
data['traces'][0]['skill_sha256'] = '0000000000000000000000000000000000000000000000000000000000000000'
with open('$TMP_TRACE', 'w') as f:
    json.dump(data, f)
"
if ! "$PYTHON" scripts/run_rigorbench.py --runs-file "$TMP_TRACE" > /dev/null 2>&1; then
    pass "RigorBench detects stale skill_sha256"
else
    fail "RigorBench did NOT detect stale skill_sha256"
fi
rm -f "$TMP_TRACE"

# 10b: tampered maintenance Git blob
TMP_MAINTENANCE=$("$PYTHON" -c "import tempfile; f = tempfile.NamedTemporaryFile(prefix='maintenance-', suffix='.json', delete=False); print(f.name.replace('\\\\', '/')); f.close()")
"$PYTHON" -c "
import json
with open('eval-runs/codex-maintenance/traces.json') as f:
    data = json.load(f)
data['records'][0]['files_read'][0]['git_blob'] = '0000000000000000000000000000000000000000'
with open('$TMP_MAINTENANCE', 'w') as f:
    json.dump(data, f)
"
if ! "$PYTHON" scripts/check_maintenance_evidence.py --runs-file "$TMP_MAINTENANCE" > /dev/null 2>&1; then
    pass "maintenance evidence detects stale Git blob"
else
    fail "maintenance evidence did NOT detect stale Git blob"
fi
rm -f "$TMP_MAINTENANCE"

# 10c: malformed source identity must not produce provenance
TMP_SLSA_DIR=$(mktemp -d -t our-skills-slsa-negative-XXXXXX)
printf 'artifact\n' > "$TMP_SLSA_DIR/artifact.zip"
if ! "$PYTHON" scripts/generate_slsa_provenance.py \
    --artifact "$TMP_SLSA_DIR/artifact.zip" \
    --output "$TMP_SLSA_DIR/provenance.json" \
    --source-uri "https://github.com/example/our-skills" \
    --source-commit "short" > /dev/null 2>&1; then
    pass "SLSA generator rejects an incomplete source commit"
else
    fail "SLSA generator accepted an incomplete source commit"
fi
rm -rf "$TMP_SLSA_DIR"

# ── Summary ────────────────────────────────────
echo ""
echo "============================================"
echo " Results: $PASS passed, $FAIL failed"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
exit 0
