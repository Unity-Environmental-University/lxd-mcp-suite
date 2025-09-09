#!/usr/bin/env python
"""
Minimal MCP stdio caller for testing.

Usage examples:
  python scripts/mcp_tools/mcp_call.py --server scripts/story-goal-mcp/mcp_server.py --init-only
  python scripts/mcp_tools/mcp_call.py --server scripts/story-goal-mcp/mcp_server.py --payload '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
  python scripts/mcp_tools/mcp_call.py --server <path> --tool guide_handshake --args '{"user_key":"dev123","name":"Lydia"}'

Prints the last line of server output (full JSON-RPC response).
"""
import argparse
import json
import os
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True, help="Path to MCP server entry (e.g., mcp_server.py)")
    ap.add_argument("--init-only", action="store_true", help="Send only initialize request")
    ap.add_argument("--payload", help="Raw JSON-RPC object to send after initialize")
    ap.add_argument("--payload-file", help="Path to file containing JSON-RPC object")
    ap.add_argument("--tool", help="If set, send tools/call with this tool name")
    ap.add_argument("--args", default="{}", help="JSON object for tool arguments")
    args = ap.parse_args()

    if sum(bool(x) for x in [args.payload, args.payload_file, args.tool]) > 1:
        print("Use only one of --payload, --payload-file, or --tool", file=sys.stderr)
        return 2

    # Build request sequence: initialize + (optional payload)
    reqs = [{"jsonrpc": "2.0", "id": 1, "method": "initialize"}]

    if args.payload_file:
        try:
            with open(args.payload_file, "r", encoding="utf-8") as f:
                reqs.append(json.load(f))
        except Exception as e:
            print(f"Failed to read --payload-file: {e}", file=sys.stderr)
            return 2
    elif args.payload:
        try:
            reqs.append(json.loads(args.payload))
        except json.JSONDecodeError as e:
            print(f"Invalid --payload JSON: {e}", file=sys.stderr)
            return 2
    elif args.tool:
        try:
            tool_args = json.loads(args.args)
        except json.JSONDecodeError as e:
            print(f"Invalid --args JSON: {e}", file=sys.stderr)
            return 2
        reqs.append({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": args.tool, "arguments": tool_args},
        })
    else:
        if not args.init_only:
            print("No --payload or --tool provided; did you mean --init-only?", file=sys.stderr)
            return 2

    env = os.environ.copy()
    # Force unbuffered output for cleaner line handling
    env.setdefault("PYTHONUNBUFFERED", "1")

    proc = subprocess.Popen(
        [sys.executable, args.server],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env=env,
    )

    try:
        for r in reqs:
            line = json.dumps(r) + "\n"
            proc.stdin.write(line)
            proc.stdin.flush()
        proc.stdin.close()

        # Collect all stdout lines; print last line
        outs = proc.stdout.read().strip().splitlines()
        if outs:
            print(outs[-1])
        else:
            # Surface stderr to aid debugging
            err = proc.stderr.read()
            if err:
                print(err.strip(), file=sys.stderr)
                return 1
    finally:
        try:
            proc.terminate()
        except Exception:
            pass
        proc.wait(timeout=5)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
