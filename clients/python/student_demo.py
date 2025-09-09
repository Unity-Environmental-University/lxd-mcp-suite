#!/usr/bin/env python
"""
Run a demo student session against the student-guide-mcp stdio server.

Steps:
- initialize
- guide_handshake -> session_id
- set_intent
- add_excerpt -> excerpt_id
- extract_intent
- interrogate_support
- generate_improvement_plan
- export_session (prints brief summary)

Usage:
  python scripts/mcp_tools/student_demo.py \
    --server scripts/student-guide-mcp/mcp_server.py \
    --user-key dev123 --name Lydia [--excerpt "..."]
"""
import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict


def send_all(server: str, reqs: list[Dict[str, Any]]) -> list[Dict[str, Any]]:
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    p = subprocess.Popen([sys.executable, server], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
    try:
        for r in reqs:
            p.stdin.write(json.dumps(r) + "\n")
            p.stdin.flush()
        p.stdin.close()
        outs = [json.loads(line) for line in p.stdout.read().splitlines() if line.strip()]
        return outs
    finally:
        try:
            p.terminate()
        except Exception:
            pass
        p.wait(timeout=5)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--user-key", default="dev123")
    ap.add_argument("--name", default="Lydia")
    ap.add_argument("--excerpt", default=(
        "My paper argues that public libraries should expand digital access because they reduce information inequality. "
        "For example, rural students often lack broadband. Therefore, investing in hotspots improves equity."
    ))
    ap.add_argument("--timebox", type=int, default=60)
    args = ap.parse_args()

    req_id = 1
    def rid() -> int:
        nonlocal req_id
        req_id += 1
        return req_id

    reqs = []
    reqs.append({"jsonrpc": "2.0", "id": req_id, "method": "initialize"})

    # handshake
    reqs.append({
        "jsonrpc": "2.0", "id": rid(), "method": "tools/call",
        "params": {"name": "guide_handshake", "arguments": {"user_key": args.user_key, "name": args.name}}
    })

    # placeholder so we can get session_id after running
    outs = send_all(args.server, reqs)
    if not outs or len(outs) < 2:
        print("Server did not return expected responses", file=sys.stderr)
        return 1
    handshake = outs[-1]
    try:
        session = json.loads(handshake["result"]["content"][0]["text"]).get("session_id")
    except Exception as e:
        print(f"Failed to parse session_id: {e}\n{json.dumps(handshake, indent=2)}", file=sys.stderr)
        return 1
    print(f"Session: {session}")

    # Next phase requests executed sequentially for clarity
    def call_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        nonlocal req_id
        req_id += 1
        r = {"jsonrpc": "2.0", "id": req_id, "method": "tools/call", "params": {"name": name, "arguments": arguments}}
        outs = send_all(args.server, [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}, r])
        return outs[-1]

    # set_intent
    call_tool("set_intent", {"session_id": session, "purpose": "argue", "audience": "peers", "constraints": ["1200 words"], "rubric_keywords": ["thesis clarity", "evidence", "reasoning"]})

    # add_excerpt
    add_resp = call_tool("add_excerpt", {"session_id": session, "text": args.excerpt})
    try:
        excerpt_id = json.loads(add_resp["result"]["content"][0]["text"]).get("id")
    except Exception:
        excerpt_id = None
    print(f"Excerpt ID: {excerpt_id}")

    # extract + interrogate
    call_tool("extract_intent", {"session_id": session, "excerpt_id": excerpt_id})
    call_tool("interrogate_support", {"session_id": session, "excerpt_id": excerpt_id})

    # plan
    plan = call_tool("generate_improvement_plan", {"session_id": session, "timebox_minutes": args.timebox})
    try:
        plan_json = json.loads(plan["result"]["content"][0]["text"])  # noqa
        actions = plan_json.get("actions", [])
        print(f"Plan actions: {len(actions)}")
        for i, a in enumerate(actions[:5], 1):
            print(f"  {i}. {a.get('title','(no title)')}")
    except Exception:
        print("Generated plan (raw):")
        print(plan)

    # export session summary
    export = call_tool("export_session", {"session_id": session})
    try:
        snap = json.loads(export["result"]["content"][0]["text"])  # noqa
        print(f"Snapshot keys: {list(snap.keys())[:6]}")
    except Exception:
        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

