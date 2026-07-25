#!/usr/bin/env python3
"""Persistent-connection helper for playing a CircleMUD/tbaMUD server.

Every Bash tool call is a brand-new process. If you `telnet localhost 4000`
fresh for each command, you get a new, unauthenticated connection every time
-- you'd have to log in again (or the MUD treats you as a new guest) and you
lose whatever state (position, combat round, menus) the previous connection
was in. MUDs are fundamentally stateful sockets, not stateless requests.

This script solves that by splitting the job in two:

  - A small background daemon (`_daemon`, not meant to be called directly)
    that opens exactly one long-lived TCP socket to the MUD, logs in once,
    and keeps a reader thread draining it forever.
  - A CLI client (`connect` / `send` / `read` / `status` / `disconnect`)
    that talks to that daemon over a Unix domain socket. Each CLI invocation
    is a fresh process, but they all share the one underlying MUD connection
    held open by the daemon, so your character stays logged in and in the
    same place between commands.

Typical flow:

    python3 mud_session.py connect
    python3 mud_session.py send "look"
    python3 mud_session.py send "north"
    python3 mud_session.py send "say hello"
    python3 mud_session.py disconnect

Run multiple independent characters/sessions at once with --name.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
import threading
import time

IAC, DONT, DO, WONT, WILL, SB, SE = 255, 254, 253, 252, 251, 250, 240

PROMPT_SENTINEL = "> "


def strip_iac(data: bytes) -> bytes:
    """Discard telnet IAC negotiation sequences; we don't honor them, just consume them."""
    out = bytearray()
    i, n = 0, len(data)
    while i < n:
        b = data[i]
        if b == IAC:
            nxt = data[i + 1] if i + 1 < n else None
            if nxt is None:
                break
            if nxt == IAC:
                out.append(IAC)
                i += 2
            elif nxt in (WILL, WONT, DO, DONT):
                i += 3
            elif nxt == SB:
                j = i + 2
                while j + 1 < n and not (data[j] == IAC and data[j + 1] == SE):
                    j += 1
                i = j + 2
            else:
                i += 2
        else:
            out.append(b)
            i += 1
    return bytes(out)


class MudLink:
    """One long-lived telnet connection, with a background reader thread."""

    def __init__(self, host: str, port: int, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock: socket.socket | None = None
        self.buf = ""
        self.lock = threading.Condition()
        self.last_recv: float | None = None
        self.closed = True

    def open(self) -> None:
        self.sock = socket.create_connection((self.host, self.port), timeout=10)
        self.closed = False
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self) -> None:
        try:
            while True:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                text = strip_iac(chunk).decode("utf-8", "replace")
                if text:
                    with self.lock:
                        self.buf += text
                        self.last_recv = time.monotonic()
                        self.lock.notify_all()
        except OSError:
            pass
        finally:
            with self.lock:
                self.closed = True
                self.lock.notify_all()

    def send_line(self, text: str) -> None:
        if self.closed:
            raise ConnectionError("mud connection is closed")
        self.sock.sendall(text.encode("utf-8", "replace") + b"\r\n")

    def buffered_len(self) -> int:
        """Current buffer length, for snapshotting a search start position before sending
        a new command -- see the `search_from` param on read_until/read_until_prompt."""
        with self.lock:
            return len(self.buf)

    def read_until(self, pattern: "re.Pattern[str] | str", timeout: float | None = None,
                   search_from: int = 0) -> str:
        """Block until `pattern` appears, then return everything up to and including it.

        `search_from` skips matches inside content that was already sitting in the buffer
        before this call started (e.g. async chatter -- an NPC arriving -- that happened to
        end with its own copy of the prompt sentinel). Without it, a stale, already-reported
        prompt can satisfy the match instantly and this returns leftover text instead of the
        response to whatever was just sent."""
        regex = pattern if isinstance(pattern, re.Pattern) else re.compile(re.escape(pattern))
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        with self.lock:
            while True:
                start = min(search_from, len(self.buf))
                m = regex.search(self.buf, start)
                if m:
                    cut = m.end()
                    out, self.buf = self.buf[:cut], self.buf[cut:]
                    return out
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise TimeoutError(f"read_until {pattern!r} timed out")
                if self.closed:
                    raise ConnectionError("socket closed while waiting")
                self.lock.wait(remaining)

    def read_until_quiet(self, quiet: float = 0.8, timeout: float | None = None) -> str:
        """Block until `quiet` seconds pass with no new bytes, then return everything buffered."""
        deadline = time.monotonic() + (timeout if timeout is not None else self.timeout)
        with self.lock:
            while True:
                now = time.monotonic()
                remaining_total = deadline - now
                if remaining_total <= 0:
                    break
                if self.last_recv and self.buf and (now - self.last_recv) >= quiet:
                    break
                if self.last_recv and self.buf:
                    wait_for = min(quiet - (now - self.last_recv), remaining_total)
                else:
                    wait_for = remaining_total
                if wait_for <= 0:
                    break
                self.lock.wait(wait_for)
            out, self.buf = self.buf, ""
            return out

    def read_until_prompt(self, timeout: float | None = None, search_from: int = 0) -> str:
        """CircleMUD ends every command's response with a "> " prompt -- waiting for that
        sentinel is faster and more deterministic than a silence window. Falls back to a
        quiet-drain if the prompt never shows up (e.g. mid-combat spam, or after `quit`).
        See read_until for why `search_from` matters here."""
        try:
            return self.read_until(PROMPT_SENTINEL, timeout=timeout, search_from=search_from)
        except TimeoutError:
            return self.read_until_quiet(quiet=0.8, timeout=1.0)

    def drain(self) -> str:
        with self.lock:
            out, self.buf = self.buf, ""
            return out

    def login(self, username: str, password: str) -> None:
        self.read_until(re.compile(r"By what name.*\?", re.I | re.S))
        self.send_line(username)
        self.read_until(re.compile(r"Password", re.I))
        self.send_line(password)
        out = self.read_until(re.compile(r"Welcome|Reconnecting|Wrong password", re.I))
        if re.search("Wrong password", out, re.I):
            raise RuntimeError("wrong password")
        if re.search("Welcome", out, re.I):
            self.send_line("")   # enter for main menu
            self.send_line("1")  # enter the game
        # else "Reconnecting": already in-world, no menu to walk through


def runtime_paths(name: str) -> dict[str, str]:
    base = os.path.join(tempfile.gettempdir(), "mud-skill")
    os.makedirs(base, exist_ok=True)
    return {
        "sock": os.path.join(base, f"{name}.sock"),
        "pid": os.path.join(base, f"{name}.pid"),
        "log": os.path.join(base, f"{name}.log"),
    }


def is_running(name: str) -> bool:
    paths = runtime_paths(name)
    if not os.path.exists(paths["pid"]):
        return False
    try:
        pid = int(open(paths["pid"]).read().strip())
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def client_request(name: str, payload: dict, connect_timeout: float = 5) -> dict | None:
    """Send one JSON request to the named daemon's Unix socket and return its JSON reply.
    Returns None if no daemon is listening (never started, crashed, or already disconnected)."""
    paths = runtime_paths(name)
    if not os.path.exists(paths["sock"]):
        return None
    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    s.settimeout(connect_timeout)
    try:
        s.connect(paths["sock"])
    except OSError:
        return None
    s.sendall(json.dumps(payload).encode("utf-8"))
    s.shutdown(socket.SHUT_WR)
    s.settimeout(payload.get("timeout", 10) + 5)
    chunks = []
    try:
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            chunks.append(chunk)
    finally:
        s.close()
    data = b"".join(chunks).decode("utf-8", "replace").strip()
    return json.loads(data) if data else None


# ---------- daemon ----------

def daemon_main(args: argparse.Namespace) -> None:
    paths = runtime_paths(args.name)
    if os.path.exists(paths["sock"]):
        os.remove(paths["sock"])

    link = MudLink(args.host, args.port)
    link.open()
    try:
        link.login(args.user, args.password)
    except Exception as e:
        with open(paths["log"], "a") as f:
            f.write(f"LOGIN FAILED: {e}\n")
        sys.exit(1)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(paths["sock"])
    server.listen(5)
    with open(paths["pid"], "w") as f:
        f.write(str(os.getpid()))

    try:
        while True:
            conn, _ = server.accept()
            try:
                data = conn.recv(65536)
                if not data:
                    continue
                req = json.loads(data.decode("utf-8", "replace"))
                action = req.get("action")
                if action == "send":
                    start = link.buffered_len()
                    link.send_line(req["text"])
                    if req.get("mode") == "quiet":
                        out = link.read_until_quiet(quiet=req.get("quiet", 0.8), timeout=req.get("timeout", 10))
                    else:
                        out = link.read_until_prompt(timeout=req.get("timeout", 10), search_from=start)
                    resp = {"ok": True, "output": out, "connected": not link.closed}
                elif action == "read":
                    out = link.read_until_quiet(quiet=req.get("quiet", 0.5), timeout=req.get("timeout", 3))
                    resp = {"ok": True, "output": out, "connected": not link.closed}
                elif action == "status":
                    resp = {"ok": True, "connected": not link.closed, "buffered_chars": len(link.buf)}
                elif action == "shutdown":
                    out = ""
                    try:
                        link.send_line("quit")
                        time.sleep(0.5)
                        out = link.drain()
                    except Exception:
                        pass
                    conn.sendall((json.dumps({"ok": True, "output": out}) + "\n").encode())
                    conn.close()
                    return
                else:
                    resp = {"ok": False, "error": f"unknown action {action!r}"}
                conn.sendall((json.dumps(resp) + "\n").encode())
            except Exception as e:
                try:
                    conn.sendall((json.dumps({"ok": False, "error": str(e)}) + "\n").encode())
                except OSError:
                    pass
            finally:
                conn.close()
    finally:
        for key in ("sock", "pid"):
            try:
                os.remove(paths[key])
            except OSError:
                pass


# ---------- CLI ----------

def cmd_connect(args: argparse.Namespace) -> None:
    paths = runtime_paths(args.name)
    if is_running(args.name):
        resp = client_request(args.name, {"action": "status"}, connect_timeout=3)
        if resp and resp.get("connected"):
            print(f"Session {args.name!r} is already connected.")
            return

    log = open(paths["log"], "a")
    proc = subprocess.Popen(
        [sys.executable, os.path.abspath(__file__), "_daemon",
         "--host", args.host, "--port", str(args.port),
         "--user", args.user, "--password", args.password,
         "--name", args.name],
        stdin=subprocess.DEVNULL, stdout=log, stderr=log,
        start_new_session=True,
    )

    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            print(f"Daemon exited early (code {proc.returncode}). Log ({paths['log']}):")
            try:
                print(open(paths["log"]).read()[-2000:])
            except OSError:
                pass
            sys.exit(1)
        if os.path.exists(paths["sock"]):
            resp = client_request(args.name, {"action": "read", "quiet": 0.8, "timeout": 5})
            if resp is not None:
                print(f"Connected as session {args.name!r} ({args.user}@{args.host}:{args.port}).\n")
                print(resp.get("output", ""))
                return
        time.sleep(0.3)
    print("Timed out waiting for the MUD to respond. Check the log:", paths["log"])
    sys.exit(1)


def cmd_send(args: argparse.Namespace) -> None:
    resp = client_request(args.name, {
        "action": "send", "text": args.text, "mode": args.mode,
        "quiet": args.quiet, "timeout": args.timeout,
    })
    if resp is None:
        print(f"No running session named {args.name!r}. Run `connect` first.")
        sys.exit(1)
    if not resp.get("ok"):
        print("Error:", resp.get("error"))
        sys.exit(1)
    print(resp.get("output", ""), end="")


def cmd_read(args: argparse.Namespace) -> None:
    resp = client_request(args.name, {"action": "read", "quiet": args.quiet, "timeout": args.timeout})
    if resp is None:
        print(f"No running session named {args.name!r}.")
        sys.exit(1)
    print(resp.get("output", ""), end="")


def cmd_status(args: argparse.Namespace) -> None:
    resp = client_request(args.name, {"action": "status"}, connect_timeout=3)
    if resp is None:
        print(f"session {args.name!r}: not running")
        return
    print(f"session {args.name!r}: connected={resp.get('connected')} buffered_chars={resp.get('buffered_chars')}")


def cmd_disconnect(args: argparse.Namespace) -> None:
    resp = client_request(args.name, {"action": "shutdown"}, connect_timeout=5)
    if resp is None:
        print(f"session {args.name!r}: not running")
        return
    print(resp.get("output", ""))
    print(f"Disconnected session {args.name!r}.")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="action", required=True)

    def add_name(sp):
        sp.add_argument("--name", default="default", help="session name, for running multiple characters at once")

    connect = sub.add_parser("connect", help="start (or reuse) the background daemon and log in")
    connect.add_argument("--host", default=os.environ.get("MUD_HOST", "localhost"))
    connect.add_argument("--port", type=int, default=int(os.environ.get("MUD_PORT", "4000")))
    connect.add_argument("--user", default=os.environ.get("MUD_NAME", "dummy"))
    connect.add_argument("--password", default=os.environ.get("MUD_PASSWORD", "helloworld"))
    add_name(connect)
    connect.set_defaults(func=cmd_connect)

    send = sub.add_parser("send", help="send one command line and return the MUD's response")
    send.add_argument("text", help='the raw command to send, e.g. "look" or "say hello"')
    send.add_argument("--mode", choices=["prompt", "quiet"], default="prompt",
                       help="prompt (default): wait for the '> ' prompt; "
                            "quiet: wait for a silence window instead (useful right after `quit`)")
    send.add_argument("--quiet", type=float, default=0.8, help="seconds of silence to wait for in quiet mode")
    send.add_argument("--timeout", type=float, default=10, help="max seconds to wait for a response")
    add_name(send)
    send.set_defaults(func=cmd_send)

    read = sub.add_parser("read", help="drain any pending output without sending a command (e.g. async chatter)")
    read.add_argument("--quiet", type=float, default=0.5)
    read.add_argument("--timeout", type=float, default=3)
    add_name(read)
    read.set_defaults(func=cmd_read)

    status = sub.add_parser("status", help="check whether a session's daemon is alive and connected")
    add_name(status)
    status.set_defaults(func=cmd_status)

    disconnect = sub.add_parser("disconnect", help="send `quit` so the character saves properly, then stop the daemon")
    add_name(disconnect)
    disconnect.set_defaults(func=cmd_disconnect)

    daemon = sub.add_parser("_daemon", help=argparse.SUPPRESS)
    daemon.add_argument("--host", required=True)
    daemon.add_argument("--port", type=int, required=True)
    daemon.add_argument("--user", required=True)
    daemon.add_argument("--password", required=True)
    daemon.add_argument("--name", required=True)
    daemon.set_defaults(func=daemon_main)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
