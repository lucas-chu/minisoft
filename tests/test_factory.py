"""Behavioral tests use disposable roots; no real app is claimed or completed."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import timedelta
import fcntl
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


MODULE = Path(__file__).resolve().parents[1] / "scripts/factory.py"
SPEC = importlib.util.spec_from_file_location("factory", MODULE)
factory = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(factory)


class FactoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        (self.root / "catalog").mkdir()
        (self.root / "runs").mkdir()
        ideas = []
        for i in range(1, 101):
            folder = f"apps/{i:03d}-mini-{i}"
            (self.root / folder).mkdir(parents=True)
            self.write(f"{folder}/IDEA.md", f"Idea {i}\n")
            ideas.append({"id": i, "name": f"Mini{i}", "folder": folder,
                          "description": f"Build idea {i}", "less": False})
        self.write_json("catalog/ideas.json", {"schema_version": 1, "order": factory.ORDER, "ideas": ideas})
        self.call("init")

    def write(self, path, text):
        destination = self.root / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(text)

    def write_json(self, path, data):
        self.write(path, json.dumps(data))

    def state(self):
        return factory.read_json(self.root / "state/progress.json")

    def call(self, *arguments, error=None):
        output, errors = io.StringIO(), io.StringIO()
        with redirect_stdout(output), redirect_stderr(errors):
            code = factory.main(["--root", str(self.root), *map(str, arguments)])
        if error is not None:
            self.assertEqual(code, 2, output.getvalue())
            self.assertIn(error, json.loads(errors.getvalue())["error"])
            return None
        self.assertEqual(code, 0, errors.getvalue())
        return json.loads(output.getvalue())

    def claim(self):
        return self.call("claim", "--owner", "test-thread")

    def build_receipt(self, idea_id, run_id):
        folder = f"apps/{idea_id:03d}-mini-{idea_id}"
        changed = [f"{folder}/README.md", f"{folder}/SPEC.md", f"{folder}/main.py"]
        for path in changed:
            self.write(path, f"Fixture source for {idea_id}: {path}\n")
        evidence = f"{folder}/evidence/verified.txt"
        self.write(evidence, "Fixture actual execution log, workflow, persistence, export, independent review.\n")
        data = {"schema_version": 1, "idea_id": idea_id, "run_id": run_id,
                "scope": "Fixture workflow only; no external integrations", "tier": "sandbox",
                "source_digest": factory.digest_files(self.root, changed), "changed_files": changed,
                "tests": [{"command": "python3 -m unittest", "passed": True, "evidence": evidence}],
                "core_workflow": {"exercised": True, "evidence": evidence},
                "persistence": {"applicable": True, "passed": True, "evidence": evidence},
                "export": {"applicable": False, "reason": "No export feature in this test fixture"},
                "independent_review": {"reviewer": "other-agent", "passed": True, "evidence": evidence},
                "website": {"required": False}, "limitations": []}
        path = f"runs/{idea_id:03d}-receipt.json"
        self.write_json(path, data)
        return path, data

    def test_init_is_idempotent_and_reads_do_not_mutate_progress(self):
        before = (self.root / "state/progress.json").read_bytes()
        self.assertEqual(self.call("status")["completed"], 0)
        self.assertEqual(self.call("next")["id"], 33)
        self.assertTrue(self.call("validate")["valid"])
        self.assertEqual(self.call("init")["remaining"], 100)
        self.assertEqual(before, (self.root / "state/progress.json").read_bytes())
        self.assertTrue(all(item["status"] == "planned" for item in self.state()["items"].values()))

    def test_claim_excludes_overlap_and_renew_requires_current_run(self):
        claim = self.claim()
        run = claim["lease"]["run_id"]
        self.assertEqual(claim["idea"]["id"], 33)
        self.call("claim", "--owner", "another-thread", error="active lease")
        self.call("claim", "--owner", "another-thread", "--recover-expired", "--confirm-workers-stopped",
                  "--note", "Attempt override", error="active lease")
        self.call("renew", "--run", "old-run", error="does not own")
        self.call("renew", "--run", run, "--ttl-minutes", "80")
        duration = factory.parse_time(self.state()["lease"]["expires_at"]) - factory.now()
        self.assertGreater(duration.total_seconds(), 79 * 60)
        self.call("heartbeat", "--run", run)

    def test_checkpoint_resumes_before_queue_and_rejects_old_run(self):
        run = self.claim()["lease"]["run_id"]
        self.call("checkpoint", "--run", run, "--note", "UI done; next exercise saved projects")
        self.assertIsNone(self.state()["lease"])
        self.assertIn("saved projects", self.call("next")["continuation"]["note"])
        resumed = self.claim()
        self.assertEqual(resumed["idea"]["id"], 33)
        self.assertNotEqual(resumed["lease"]["run_id"], run)
        self.call("checkpoint", "--run", run, "--note", "stale update", error="does not own")

    def test_blocked_item_is_retained_skipped_and_explicitly_unblocked(self):
        run = self.claim()["lease"]["run_id"]
        result = self.call("checkpoint", "--run", run, "--note", "Provider unavailable", "--blocked")
        self.assertEqual(result["blocked"], [33])
        self.assertEqual(self.call("next")["id"], 1)
        self.call("unblock", "33", "--note", "Provider recovered")
        self.assertEqual(self.call("next")["id"], 33)
        self.call("unblock", "1", "--note", "not blocked", error="not blocked")

    def test_expired_lease_requires_external_verification_attestation(self):
        previous = self.claim()["lease"]["run_id"]
        state = self.state()
        state["lease"]["acquired_at"] = factory.stamp(factory.now() - timedelta(minutes=60))
        state["lease"]["expires_at"] = factory.stamp(factory.now() - timedelta(minutes=5))
        self.write_json("state/progress.json", state)
        self.call("renew", "--run", previous, error="lease expired")
        self.call("claim", "--owner", "new", error="confirm-workers-stopped")
        self.call("claim", "--owner", "new", "--recover-expired", "--note", "Checked agents",
                  error="confirm-workers-stopped")
        recovered = self.call("claim", "--owner", "new", "--recover-expired", "--confirm-workers-stopped",
                              "--note", "Verified prior coordinator and all subagents stopped")
        self.assertEqual(recovered["idea"]["id"], 33)
        self.assertNotEqual(recovered["lease"]["run_id"], previous)
        self.call("checkpoint", "--run", previous, "--note", "stale", error="does not own")
        self.assertEqual(self.state()["items"]["33"]["history"][-2]["event"], "recover_expired")

    def test_completion_checks_identity_evidence_and_hash_then_counts_once(self):
        run = self.claim()["lease"]["run_id"]
        path, data = self.build_receipt(33, run)
        before = (self.root / "state/progress.json").read_bytes()
        for field, replacement, expected in (("idea_id", 1, "idea ID mismatch"),
                                             ("run_id", "other-run", "run ID mismatch"),
                                             ("source_digest", "bad", "source_digest"),
                                             ("tests", [], "test evidence")):
            broken = dict(data, **{field: replacement})
            self.write_json(path, broken)
            self.call("complete", "--run", run, "--receipt", path, error=expected)
            self.assertEqual(before, (self.root / "state/progress.json").read_bytes())
        self.write_json(path, data)
        completed = self.call("complete", "--run", run, "--receipt", path)
        self.assertEqual(completed["completed"], 1)
        self.assertEqual(completed["next"]["id"], 1)
        self.call("complete", "--run", run, "--receipt", path, error="does not own")
        self.assertEqual(self.call("status")["completed"], 1)
        self.write(data["changed_files"][-1], "Changed after verification\n")
        self.assertEqual(self.call("validate")["completed"], 1)
        frozen_path = self.state()["items"]["33"]["receipt"]
        self.assertEqual(frozen_path, f"runs/{run}/receipt.json")
        self.write_json(path, {"modified": "original receipt can be edited without changing accepted record"})
        self.assertEqual(self.call("validate")["completed"], 1)
        frozen = factory.read_json(self.root / frozen_path)
        evidence_path = next(iter(frozen["evidence_hashes"]))
        self.write(evidence_path, "Tampered frozen evidence")
        self.call("validate", error="frozen evidence integrity")

    def test_publication_review_and_applicability_are_explicit_gates(self):
        run = self.claim()["lease"]["run_id"]
        path, data = self.build_receipt(33, run)
        broken = dict(data, independent_review={**data["independent_review"], "reviewer": "test-thread"})
        self.write_json(path, broken)
        self.call("complete", "--run", run, "--receipt", path, error="independent")
        broken = dict(data, persistence={"applicable": True, "passed": False})
        self.write_json(path, broken)
        self.call("complete", "--run", run, "--receipt", path, error="persistence check")
        for field, value, expected in (("scope", "", "scope"), ("tier", "production-ready", "tier")):
            self.write_json(path, dict(data, **{field: value}))
            self.call("complete", "--run", run, "--receipt", path, error=expected)
        broken = dict(data, website={"required": True, "status": "building", "url": "https://example.com"})
        self.write_json(path, broken)
        self.call("complete", "--run", run, "--receipt", path, error="publication")
        data["website"] = {"required": True, "status": "succeeded", "url": "https://example.com",
                           "evidence": data["core_workflow"]["evidence"]}
        data["website"]["source_digest"] = "other-digest"
        self.write_json(path, data)
        self.call("complete", "--run", run, "--receipt", path, error="published source_digest")
        data["website"]["source_digest"] = data["source_digest"]
        self.write_json(path, data)
        self.assertEqual(self.call("complete", "--run", run, "--receipt", path)["completed"], 1)

    def test_completed_history_survives_shared_and_original_evidence_edits(self):
        run = self.claim()["lease"]["run_id"]
        path, data = self.build_receipt(33, run)
        shared = "packages/shared.py"
        self.write(shared, "Reviewed shared source\n")
        data["changed_files"].append(shared)
        data["source_digest"] = factory.digest_files(self.root, data["changed_files"])
        self.write_json(path, data)
        self.write(shared, "Changed before acceptance\n")
        self.call("complete", "--run", run, "--receipt", path, error="source_digest")
        self.write(shared, "Reviewed shared source\n")
        self.call("complete", "--run", run, "--receipt", path)
        frozen_path = self.state()["items"]["33"]["receipt"]
        before = (self.root / frozen_path).read_bytes()
        self.write(shared, "Updated for a later app\n")
        self.write(data["core_workflow"]["evidence"], "Later changed original evidence\n")
        self.write_json(path, {"overwritten": True})
        self.assertEqual(self.call("validate")["completed"], 1)
        self.assertEqual(self.call("next")["id"], 1)
        self.assertEqual(before, (self.root / frozen_path).read_bytes())

    def test_all_blocked_is_not_all_complete_and_unblock_resumes(self):
        state = self.state()
        for item in state["items"].values():
            item.update(status="blocked", run_id=str(factory.uuid.uuid4()), run_owner="old-thread",
                        continuation={"at": factory.stamp(), "note": "Needs provider recovery"})
        self.write_json("state/progress.json", state)
        self.assertIsNone(self.call("next"))
        result = self.claim()
        self.assertFalse(result["claimed"])
        self.assertFalse(result["all_complete"])
        self.assertEqual(result["remaining"], 100)
        self.assertEqual(len(result["blocked"]), 100)
        self.call("unblock", "33", "--note", "Provider restored")
        self.assertEqual(self.claim()["idea"]["id"], 33)

    def test_missing_empty_and_escaping_evidence_fail_without_mutation(self):
        run = self.claim()["lease"]["run_id"]
        path, data = self.build_receipt(33, run)
        evidence = data["core_workflow"]["evidence"]
        self.write(evidence, "")
        self.call("complete", "--run", run, "--receipt", path, error="empty file")
        self.write(evidence, "Restored fixture evidence")
        self.call("complete", "--run", run, "--receipt", "../outside.json", error="escapes")
        outside = self.root.parent / f"outside-{self.root.name}.txt"
        outside.write_text("Outside root")
        self.addCleanup(outside.unlink)
        (self.root / "runs/escape.txt").symlink_to(outside)
        data["core_workflow"]["evidence"] = "runs/escape.txt"
        self.write_json(path, data)
        self.call("complete", "--run", run, "--receipt", path, error="escapes")
        self.assertEqual(self.state()["items"]["33"]["status"], "in_progress")

    def test_all_complete_is_exactly_100_and_next_is_null(self):
        state = self.state()
        for idea_id in factory.ORDER:
            run = str(factory.uuid.uuid4())
            _, data = self.build_receipt(idea_id, run)
            item = state["items"][str(idea_id)]
            item.update(status="complete", run_id=run, run_owner="test-thread")
            path, digest = factory.freeze_receipt(self.root, item, data)
            item.update(receipt=path, receipt_digest=digest)
        self.write_json("state/progress.json", state)
        self.assertEqual(self.call("validate")["completed"], 100)
        self.assertIsNone(self.call("next"))
        result = self.claim()
        self.assertFalse(result["claimed"])
        self.assertTrue(result["all_complete"])
        del state["items"]["100"]
        self.write_json("state/progress.json", state)
        self.call("validate", error="exactly 1..100")

    def test_catalog_exact_ids_order_and_duplicate_folders(self):
        path = self.root / "catalog/ideas.json"
        data = factory.read_json(path)
        original = json.loads(json.dumps(data))
        data["ideas"][-1]["id"] = 1
        self.write_json("catalog/ideas.json", data)
        self.call("validate", error="exactly 1..100")
        data = json.loads(json.dumps(original))
        data["order"] = list(range(1, 101))
        self.write_json("catalog/ideas.json", data)
        self.call("validate", error="catalog order")
        data = json.loads(json.dumps(original))
        data["ideas"][-1]["folder"] = data["ideas"][0]["folder"]
        self.write_json("catalog/ideas.json", data)
        self.call("validate", error="duplicate app folder")

    def test_concurrent_process_claims_have_exactly_one_winner(self):
        processes = [subprocess.Popen([sys.executable, str(MODULE), "--root", str(self.root),
                                       "claim", "--owner", f"thread-{i}"],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                     for i in range(2)]
        results = [process.communicate(timeout=10) for process in processes]
        self.assertEqual(sorted(process.returncode for process in processes), [0, 2], results)
        self.assertEqual(self.call("status")["in_progress"], [33])
        self.assertEqual(len(self.state()["items"]["33"]["history"]), 1)

    def test_mutex_wait_is_bounded_and_atomic_failure_preserves_state(self):
        with (self.root / "state/.factory.lock").open("a+") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            with self.assertRaisesRegex(ValueError, "mutex is busy"):
                with factory.mutex(self.root, timeout=0.01):
                    self.fail("mutex must exclude competing lock holder")
        before = (self.root / "state/progress.json").read_bytes()
        with patch.object(factory.os, "replace", side_effect=OSError("simulated disk failure")):
            self.call("claim", "--owner", "test-thread", error="disk failure")
        self.assertEqual(before, (self.root / "state/progress.json").read_bytes())
        self.assertEqual(sorted(p.name for p in (self.root / "state").iterdir()), [".factory.lock", "progress.json"])


if __name__ == "__main__":
    unittest.main()
