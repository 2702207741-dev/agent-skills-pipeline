#!/usr/bin/env python3
"""Generate or check v2 platform index, graph report, and quality dashboard."""

from __future__ import annotations

import argparse
import sys

sys.dont_write_bytecode = True

from platform_reports import check_reports, write_reports


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if checked-in reports are missing or stale")
    args = parser.parse_args()

    try:
        if args.check:
            mismatches = check_reports()
            if mismatches:
                for mismatch in mismatches:
                    print(f"[FAIL] {mismatch}")
                return 1
            print("[OK] Platform reports are current")
            return 0
        paths = write_reports()
    except Exception as exc:
        print(f"[FAIL] {exc}")
        return 1

    for path in paths:
        print(f"[OK] Wrote {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
