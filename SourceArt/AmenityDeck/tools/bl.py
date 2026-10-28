"""Run Python inside the live Blender session (Blender Lab "MCP" add-on, port 9876).

Usage:
    python tools/bl.py script.py      # run a file
    python tools/bl.py -c "code"      # run inline code
    echo "code" | python tools/bl.py  # run stdin

Set `result = ...` in the code to get a JSON value back; print() output is returned too.
"""
import json
import socket
import sys

HOST, PORT = "127.0.0.1", 9876


def run(code, timeout=600):
    with socket.create_connection((HOST, PORT), timeout=timeout) as s:
        s.sendall((json.dumps({"type": "execute", "code": code, "strict_json": False}) + "\0").encode())
        buf = b""
        while b"\0" not in buf:
            chunk = s.recv(1 << 16)
            if not chunk:
                break
            buf += chunk
    return json.loads(buf.split(b"\0", 1)[0])


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["-c"]:
        code = args[1]
    elif args:
        code = open(args[0], encoding="utf-8").read()
    else:
        code = sys.stdin.read()
    resp = run(code)
    for key in ("stdout", "stderr"):
        if resp.get(key):
            sys.stdout.write(resp.pop(key))
    print(json.dumps(resp, indent=1, default=str))
    sys.exit(0 if resp.get("status") == "ok" else 1)
