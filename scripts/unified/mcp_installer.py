#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
from string import Template

try:
    import yaml  # type: ignore
except Exception:
    yaml = None

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parents[1] / "unified" / "out"
MANIFEST = Path(__file__).resolve().parent / "manifest.yaml"


def load_manifest():
    if yaml is None:
        raise SystemExit("PyYAML not installed. Run: pip install pyyaml")
    with open(MANIFEST, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data.get("tools", {})


def expand_vars(s: str) -> str:
    return Template(s).safe_substitute(REPO_ROOT=str(ROOT))


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def write(path: Path, content: str):
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    return path


def gen_linux_systemd(name: str, cmd: str, cwd: str) -> Path:
    unit = f"""[Unit]
Description={name} (MCP stdio)
After=network.target

[Service]
Type=simple
WorkingDirectory={cwd}
Environment=PYTHONUNBUFFERED=1
ExecStart=/usr/bin/env bash -lc '{cmd}'
Restart=on-failure
RestartSec=2
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
"""
    out = OUT / name / "linux-systemd" / f"{name}.service"
    write(out, unit)
    return out


def gen_local_config(name: str, cmd: str, cwd: str) -> Path:
    cfg = {
        "mcpServers": {
            name: {
                "command": "bash",
                "args": ["-lc", cmd],
                "env": {"PYTHONUNBUFFERED": "1"},
                "cwd": cwd,
            }
        }
    }
    out = OUT / name / "local-config" / "clients.json"
    write(out, json.dumps(cfg, indent=2))
    return out


def gen_macos_launchd(name: str, cmd: str, cwd: str) -> Path:
    plist = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.lxd.{name}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string><string>-lc</string><string>{cmd}</string>
  </array>
  <key>WorkingDirectory</key><string>{cwd}</string>
  <key>EnvironmentVariables</key>
  <dict><key>PYTHONUNBUFFERED</key><string>1</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict>
</plist>
"""
    out = OUT / name / "macos-launchd" / f"com.lxd.{name}.plist"
    write(out, plist)
    return out


def gen_windows_task(name: str, cmd: str, cwd: str) -> Path:
    xml = f"""
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.4" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers/>
  <Principals><Principal id="Author"><RunLevel>HighestAvailable</RunLevel></Principal></Principals>
  <Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><AllowStartOnDemand>true</AllowStartOnDemand><RestartOnFailure><Count>3</Count><Interval>PT5M</Interval></RestartOnFailure></Settings>
  <Actions Context="Author">
    <Exec>
      <Command>powershell.exe</Command>
      <Arguments>-ExecutionPolicy Bypass -NoLogo -NoProfile -Command "cd '{cwd}'; $env:PYTHONUNBUFFERED='1'; {cmd}"</Arguments>
      <WorkingDirectory>{cwd}</WorkingDirectory>
    </Exec>
  </Actions>
</Task>
"""
    out = OUT / name / "windows-task" / f"{name}.xml"
    write(out, xml)
    return out


def gen_http_proxy_linux(name: str, cmd: str, cwd: str) -> Path:
    app_tpl = """import os, json, subprocess
from flask import Flask, request, jsonify

app = Flask(__name__)
MAX = int(os.environ.get('MAX_CONTENT_LENGTH', '1048576'))
app.config['MAX_CONTENT_LENGTH'] = MAX
TOKEN = os.environ.get('TOKEN','')
CMD = os.environ.get('SERVER_CMD', CMD_PLACE)
CWD = os.environ.get('SERVER_CWD', CWD_PLACE)

@app.post('/call')
def call():
    if TOKEN and request.headers.get('Authorization','') != ('Bearer ' + TOKEN):
        return jsonify({'error':'unauthorized'}), 401
    try:
        req = request.get_json(force=True, silent=False)
    except Exception:
        return jsonify({'error':'invalid json'}), 400
    p = subprocess.Popen(['bash','-lc', CMD], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, cwd=CWD)
    p.stdin.write(json.dumps(req)+'\n'); p.stdin.flush(); p.stdin.close()
    line = p.stdout.readline().strip()
    p.terminate()
    return app.response_class(line, mimetype='application/json')

@app.get('/healthz')
def h(): return jsonify({'status':'ok'})
"""
    app = app_tpl.replace('CMD_PLACE', repr(cmd)).replace('CWD_PLACE', repr(cwd))
    svc = f"""[Unit]
Description=MCP HTTP Proxy ({name})
After=network.target

[Service]
Environment=TOKEN=
Environment=SERVER_CMD={cmd}
Environment=SERVER_CWD={cwd}
WorkingDirectory={cwd}
ExecStart=/usr/bin/env gunicorn -b 127.0.0.1:8091 -w 2 http_proxy:app
Restart=on-failure
User=www-data
Group=www-data

[Install]
WantedBy=multi-user.target
"""
    req = "flask==3.0.0\ngunicorn==21.2.0\n"
    base = OUT / name / "http-proxy-linux"
    write(base / "http_proxy.py", app)
    write(base / "requirements.txt", req)
    write(base / f"mcp-{name}-proxy.service", svc)
    # Print nginx snippet
    nginx = (
        "server {\n    listen 80;\n    server_name <your-domain>;\n    location /mcp/" + name + "/ {\n        proxy_pass http://127.0.0.1:8091;\n        proxy_set_header Host $host;\n        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;\n        proxy_set_header X-Forwarded-Proto $scheme;\n    }\n}\n"
    )
    write(base / "nginx.conf.example", nginx)
    return base


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="List tools")
    ap.add_argument("--tool", help="Tool name from manifest")
    ap.add_argument("--target", choices=["linux-systemd","local-config","macos-launchd","windows-task","http-proxy-linux"], help="What to generate")
    args = ap.parse_args()

    tools = load_manifest()
    if args.list:
        print("Available tools:")
        for k in tools.keys():
            print(" -", k)
        return

    if not args.tool or not args.target:
        raise SystemExit("Provide --tool and --target or use --list")

    if args.tool not in tools:
        raise SystemExit(f"Unknown tool: {args.tool}")
    t = tools[args.tool]
    cmd = expand_vars(t["cmd"]).strip()
    cwd = expand_vars(t.get("cwd", str(ROOT)))

    if args.target == "linux-systemd":
        out = gen_linux_systemd(args.tool, cmd, cwd)
        print(f"Wrote {out}")
        print(f"Copy and enable:\n  sudo cp {out} /etc/systemd/system/\n  sudo systemctl daemon-reload\n  sudo systemctl enable --now {args.tool}.service")
    elif args.target == "local-config":
        out = gen_local_config(args.tool, cmd, cwd)
        print(f"Wrote {out}. Merge into your client's MCP config.")
    elif args.target == "macos-launchd":
        out = gen_macos_launchd(args.tool, cmd, cwd)
        print(f"Wrote {out}\nLoad with:\n  launchctl load -w ~/Library/LaunchAgents/{out.name}")
    elif args.target == "windows-task":
        out = gen_windows_task(args.tool, cmd, cwd)
        print(f"Wrote {out}\nImport with (as admin):\n  schtasks /Create /TN {args.tool} /XML {out}")
    elif args.target == "http-proxy-linux":
        base = gen_http_proxy_linux(args.tool, cmd, cwd)
        print(f"Wrote HTTP proxy under {base}\nInstall:\n  python3 -m venv {base}/.venv && source {base}/.venv/bin/activate && pip install -r {base}/requirements.txt\n  sudo cp {base}/mcp-{args.tool}-proxy.service /etc/systemd/system/\n  sudo systemctl daemon-reload && sudo systemctl enable --now mcp-{args.tool}-proxy.service\n  (nginx) see {base}/nginx.conf.example")


if __name__ == "__main__":
    main()
