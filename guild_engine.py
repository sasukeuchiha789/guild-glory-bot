# ==========================================================
#  SYSTEM      : Guild Glory Core Runtime
#  MODULE      : Guild Execution Engine
#  FILE        : guild_engine.py
# ==========================================================

import time
import threading
import logging
from queue import Queue, Empty
from typing import Dict, Callable

from packet_builder import PacketBuilder

log = logging.getLogger("GuildGloryRuntime.Engine")

# ----------------------------------------------------------
# ENGINE STATES
# ----------------------------------------------------------

ENGINE_STATES = (
    "BOOT",
    "INITIALIZING",
    "SYNCING",
    "RUNNING",
    "DEGRADED",
    "SHUTDOWN",
)

# ----------------------------------------------------------
# ENGINE EVENTS
# ----------------------------------------------------------

EVENT_CLIENT_READY = "CLIENT_READY"
EVENT_CLIENT_DEGRADED = "CLIENT_DEGRADED"
EVENT_TICK = "ENGINE_TICK"
EVENT_SHUTDOWN = "ENGINE_SHUTDOWN"

# ----------------------------------------------------------
# TASK MODEL
# ----------------------------------------------------------

class EngineTask:
    """
    Represents a scheduled engine task.
    """

    def __init__(self, name: str, callback: Callable, interval: float):
        self.name = name
        self.callback = callback
        self.interval = interval
        self.last_run = 0.0

    def should_run(self) -> bool:
        return (time.time() - self.last_run) >= self.interval

    def run(self):
        log.debug(f"Executing task: {self.name}")
        self.callback()
        self.last_run = time.time()

# ----------------------------------------------------------
# EVENT DISPATCHER
# ----------------------------------------------------------

class EventDispatcher:
    """
    Lightweight event routing layer.
    """

    def __init__(self):
        self.handlers: Dict[str, list[Callable]] = {}

    def register(self, event: str, handler: Callable):
        self.handlers.setdefault(event, []).append(handler)
        log.debug(f"Handler registered for event: {event}")

    def dispatch(self, event: str, payload=None):
        handlers = self.handlers.get(event, [])
        log.debug(
            f"Dispatching event '{event}' to {len(handlers)} handlers"
        )
        for handler in handlers:
            try:
                handler(payload)
            except Exception as exc:
                log.error(
                    f"Event handler error [{event}]: {exc}"
                )

# ----------------------------------------------------------
# WORKER THREAD
# ----------------------------------------------------------

class EngineWorker(threading.Thread):
    """
    Background worker for processing engine jobs.
    """

    def __init__(self, engine_ref, worker_id: int):
        super().__init__(daemon=True)
        self.engine = engine_ref
        self.worker_id = worker_id
        self.running = True
        self.queue: Queue = Queue()

    def submit(self, job):
        self.queue.put(job)

    def run(self):
        log.debug(f"EngineWorker-{self.worker_id} started")
        while self.running:
            try:
                job = self.queue.get(timeout=1)
                job()
            except Empty:
                continue
            except Exception as exc:
                log.error(
                    f"Worker-{self.worker_id} job error: {exc}"
                )

    def stop(self):
        self.running = False

# ----------------------------------------------------------
# GUILD ENGINE CORE
# ----------------------------------------------------------

class GuildEngine(threading.Thread):
    """
    Central orchestration engine.
    """

    def __init__(self, client_ref):
        super().__init__(daemon=True, name="GuildEngine")
        self.client = client_ref
        self.state = "BOOT"
        self.running = True

        self.dispatcher = EventDispatcher()
        self.tasks: list[EngineTask] = []

        self.workers = [
            EngineWorker(self, i) for i in range(2)
        ]

        self.packet_builder = PacketBuilder(
            self.client.session.session_id
        )

        self._register_internal_handlers()

    # ------------------------------------------------------

    def run(self):
        log.info("GuildEngine thread started")
        self._transition("INITIALIZING")

        for worker in self.workers:
            worker.start()

        while self.running:
            try:
                self._engine_loop()
            except Exception as exc:
                log.error(f"Engine error: {exc}")
                self._transition("DEGRADED")
            time.sleep(0.1)

        self._shutdown_workers()
        log.info("GuildEngine terminated")

    # ------------------------------------------------------

    def _engine_loop(self):
        if self.state == "INITIALIZING":
            self._initialize()

        elif self.state == "SYNCING":
            self._sync_with_client()

        elif self.state == "RUNNING":
            self._run_tasks()
            self.dispatcher.dispatch(EVENT_TICK)

        elif self.state == "DEGRADED":
            self._handle_degraded()

        elif self.state == "SHUTDOWN":
            self.running = False

    # ------------------------------------------------------

    def _transition(self, new_state: str):
        log.warning(f"ENGINE STATE {self.state} -> {new_state}")
        self.state = new_state

    # ------------------------------------------------------

    def _initialize(self):
        log.info("Initializing engine subsystems")

        self._register_task(
            "heartbeat_emit",
            self._emit_heartbeat,
            interval=5
        )

        self._register_task(
            "health_monitor",
            self._monitor_health,
            interval=4
        )

        self._transition("SYNCING")

    def _sync_with_client(self):
        log.info("Syncing engine with client state")

        if self.client.state == "ACTIVE":
            self.dispatcher.dispatch(EVENT_CLIENT_READY)
            self._transition("RUNNING")
        else:
            log.warning(
                "Client not active — engine waiting"
            )
            time.sleep(1)

    # ------------------------------------------------------

    def _run_tasks(self):
        for task in self.tasks:
            if task.should_run():
                self._submit_task(task.run)

    # ------------------------------------------------------

    def _handle_degraded(self):
        log.warning("Engine entered DEGRADED mode")
        self.dispatcher.dispatch(EVENT_CLIENT_DEGRADED)

        time.sleep(2)
        self._transition("SYNCING")

    # ------------------------------------------------------
    # TASKS
    # ------------------------------------------------------

    def _emit_heartbeat(self):
        seq = self.client.session.sequence
        packet = self.packet_builder.build_heartbeat(seq)
        try:
            self.client.transport.send(packet)
            log.debug("Engine heartbeat packet submitted")
        except Exception:
            log.warning(
                "Heartbeat send failed (transport unavailable)"
            )

    def _monitor_health(self):
        log.debug("Performing engine health check")

        if self.client.state in ("DEGRADED", "DISCONNECTED"):
            log.warning(
                "Detected client instability from engine monitor"
            )
            self._transition("DEGRADED")

    # ------------------------------------------------------
    # TASK MANAGEMENT
    # ------------------------------------------------------

    def _register_task(self, name: str, callback: Callable, interval: float):
        task = EngineTask(name, callback, interval)
        self.tasks.append(task)
        log.debug(f"Task registered: {name}")

    def _submit_task(self, job):
        worker = self.workers[
            int(time.time()) % len(self.workers)
        ]
        worker.submit(job)

    # ------------------------------------------------------
    # EVENT HANDLERS
    # ------------------------------------------------------

    def _register_internal_handlers(self):
        self.dispatcher.register(
            EVENT_CLIENT_READY,
            self._on_client_ready
        )
        self.dispatcher.register(
            EVENT_CLIENT_DEGRADED,
            self._on_client_degraded
        )
        self.dispatcher.register(
            EVENT_SHUTDOWN,
            self._on_shutdown
        )

    def _on_client_ready(self, payload=None):
        log.info("Engine notified: client READY")

    def _on_client_degraded(self, payload=None):
        log.warning(
            "Engine notified: client DEGRADED"
        )

    def _on_shutdown(self, payload=None):
        log.info("Engine shutdown requested")
        self._transition("SHUTDOWN")

    # ------------------------------------------------------

    def shutdown(self):
        log.info("GuildEngine shutdown initiated")
        self.dispatcher.dispatch(EVENT_SHUTDOWN)

    def _shutdown_workers(self):
        for worker in self.workers:
            worker.stop()