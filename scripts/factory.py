#!/usr/bin/env python3
"""Small durable control plane for the 100-app factory (Python standard library).

Usage: python3 scripts/factory.py [--root ROOT] init|status|next|validate
       ... digest --files apps/033-mini-hackathon/README.md ...
       ... claim --owner THREAD_ID [--ttl-minutes 55]
       ... renew --run RUN_ID [--ttl-minutes 55]  # heartbeat is an alias
       ... checkpoint --run RUN_ID --note CONTINUATION [--blocked]
       ... complete --run RUN_ID --receipt runs/RECEIPT.json
       ... unblock IDEA_ID --note REASON
Expired recovery also requires --recover-expired --confirm-workers-stopped
--note REASON on claim, after externally verifying prior workers have stopped.

Receipt schema_version=1, idea_id, run_id, tests=[{command,passed:true,evidence}],
core_workflow={exercised:true,evidence}, persistence/export={applicable:true,
passed:true,evidence} or {applicable:false,reason}, independent_review={reviewer,
passed:true,evidence}, website={required:false} or {required:true,
status:"succeeded",url,evidence}, limitations=[strings], changed_files=[paths],
source_digest=<SHA256 from digest --files with those exact changed_files>.
Receipts also require scope=<implemented behavior> and tier=prototype|sandbox|
operational. Acceptance freezes the receipt and referenced evidence under
runs/RUN_ID/, hashes them, and validates those snapshots on subsequent reads.
Every evidence path must be a nonempty file inside ROOT. README.md and SPEC.md
must exist in the app folder. The gate validates assertions and files; the
coordinator must inspect actual execution, independent review, and publication.
"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
import fcntl
import hashlib
import json
from pathlib import Path
import os
import sys
import tempfile
import time
from urllib.parse import urlparse
import uuid


VERSION = 1
IDS = set(range(1, 101))
ORDER = [33] + [i for i in range(1, 101) if i != 33]
STATUSES = {"planned", "in_progress", "blocked", "complete"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def now():
    return datetime.now(timezone.utc)


def stamp(value=None):
    return (value or now()).isoformat()


def parse_time(value):
    parsed = datetime.fromisoformat(value)
    require(parsed.tzinfo is not None, "timestamps must include a timezone")
    return parsed


def inside(root, value):
    require(isinstance(value, str) and value.strip(), "path must be nonempty")
    path = (root / value).resolve()
    require(path.is_relative_to(root), f"path escapes factory root: {value}")
    return path


def nonempty_file(root, value):
    path = inside(root, value)
    require(path.is_file() and path.stat().st_size > 0, f"missing or empty file: {value}")
    return path


def digest_files(root, paths):
    require(isinstance(paths, list) and paths, "changed_files must be nonempty")
    normalized = [str(nonempty_file(root, path).relative_to(root)) for path in paths]
    require(len(normalized) == len(set(normalized)), "changed_files contain duplicate paths")
    digest = hashlib.sha256()
    for name in sorted(normalized):
        data = (root / name).read_bytes()
        digest.update(name.encode() + b"\0" + len(data).to_bytes(8, "big") + data)
    return digest.hexdigest()


def read_json(path):
    with path.open() as handle:
        return json.load(handle)


@contextmanager
def mutex(root, timeout=5):
    directory = inside(root, "state")
    directory.mkdir(parents=True, exist_ok=True)
    path = inside(root, "state/.factory.lock")
    with path.open("a+") as handle:
        deadline = time.monotonic() + timeout
        while True:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                require(time.monotonic() < deadline, "factory state mutex is busy; retry later")
                time.sleep(0.05)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def atomic_bytes(destination, content):
    temporary = None
    try:
        with tempfile.NamedTemporaryFile("wb", dir=destination.parent, delete=False) as handle:
            temporary = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        temporary = None
        descriptor = os.open(destination.parent, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    finally:
        if temporary:
            Path(temporary).unlink(missing_ok=True)


def write_state(root, state):
    state["updated_at"] = stamp()
    atomic_bytes(inside(root, "state/progress.json"), (json.dumps(state, indent=2, sort_keys=True) + "\n").encode())


def immutable_bytes(path, content):
    if path.exists():
        require(path.read_bytes() == content, "existing snapshot conflicts")
    else:
        atomic_bytes(path, content)


def catalog(root):
    data = read_json(inside(root, "catalog/ideas.json"))
    require(type(data.get("schema_version")) is int and data["schema_version"] == VERSION, "unsupported catalog schema")
    require(data.get("order") == ORDER and all(type(i) is int for i in data["order"]),
            "catalog order must be 33, 1..32, 34..100")
    ideas = data.get("ideas")
    require(isinstance(ideas, list) and len(ideas) == 100, "catalog must contain exactly 100 ideas")
    require(all(type(idea.get("id")) is int for idea in ideas), "idea IDs must be integers")
    require({idea["id"] for idea in ideas} == IDS, "catalog IDs must be exactly 1..100")
    folders = set()
    for idea in ideas:
        folder = inside(root, idea["folder"])
        require(folder.parent == root / "apps", "each app must have its own direct apps subfolder")
        require(folder not in folders, "duplicate app folder")
        folders.add(folder)
        require(isinstance(idea.get("name"), str) and idea["name"].strip(), "idea name is missing")
        nonempty_file(root, str(folder / "IDEA.md"))
    return {idea["id"]: idea for idea in ideas}


def initial_state():
    return {"schema_version": VERSION, "updated_at": stamp(), "lease": None,
            "items": {str(i): {"status": "planned", "run_id": None, "run_owner": None,
                               "continuation": None, "receipt": None, "history": []} for i in ORDER}}


def receipt(root, ideas, item, idea_id, value, historical=False):
    data = read_json(nonempty_file(root, value))
    if historical:
        require(hashlib.sha256(inside(root, value).read_bytes()).hexdigest() == item.get("receipt_digest"),
                "frozen receipt integrity mismatch")
    require(isinstance(data.get("scope"), str) and data["scope"].strip(), "receipt scope is required")
    require(data.get("tier") in {"prototype", "sandbox", "operational"}, "receipt tier is invalid")
    require(data.get("schema_version") == VERSION, "unsupported receipt schema")
    require(type(data.get("idea_id")) is int and data["idea_id"] == idea_id, "receipt idea ID mismatch")
    require(data.get("run_id") == item["run_id"], "receipt run ID mismatch")
    folder = ideas[idea_id]["folder"]
    if not historical:
        for name in ("README.md", "SPEC.md"):
            nonempty_file(root, f"{folder}/{name}")
    tests = data.get("tests")
    require(isinstance(tests, list) and tests, "receipt requires actual test evidence")
    for test in tests:
        require(isinstance(test.get("command"), str) and test["command"].strip(), "test command missing")
        require(test.get("passed") is True, "all receipt tests must pass")
        nonempty_file(root, test["evidence"])
    workflow = data.get("core_workflow", {})
    require(workflow.get("exercised") is True, "core workflow must be exercised")
    nonempty_file(root, workflow["evidence"])
    for name in ("persistence", "export"):
        check = data.get(name, {})
        require(type(check.get("applicable")) is bool, f"{name} applicability must be explicit")
        if check["applicable"]:
            require(check.get("passed") is True, f"{name} check must pass")
            nonempty_file(root, check["evidence"])
        else:
            require(isinstance(check.get("reason"), str) and check["reason"].strip(), f"{name} needs a reason")
    review = data.get("independent_review", {})
    require(review.get("passed") is True, "independent review must pass")
    require(isinstance(review.get("reviewer"), str) and review["reviewer"].strip()
            and review["reviewer"] != item["run_owner"], "reviewer must be independent of run owner")
    nonempty_file(root, review["evidence"])
    website = data.get("website", {})
    require(type(website.get("required")) is bool, "website requirement must be explicit")
    if website["required"]:
        url = urlparse(website.get("url", ""))
        require(website.get("status") == "succeeded" and url.scheme in {"http", "https"}
                and bool(url.netloc), "required website publication must have succeeded with a URL")
        nonempty_file(root, website["evidence"])
        if "source_digest" in website:
            require(website["source_digest"] == data.get("source_digest"), "published source_digest mismatch")
    limitations = data.get("limitations")
    require(isinstance(limitations, list) and all(isinstance(x, str) for x in limitations), "limitations must be a list")
    changed = data.get("changed_files")
    require(isinstance(changed, list) and changed, "changed_files must be nonempty")
    if not historical:
        require(data.get("source_digest") == digest_files(root, changed), "source_digest does not match current changed_files")
    require(any(inside(root, path).is_relative_to(root / folder) for path in changed), "receipt needs app changes")
    require(all((root / folder / name).resolve() in {inside(root, p) for p in changed}
                for name in ("README.md", "SPEC.md")), "changed_files must include README.md and SPEC.md")
    if not historical:
        for path in changed:
            nonempty_file(root, path)
    if historical:
        hashes = data.get("evidence_hashes", {})
        references = evidence_references(data)
        require(set(hashes) == {record["evidence"] for record in references}, "frozen evidence manifest mismatch")
        for path, digest in hashes.items():
            file = nonempty_file(root, path)
            require(file.is_relative_to(inside(root, value).parent / "evidence")
                    and hashlib.sha256(file.read_bytes()).hexdigest() == digest, "frozen evidence integrity mismatch")
    return data


def evidence_references(data):
    records = data["tests"] + [data["core_workflow"], data["independent_review"]]
    records += [data[name] for name in ("persistence", "export") if data[name]["applicable"]]
    return records + ([data["website"]] if data["website"]["required"] else [])


def freeze_receipt(root, item, data):
    frozen = json.loads(json.dumps(data))
    directory = inside(root, f"runs/{item['run_id']}")
    inside(root, str(directory / "evidence")).mkdir(parents=True, exist_ok=True)
    hashes, sources = {}, {}
    for record in evidence_references(frozen):
        original = nonempty_file(root, record["evidence"])
        content = original.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        destination = inside(root, str(directory / "evidence" / f"{digest}-{original.name}"))
        immutable_bytes(destination, content)
        path = str(destination.relative_to(root))
        sources[path] = str(original.relative_to(root))
        hashes[path] = digest
        record["evidence"] = path
    frozen.update(evidence_hashes=hashes, evidence_sources=sources)
    destination = inside(root, str(directory / "receipt.json"))
    content = (json.dumps(frozen, indent=2, sort_keys=True) + "\n").encode()
    immutable_bytes(destination, content)
    return str(destination.relative_to(root)), hashlib.sha256(content).hexdigest()


def validate_state(root, ideas, state):
    require(state.get("schema_version") == VERSION, "unsupported state schema")
    parse_time(state["updated_at"])
    items = state.get("items", {})
    require(set(items) == {str(i) for i in IDS}, "state IDs must be exactly 1..100")
    run_ids = []
    for key, item in items.items():
        require(item.get("status") in STATUSES, f"invalid status for {key}")
        require(isinstance(item.get("history"), list), f"history missing for {key}")
        if item["status"] == "planned":
            require(item.get("run_id") is None and item.get("receipt") is None, "planned item contains run/receipt")
        else:
            require(isinstance(item.get("run_id"), str) and item["run_id"], "unfinished/completed item needs run ID")
            require(isinstance(item.get("run_owner"), str) and item["run_owner"], "run owner missing")
            run_ids.append(item["run_id"])
        if item["status"] == "complete":
            receipt(root, ideas, item, int(key), item.get("receipt"), historical=True)
        else:
            require(item.get("receipt") is None, "unfinished item has completion receipt")
        continuation = item.get("continuation")
        if continuation is not None:
            require(isinstance(continuation.get("note"), str) and continuation["note"].strip(), "continuation note missing")
            parse_time(continuation["at"])
    require(len(run_ids) == len(set(run_ids)), "duplicate current run IDs")
    lease = state.get("lease")
    if lease is not None:
        require(type(lease.get("idea_id")) is int and lease["idea_id"] in IDS, "invalid lease idea ID")
        item = items[str(lease["idea_id"])]
        require(item["status"] == "in_progress" and lease.get("run_id") == item["run_id"]
                and lease.get("owner") == item["run_owner"], "lease and item disagree")
        require(parse_time(lease["expires_at"]) > parse_time(lease["acquired_at"]), "invalid lease duration")


def next_item(ideas, state):
    for status in ("in_progress", "planned"):
        for idea_id in ORDER:
            item = state["items"][str(idea_id)]
            if item["status"] == status:
                return {**ideas[idea_id], "status": status, "run_id": item["run_id"],
                        "continuation": item["continuation"]}
    return None


def status(ideas, state):
    grouped = {kind: [i for i in ORDER if state["items"][str(i)]["status"] == kind] for kind in STATUSES}
    return {"total": 100, "completed": len(grouped["complete"]), "remaining": 100 - len(grouped["complete"]),
            "all_complete": len(grouped["complete"]) == 100, "in_progress": grouped["in_progress"],
            "blocked": grouped["blocked"], "lease": state["lease"], "next": next_item(ideas, state)}


def event(item, kind, run_id, owner, note=None):
    item["history"].append({"at": stamp(), "event": kind, "run_id": run_id, "owner": owner, "note": note})


def active_lease(state, run_id):
    lease = state["lease"]
    require(lease is not None and lease["run_id"] == run_id, "run does not own the current lease")
    require(parse_time(lease["expires_at"]) > now(), "lease expired; verify workers stopped and recover before writing")
    return lease, state["items"][str(lease["idea_id"])]


def execute(args):
    root = Path(args.root).resolve()
    require(root.is_dir(), "factory root does not exist")
    with mutex(root):
        ideas = catalog(root)
        path = inside(root, "state/progress.json")
        if args.command == "init" and not path.exists():
            write_state(root, initial_state())
        require(path.is_file(), "factory state missing; run init first")
        state = read_json(path)
        validate_state(root, ideas, state)
        if args.command in {"init", "status"}:
            return status(ideas, state)
        if args.command == "next":
            return next_item(ideas, state)
        if args.command == "validate":
            return {"valid": True, "completed": status(ideas, state)["completed"]}
        if args.command == "digest":
            return {"source_digest": digest_files(root, args.files)}
        if args.command in {"claim", "renew", "heartbeat"}:
            require(0 < args.ttl_minutes <= 1440, "TTL must be between 0 and 1440 minutes")
        if args.command == "claim":
            require(args.owner.strip(), "owner must be a stable thread/turn identifier")
            lease = state["lease"]
            if lease is not None:
                require(parse_time(lease["expires_at"]) <= now(), "another run holds an active lease")
                require(args.recover_expired and args.confirm_workers_stopped and args.note and args.note.strip(),
                        "expired lease requires --recover-expired --confirm-workers-stopped --note after verification")
                previous = state["items"][str(lease["idea_id"]) ]
                event(previous, "recover_expired", lease["run_id"], args.owner, args.note)
                state["lease"] = None
            selected = next_item(ideas, state)
            if selected is None:
                return {"claimed": False, **status(ideas, state)}
            item = state["items"][str(selected["id"])]
            run_id = str(uuid.uuid4())
            item.update(status="in_progress", run_id=run_id, run_owner=args.owner)
            state["lease"] = {"idea_id": selected["id"], "run_id": run_id, "owner": args.owner,
                              "acquired_at": stamp(), "expires_at": stamp(now() + timedelta(minutes=args.ttl_minutes))}
            event(item, "claim", run_id, args.owner)
            result = {"claimed": True, "lease": state["lease"], "idea": next_item(ideas, state)}
        elif args.command in {"renew", "heartbeat"}:
            lease, item = active_lease(state, args.run)
            lease["expires_at"] = stamp(now() + timedelta(minutes=args.ttl_minutes))
            event(item, "renew", args.run, lease["owner"])
            result = {"lease": lease}
        elif args.command in {"checkpoint", "complete"}:
            lease, item = active_lease(state, args.run)
            if args.command == "checkpoint":
                require(args.note.strip(), "checkpoint requires a useful continuation note")
                item["status"] = "blocked" if args.blocked else "in_progress"
                item["continuation"] = {"at": stamp(), "note": args.note, "run_id": args.run}
                event(item, "blocked" if args.blocked else "checkpoint", args.run, lease["owner"], args.note)
            else:
                data = receipt(root, ideas, item, lease["idea_id"], args.receipt)
                frozen_path, digest = freeze_receipt(root, item, data)
                item.update(status="complete", receipt=frozen_path, receipt_digest=digest)
                event(item, "complete", args.run, lease["owner"])
            state["lease"] = None
            result = status(ideas, state)
        elif args.command == "unblock":
            require(args.idea_id in IDS and args.note.strip(), "unblock needs an idea ID and reason")
            item = state["items"][str(args.idea_id)]
            require(item["status"] == "blocked", "idea is not blocked")
            item["status"] = "in_progress"
            event(item, "unblock", item["run_id"], item["run_owner"], args.note)
            result = status(ideas, state)
        validate_state(root, ideas, state)
        write_state(root, state)
        return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--root", default=str(Path(__file__).resolve().parents[1]))
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("init", "status", "next", "validate", "digest", "claim", "renew", "heartbeat", "checkpoint", "complete", "unblock"):
        command = commands.add_parser(name)
        command.add_argument("--root", default=argparse.SUPPRESS)
        if name in {"claim", "renew", "heartbeat"}:
            command.add_argument("--ttl-minutes", type=float, default=55)
        if name == "claim":
            command.add_argument("--owner", required=True)
            command.add_argument("--recover-expired", action="store_true")
            command.add_argument("--confirm-workers-stopped", action="store_true")
            command.add_argument("--note")
        if name in {"renew", "heartbeat", "checkpoint", "complete"}:
            command.add_argument("--run", required=True)
        if name in {"checkpoint", "unblock"}:
            command.add_argument("--note", required=True)
        if name == "checkpoint":
            command.add_argument("--blocked", action="store_true")
        if name == "complete":
            command.add_argument("--receipt", required=True)
        if name == "unblock":
            command.add_argument("idea_id", type=int)
        if name == "digest":
            command.add_argument("--files", nargs="+", required=True)
    args = parser.parse_args(argv)
    try:
        print(json.dumps(execute(args), separators=(",", ":")))
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as error:
        print(json.dumps({"error": str(error)}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
