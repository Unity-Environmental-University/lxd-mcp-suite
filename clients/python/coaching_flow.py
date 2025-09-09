#!/usr/bin/env python
import argparse
import json
import os
import subprocess
import sys


def call(server, method, params=None, id_=1):
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    p = subprocess.Popen([sys.executable, server], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, env=env)
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}, {"jsonrpc": "2.0", "id": id_, "method": method, "params": params or {}}]
    for r in reqs:
        p.stdin.write(json.dumps(r) + "\n"); p.stdin.flush()
    p.stdin.close()
    lines = [json.loads(l) for l in p.stdout.read().splitlines() if l.strip()]
    try:
        p.terminate()
    except Exception:
        pass
    p.wait(timeout=5)
    return lines[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--user-key", default="dev123")
    ap.add_argument("--name", default="Lydia")
    args = ap.parse_args()

    hs = call(args.server, "tools/call", {"name": "guide_handshake", "arguments": {"user_key": args.user_key, "name": args.name}}, id_=2)
    session = json.loads(hs["result"]["content"][0]["text"])['session_id']
    ui = call(args.server, "tools/call", {"name": "start_coaching_flow", "arguments": {"session_id": session}}, id_=3)
    payload = json.loads(ui["result"]["content"][0]["text"])  # contains ui
    print(json.dumps({"session_id": session, "ui": payload.get("ui")}, indent=2))

if __name__ == "__main__":
    main()

