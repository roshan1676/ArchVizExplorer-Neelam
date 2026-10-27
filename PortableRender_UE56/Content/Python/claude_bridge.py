"""
Claude file bridge for Unreal Editor.
Watches <Project>/Saved/ClaudeBridge/inbox for *.py files, runs each one on the
editor (game) thread, and writes the result to outbox/<name>.json.
Only runs inside the editor. Delete this file + init_unreal.py to remove it.
"""
import unreal, os, io, json, time, traceback, contextlib, builtins

ROOT   = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "ClaudeBridge")
INBOX  = os.path.join(ROOT, "inbox")
OUTBOX = os.path.join(ROOT, "outbox")
DONE   = os.path.join(ROOT, "done")
POLL_SECONDS = 0.5
HEARTBEAT_SECONDS = 3.0

for d in (INBOX, OUTBOX, DONE):
    os.makedirs(d, exist_ok=True)

_state = {"last_poll": 0.0, "last_beat": 0.0}

def _write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)
    os.replace(tmp, path)

def _run_one(name):
    src = os.path.join(INBOX, name)
    try:
        with open(src, "r", encoding="utf-8") as f:
            code = f.read()
    except Exception:
        return
    os.replace(src, os.path.join(DONE, name))
    out, err = io.StringIO(), io.StringIO()
    scope = {"unreal": unreal, "__name__": "__claude__", "result": None}
    ok, tb = True, None
    t0 = time.time()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            exec(compile(code, name, "exec"), scope)
    except Exception:
        ok, tb = False, traceback.format_exc()
    _write_json(os.path.join(OUTBOX, os.path.splitext(name)[0] + ".json"), {
        "ok": ok, "stdout": out.getvalue(), "stderr": err.getvalue(),
        "error": tb, "result": scope.get("result"), "seconds": round(time.time() - t0, 3),
    })
    unreal.log("ClaudeBridge: ran %s (%s)" % (name, "ok" if ok else "error"))

def _tick(delta):
    now = time.time()
    if now - _state["last_beat"] > HEARTBEAT_SECONDS:
        _state["last_beat"] = now
        try:
            _write_json(os.path.join(ROOT, "heartbeat.json"), {"time": now, "engine": unreal.SystemLibrary.get_engine_version()})
        except Exception:
            pass
    if now - _state["last_poll"] < POLL_SECONDS:
        return
    _state["last_poll"] = now
    try:
        names = sorted(n for n in os.listdir(INBOX) if n.endswith(".py"))
    except Exception:
        return
    for n in names:
        _run_one(n)

def start():
    old = getattr(builtins, "_claude_bridge_handle", None)
    if old is not None:
        try:
            unreal.unregister_slate_post_tick_callback(old)
        except Exception:
            pass
    builtins._claude_bridge_handle = unreal.register_slate_post_tick_callback(_tick)
    unreal.log("ClaudeBridge: watching %s" % INBOX)

start()
