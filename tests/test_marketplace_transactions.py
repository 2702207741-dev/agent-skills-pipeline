from __future__ import annotations

import argparse
import copy
import json
import random
import tempfile
import unittest
from pathlib import Path

from scripts import marketplace


class MarketplaceTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="our-skills-transaction-")
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name).resolve()
        self.platform = "codex"
        registry = marketplace.load_registry()
        self.entries = registry["skills"][:2]
        self.base = marketplace.target_base(self.home, self.platform)
        self.old_destination = marketplace.skill_destination(self.base, self.platform, self.entries[0])
        self.old_destination.mkdir(parents=True)
        (self.old_destination / "SKILL.md").write_text("---\nname: retained-before-failure\n---\n", encoding="utf-8")
        (self.old_destination / "old.txt").write_text("keep me\n", encoding="utf-8")
        self.new_destination = marketplace.skill_destination(self.base, self.platform, self.entries[1])

    def plan(self) -> dict:
        return marketplace.build_install_plan(self.home, self.platform, self.entries, "install")

    def test_failure_restores_every_touched_destination(self) -> None:
        plan = self.plan()
        marketplace.validate_install_plan(plan, "install", self.platform, self.home)

        with self.assertRaisesRegex(ValueError, "all touched destinations restored"):
            marketplace.apply_install_plan(plan, failure_after=1)

        self.assertEqual((self.old_destination / "old.txt").read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse(self.new_destination.exists())
        self.assertEqual(marketplace.verify_audit_chain(self.home), [])

    def test_failure_after_backup_restores_original_destination(self) -> None:
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "all touched destinations restored"):
            marketplace.apply_install_plan(plan, failure_after=1, failure_phase="backup")

        self.assertEqual((self.old_destination / "old.txt").read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse(self.new_destination.exists())

    def test_failure_during_staging_does_not_touch_destinations(self) -> None:
        plan = self.plan()
        with self.assertRaisesRegex(ValueError, "all touched destinations restored"):
            marketplace.apply_install_plan(plan, failure_after=1, failure_phase="stage")

        self.assertEqual((self.old_destination / "old.txt").read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse(self.new_destination.exists())

    def test_successful_transaction_can_roll_back_as_one_unit(self) -> None:
        plan = self.plan()
        marketplace.validate_install_plan(plan, "install", self.platform, self.home)
        marketplace.apply_install_plan(plan)
        self.assertFalse((self.old_destination / "old.txt").exists())
        self.assertTrue((self.new_destination / "SKILL.md").is_file())

        args = argparse.Namespace(
            transaction=plan["transaction_id"],
            skill=None,
            apply=True,
            dry_run=False,
        )
        self.assertEqual(marketplace.command_rollback_transaction(args, self.home, self.platform), 0)
        self.assertEqual((self.old_destination / "old.txt").read_text(encoding="utf-8"), "keep me\n")
        self.assertFalse(self.new_destination.exists())
        self.assertEqual(marketplace.verify_audit_chain(self.home), [])

    def test_tampered_audit_log_blocks_transaction_rollback(self) -> None:
        plan = self.plan()
        marketplace.apply_install_plan(plan)
        audit_log = marketplace.audit_log(self.home)
        events = audit_log.read_text(encoding="utf-8").splitlines()
        first = json.loads(events[0])
        first["action"] = "tampered"
        events[0] = json.dumps(first, sort_keys=True)
        audit_log.write_text("\n".join(events) + "\n", encoding="utf-8")

        args = argparse.Namespace(
            transaction=plan["transaction_id"],
            skill=None,
            apply=True,
            dry_run=False,
        )
        with self.assertRaisesRegex(ValueError, "audit log integrity failed"):
            marketplace.command_rollback_transaction(args, self.home, self.platform)

    def test_altered_plan_digest_is_rejected(self) -> None:
        plan = self.plan()
        altered = copy.deepcopy(plan)
        altered["operations"][0]["destination"] = str(self.home / "outside")
        with self.assertRaisesRegex(ValueError, "digest does not match"):
            marketplace.validate_install_plan(altered, "install", self.platform, self.home)

    def test_randomized_rehashed_plan_mutations_are_rejected(self) -> None:
        rng = random.Random(4103)
        fields = ["destination", "source", "source_digest", "destination_files_before", "rollback_mode"]
        for _ in range(20):
            altered = copy.deepcopy(self.plan())
            operation = rng.choice(altered["operations"])
            field = rng.choice(fields)
            if field in {"destination", "source"}:
                operation[field] = str(self.home / "mutated" / str(rng.randrange(10000)))
            elif field == "source_digest":
                operation[field] = f"{rng.getrandbits(256):064x}"
            elif field == "destination_files_before":
                operation[field] = {"unexpected.txt": f"{rng.getrandbits(256):064x}"}
            else:
                operation[field] = "remove_created_dest" if operation[field] == "restore_backup" else "restore_backup"
            altered["plan_sha256"] = marketplace.digest_value(
                {key: value for key, value in altered.items() if key != "plan_sha256"}
            )
            with self.assertRaises(ValueError):
                marketplace.validate_install_plan(altered, "install", self.platform, self.home)

    def test_symlink_destination_is_rejected(self) -> None:
        outside = self.home / "outside"
        outside.mkdir()
        marketplace.remove_destination(self.old_destination)
        try:
            self.old_destination.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"directory symlinks are unavailable: {exc}")
        with self.assertRaisesRegex(ValueError, "link or junction"):
            self.plan()

    def test_junction_compatibility_probe_is_link_like(self) -> None:
        class JunctionLike:
            def is_symlink(self) -> bool:
                return False

            def is_junction(self) -> bool:
                return True

        self.assertTrue(marketplace.path_is_link_like(JunctionLike()))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
