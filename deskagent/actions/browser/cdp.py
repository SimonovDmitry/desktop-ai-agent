from __future__ import annotations

import base64
import hashlib
import json
import os
import socket
import ssl
import struct
import threading
import time
from contextlib import closing
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlparse
from urllib.request import Request, urlopen

from deskagent.actions.browser.base import BrowserBackend
from deskagent.actions.browser.models import (
    BackendKind,
    BrowserConnectionError,
    BrowserTab,
    BrowserTargetError,
    BrowserTimeoutError,
)


class CDPWebSocket:
    """Small synchronous RFC 6455 client tailored for local DevTools sockets."""

    def __init__(self, url: str, timeout: float = 10.0):
        self.url = url
        self.timeout = timeout
        self._socket = None
        self._lock = threading.RLock()
        self._next_id = 0

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    def connect(self):
        parsed = urlparse(self.url)
        if parsed.scheme not in {"ws", "wss"} or not parsed.hostname:
            raise BrowserConnectionError(f"Invalid DevTools WebSocket URL: {self.url}")
        port = parsed.port or (443 if parsed.scheme == "wss" else 80)
        sock = socket.create_connection((parsed.hostname, port), timeout=self.timeout)
        if parsed.scheme == "wss":
            sock = ssl.create_default_context().wrap_socket(sock, server_hostname=parsed.hostname)
        sock.settimeout(self.timeout)
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        path = parsed.path or "/"
        if parsed.query:
            path += "?" + parsed.query
        host = parsed.hostname if parsed.port is None else f"{parsed.hostname}:{parsed.port}"
        request = (
            f"GET {path} HTTP/1.1\r\nHost: {host}\r\nUpgrade: websocket\r\n"
            f"Connection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
        )
        sock.sendall(request.encode("ascii"))
        response = self._read_headers(sock)
        first_line = response.split(b"\r\n", 1)[0]
        if b" 101 " not in first_line:
            sock.close()
            raise BrowserConnectionError(f"DevTools WebSocket handshake failed: {first_line.decode(errors='replace')}")
        expected = base64.b64encode(
            hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode("ascii")).digest()
        ).decode("ascii")
        headers = self._parse_headers(response)
        if headers.get("sec-websocket-accept") != expected:
            sock.close()
            raise BrowserConnectionError("DevTools WebSocket returned an invalid handshake")
        self._socket = sock

    def command(self, method: str, params: dict | None = None) -> dict:
        with self._lock:
            if self._socket is None:
                self.connect()
            self._next_id += 1
            command_id = self._next_id
            payload = json.dumps({"id": command_id, "method": method, "params": params or {}}).encode("utf-8")
            self._send_frame(payload)
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                message = self._receive_message()
                if message.get("id") != command_id:
                    continue
                if "error" in message:
                    error = message["error"]
                    raise BrowserConnectionError(
                        f"CDP {method} failed ({error.get('code')}): {error.get('message', 'unknown error')}"
                    )
                return message.get("result", {})
            raise BrowserTimeoutError(f"Timed out waiting for CDP command: {method}")

    def close(self):
        sock, self._socket = self._socket, None
        if sock is not None:
            try:
                self._send_frame(b"", opcode=0x8, sock=sock)
            except OSError:
                pass
            sock.close()

    @staticmethod
    def _read_headers(sock):
        data = bytearray()
        while b"\r\n\r\n" not in data:
            chunk = sock.recv(4096)
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > 65536:
                raise BrowserConnectionError("Oversized DevTools handshake")
        return bytes(data)

    @staticmethod
    def _parse_headers(response):
        result = {}
        for line in response.split(b"\r\n")[1:]:
            if b":" in line:
                name, value = line.split(b":", 1)
                result[name.decode("ascii").lower()] = value.decode("ascii").strip()
        return result

    def _send_frame(self, payload: bytes, opcode=0x1, sock=None):
        sock = sock or self._socket
        mask = os.urandom(4)
        length = len(payload)
        head = bytearray([0x80 | opcode])
        if length < 126:
            head.append(0x80 | length)
        elif length < 65536:
            head.append(0x80 | 126)
            head.extend(struct.pack("!H", length))
        else:
            head.append(0x80 | 127)
            head.extend(struct.pack("!Q", length))
        head.extend(mask)
        head.extend(byte ^ mask[index % 4] for index, byte in enumerate(payload))
        sock.sendall(head)

    def _receive_message(self):
        fragments = bytearray()
        while True:
            first, second = self._recv_exact(2)
            final, opcode, masked = bool(first & 0x80), first & 0x0F, bool(second & 0x80)
            length = second & 0x7F
            if length == 126:
                length = struct.unpack("!H", self._recv_exact(2))[0]
            elif length == 127:
                length = struct.unpack("!Q", self._recv_exact(8))[0]
            mask = self._recv_exact(4) if masked else None
            payload = bytearray(self._recv_exact(length))
            if mask:
                payload = bytearray(byte ^ mask[index % 4] for index, byte in enumerate(payload))
            if opcode == 0x8:
                raise BrowserConnectionError("DevTools WebSocket closed")
            if opcode == 0x9:
                self._send_frame(bytes(payload), opcode=0xA)
                continue
            if opcode in {0x0, 0x1}:
                fragments.extend(payload)
                if final:
                    try:
                        return json.loads(fragments.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise BrowserConnectionError("Invalid JSON from DevTools WebSocket") from exc

    def _recv_exact(self, size):
        data = bytearray()
        while len(data) < size:
            try:
                chunk = self._socket.recv(size - len(data))
            except socket.timeout as exc:
                raise BrowserTimeoutError("Timed out reading from DevTools WebSocket") from exc
            if not chunk:
                raise BrowserConnectionError("DevTools WebSocket disconnected")
            data.extend(chunk)
        return bytes(data)


class CDPBackend(BrowserBackend):
    def __init__(self, port=9222, host="127.0.0.1", timeout=10.0, browser_id="chrome"):
        self.port = port
        self.host = host
        self.timeout = timeout
        self.browser_id = browser_id

    @property
    def base_url(self):
        return f"http://{self.host}:{self.port}"

    def available(self) -> bool:
        try:
            self.version()
            return True
        except BrowserConnectionError:
            return False

    def version(self):
        return self._http_json("/json/version")

    def list_tabs(self):
        targets = self._http_json("/json/list")
        return [
            BrowserTab(
                id=item["id"],
                title=item.get("title", ""),
                url=item.get("url", ""),
                browser=self.browser_id,
                backend=BackendKind.CDP,
                websocket_url=item.get("webSocketDebuggerUrl"),
            )
            for item in targets
            if item.get("type") == "page" and item.get("id")
        ]

    def tab(self, tab_id=None):
        tabs = self.list_tabs()
        if not tabs:
            raise BrowserTargetError("Browser has no page tabs")
        if tab_id:
            for tab in tabs:
                if tab.id == tab_id:
                    return tab
            raise BrowserTargetError(f"Browser tab not found: {tab_id}")
        return tabs[0]

    def command(self, method: str, params=None, tab_id=None):
        tab = self.tab(tab_id)
        if not tab.websocket_url:
            raise BrowserConnectionError(f"Tab has no DevTools WebSocket URL: {tab.id}")
        with CDPWebSocket(tab.websocket_url, self.timeout) as client:
            return client.command(method, params)

    def browser_command(self, method: str, params=None):
        websocket_url = self.version().get("webSocketDebuggerUrl")
        if not websocket_url:
            raise BrowserConnectionError("Browser DevTools endpoint has no WebSocket URL")
        with CDPWebSocket(websocket_url, self.timeout) as client:
            return client.command(method, params)

    def open_tab(self, url="about:blank"):
        return self._http_json(f"/json/new?{quote(url, safe=':/?&=%#')}", method="PUT")

    def close_tab(self, tab_id):
        return self._http_json(f"/json/close/{quote(tab_id, safe='')}")

    def activate_tab(self, tab_id):
        return self._http_json(f"/json/activate/{quote(tab_id, safe='')}")

    def _http_json(self, path, method="GET"):
        request = Request(self.base_url + path, method=method)
        try:
            with closing(urlopen(request, timeout=self.timeout)) as response:
                payload = response.read()
        except (HTTPError, URLError, OSError, TimeoutError) as exc:
            raise BrowserConnectionError(f"Cannot connect to CDP on {self.host}:{self.port}: {exc}") from exc
        try:
            return json.loads(payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise BrowserConnectionError("CDP endpoint returned invalid JSON") from exc
