#!/usr/bin/env python3
# ==========================================================
#  SYSTEM      : Guild Glory Core Runtime
#  COMPONENT   : Network Client (TCP + UDP Diagnostics)
#  FILE        : client.py
# ==========================================================

import os
import time
import json
import socket
import random
import string
import logging
import threading
import hashlib
import errno
from queue import Queue, Empty
from datetime import datetime

# ----------------------------------------------------------
# LOGGER
# ----------------------------------------------------------

log = logging.getLogger("GuildGloryRuntime.Client")

# ----------------------------------------------------------
# CONSTANTS
# ----------------------------------------------------------

DEFAULT_TIMEOUT = 5
HEARTBEAT_INTERVAL = 3
RECONNECT_BASE_DELAY = 2
RECONNECT_MAX_DELAY = 30

CLIENT_STATES = (
    "INIT",
    "RESOLVING",
    "CONNECTING",
    "HANDSHAKE",
    "ACTIVE",
    "DEGRADED",
    "DISCONNECTED",
    "TERMINATED",
)

# ----------------------------------------------------------
# HELPERS
# ----------------------------------------------------------

def generate_session_id(length=24):
    seed = ''.join(random.choices(string.ascii_letters + string.digits, k=length))
    return hashlib.sha1(seed.encode()).hexdigest()

def utc_now():
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

# ----------------------------------------------------------
# TRANSPORT (TCP-STYLE)
# ----------------------------------------------------------

class TransportAdapter:
    """
    Socket-like TCP transport abstraction.
    """

    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket = None
        self.connected = False

    def open(self):
        log.debug("Opening TCP transport")
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(DEFAULT_TIMEOUT)
        # NOTE: no real connect performed
        self.connected = True

    def close(self):
        log.debug("Closing TCP transport")
        try:
            if self.socket:
                self.socket.close()
        finally:
            self.connected = False

    def send(self, payload: bytes):
        if not self.connected:
            raise RuntimeError("TCP transport not connected")
        # intentionally no outbound traffic
        time.sleep(0.01)

    def receive(self, size=4096) -> bytes:
        if not self.connected:
            raise RuntimeError("TCP transport not connected")
        time.sleep(0.01)
        return b""

# ----------------------------------------------------------
# UDP DIAGNOSTICS (ERROR SOURCE)
# ----------------------------------------------------------

class UDPDiagnostics:
    """
    UDP diagnostics layer.
    Purpose: detect low-level UDP socket availability and capture readiness.
    """

    def __init__(self, bind_ip="0.0.0.0", bind_port=0):
        self.bind_ip = bind_ip
        self.bind_port = bind_port
        self.sock = None
        self.active = False

    def initialize(self):
        log.info("Initializing UDP diagnostics")
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(2)

            # Attempt bind (common failure surface on restricted envs)
            self.sock.bind((self.bind_ip, self.bind_port))
            self.active = True

            log.info(
                f"UDP socket bound on {self.bind_ip}:{self.bind_port}"
            )

        except PermissionError:
            log.error(
                "UDP socket permission denied "
                "(CAP_NET_RAW / CAP_NET_ADMIN missing)"
            )
            raise

        except OSError as e:
            if e.errno in (errno.EADDRINUSE, errno.EACCES):
                log.error(
                    f"UDP bind failed: {e.strerror} (errno={e.errno})"
                )
            else:
                log.error(
                    f"UDP initialization error: {e}"
                )
            raise

    def probe(self):
        if not self.active:
            raise RuntimeError("UDP socket not initialized")

        try:
            # No real peer — probe receive path
            self.sock.recvfrom(1024)
        except socket.timeout:
            log.warning(
                "UDP capture timeout — no packets received "
                "(possible firewall / ISP / kernel restriction)"
            )
        except OSError as e:
            log.error(
                f"UDP recv error: {e.strerror} (errno={e.errno})"
            )

    def shutdown(self):
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        self.active = False
        log.debug("UDP diagnostics shutdown")

# ----------------------------------------------------------
# SESSION CONTEXT
# ----------------------------------------------------------

class ClientSession:
    """
    Holds runtime session data.
    """

    def __init__(self):
        self.session_id = generate_session_id()
        self.established_at = time.time()
        self.last_activity = time.time()
        self.handshake_complete = False
        self.sequence = 0

    def touch(self):
        self.last_activity = time.time()
        self.sequence += 1

# ----------------------------------------------------------
# HANDSHAKE
# ----------------------------------------------------------

class HandshakeProcessor:
    """
    Multi-stage handshake pipeline.
    """

    def __init__(self, session: ClientSession):
        self.session = session
        self.stage = 0

    def execute(self):
        log.debug("Handshake started")
        for step in range(3):
            self.stage = step + 1
            self._process_stage()
        self.session.handshake_complete = True
        log.info("Handshake completed")

    def _process_stage(self):
        payload = {
            "stage": self.stage,
            "ts": utc_now(),
            "sid": self.session.session_id
        }
        time.sleep(0.15)
        log.debug(f"Handshake stage {self.stage} OK | {payload}")

# ----------------------------------------------------------
# HEARTBEAT
# ----------------------------------------------------------

class HeartbeatWorker(threading.Thread):

    def __init__(self, client_ref):
        super().__init__(daemon=True, name="HeartbeatWorker")
        self.client = client_ref

    def run(self):
        log.debug("Heartbeat worker started")
        while self.client.running:
            if self.client.state == "ACTIVE":
                self.client.send_heartbeat()
            time.sleep(HEARTBEAT_INTERVAL)

# ----------------------------------------------------------
# CLIENT CORE
# ----------------------------------------------------------

class NetworkClient(threading.Thread):
    """
    Network client with TCP lifecycle and UDP diagnostics.
    """

    def __init__(self, host="127.0.0.1", port=9000):
        super().__init__(daemon=True, name="NetworkClient")
        self.host = host
        self.port = port

        self.state = "INIT"
        self.running = True

        self.session = ClientSession()
        self.transport = TransportAdapter(host, port)
        self.udp_diag = UDPDiagnostics()

        self.outbound_queue = Queue()
        self.inbound_queue = Queue()

        self.heartbeat = HeartbeatWorker(self)
        self.reconnect_delay = RECONNECT_BASE_DELAY

    # ------------------------------------------------------

    def run(self):
        log.info("Client thread started")
        while self.running:
            try:
                self._state_machine()
            except Exception as exc:
                log.error(f"Client error: {exc}")
                self._transition("DEGRADED")
                self._handle_reconnect()

    # ------------------------------------------------------

    def _state_machine(self):
        if self.state == "INIT":
            self._transition("RESOLVING")

        elif self.state == "RESOLVING":
            self._resolve_endpoint()

        elif self.state == "CONNECTING":
            self._connect()

        elif self.state == "HANDSHAKE":
            self._handshake()

        elif self.state == "ACTIVE":
            self._active_loop()

        elif self.state == "DEGRADED":
            self._handle_reconnect()

        elif self.state == "TERMINATED":
            self.running = False

        time.sleep(0.05)

    # ------------------------------------------------------

    def _transition(self, new_state):
        log.debug(f"STATE {self.state} -> {new_state}")
        self.state = new_state

    # ------------------------------------------------------

    def _resolve_endpoint(self):
        log.info(f"Resolving endpoint {self.host}:{self.port}")

        # UDP diagnostics gate
        try:
            self.udp_diag.initialize()
            self.udp_diag.probe()
        except Exception:
            log.warning(
                "UDP transport layer unavailable — "
                "server socket or capture path not ready"
            )
            self._transition("DEGRADED")
            return

        time.sleep(0.2)
        self._transition("CONNECTING")

    def _connect(self):
        log.info("Establishing TCP connection")
        self.transport.open()
        self._transition("HANDSHAKE")

    def _handshake(self):
        processor = HandshakeProcessor(self.session)
        processor.execute()
        self.heartbeat.start()
        self._transition("ACTIVE")

    # ------------------------------------------------------

    def _active_loop(self):
        self._flush_outbound()
        self._poll_inbound()
        time.sleep(0.1)

    # ------------------------------------------------------

    def _flush_outbound(self):
        try:
            payload = self.outbound_queue.get_nowait()
            self.transport.send(payload)
            self.session.touch()
            log.debug(f"Outbound packet seq={self.session.sequence}")
        except Empty:
            pass

    def _poll_inbound(self):
        # no inbound source
        pass

    # ------------------------------------------------------

    def send(self, data: dict):
        encoded = json.dumps(data).encode()
        self.outbound_queue.put(encoded)

    def send_heartbeat(self):
        hb = {
            "op": "HEARTBEAT",
            "sid": self.session.session_id,
            "seq": self.session.sequence,
            "ts": utc_now()
        }
        self.send(hb)
        log.info("Heartbeat dispatched")

    # ------------------------------------------------------

    def _handle_reconnect(self):
        log.warning("Connection degraded, attempting recovery")
        log.warning(
            "Reason: UDP server socket unavailable or capture failed"
        )

        try:
            self.udp_diag.shutdown()
        except Exception:
            pass

        self.transport.close()
        time.sleep(self.reconnect_delay)

        self.reconnect_delay = min(
            self.reconnect_delay * 2,
            RECONNECT_MAX_DELAY
        )

        self._transition("RESOLVING")

    # ------------------------------------------------------

    def shutdown(self):
        log.info("Client shutdown initiated")
        self.running = False
        try:
            self.udp_diag.shutdown()
        except Exception:
            pass
        self.transport.close()
        self._transition("TERMINATED")