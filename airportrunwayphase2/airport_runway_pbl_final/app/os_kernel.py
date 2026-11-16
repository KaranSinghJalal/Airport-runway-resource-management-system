"""Educational OS layer for AirOps: process lifecycle, CPU scheduling and resource synchronization.

This is an operating-systems simulation, not an actual kernel or certified ATC controller.
Uses real Python threading primitives to protect shared state and demonstrates OS concepts.
"""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass, asdict
from threading import Lock, Semaphore, Thread
from time import time
from typing import Optional

VALID_ALGORITHMS = {"FCFS", "SJF", "PRIORITY", "ROUND_ROBIN"}
PRIORITY_RANK = {"emergency": 0, "high": 1, "normal": 2, "low": 3}

@dataclass
class Process:
    pid: int
    name: str
    burst: int
    priority: str = "normal"
    state: str = "READY"
    remaining: int = 0
    arrival_order: int = 0
    waiting: int = 0
    turnaround: int = 0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None

    def __post_init__(self):
        if not self.remaining:
            self.remaining = self.burst

    def public(self):
        d = asdict(self)
        d["started_at"] = round(d["started_at"], 3) if d["started_at"] else None
        d["finished_at"] = round(d["finished_at"], 3) if d["finished_at"] else None
        return d

class OSKernel:
    """Small thread-safe OS simulator with process table, ready queue and runway semaphores."""
    def __init__(self):
        self._lock = Lock()                 # mutex for process table and scheduler state
        self._next_pid = 1001
        self._sequence = 0
        self._processes: dict[int, Process] = {}
        self._ready: deque[int] = deque()   # ready queue
        self._events: deque[dict] = deque(maxlen=30)
        self._cpu_busy = False
        self._runs = 0
        self._last_algorithm = "PRIORITY"
        self._runway_semaphores = {"RWY-09": Semaphore(1), "RWY-27": Semaphore(1), "RWY-18": Semaphore(1)}
        self._resource_lock = Lock()
        self._resource_owners: dict[str, Optional[str]] = {k: None for k in self._runway_semaphores}
        self._event("OS_BOOT", "OS simulation initialized: mutex, ready queue and runway semaphores online")

    def _event(self, event, details):
        self._events.appendleft({"event": event, "details": details, "time": time()})

    def snapshot(self):
        with self._lock:
            processes = [p.public() for p in sorted(self._processes.values(), key=lambda x: x.pid, reverse=True)]
            counts = {s: sum(p.state == s for p in self._processes.values()) for s in ("READY", "RUNNING", "WAITING", "TERMINATED")}
            ready = list(self._ready)
            events = list(self._events)
            runs, algo = self._runs, self._last_algorithm
        with self._resource_lock:
            resources = [{"name": name, "available": owner is None, "owner": owner, "semaphore_permits": 1 if owner is None else 0} for name, owner in self._resource_owners.items()]
        return {"processes": processes, "counts": counts, "ready_queue": ready, "events": events,
                "resources": resources, "metrics": {"process_count": len(processes), "scheduler_runs": runs,
                "algorithm": algo, "mutex": "LOCKED/UNLOCKED (protected critical sections)",
                "ready_queue_size": len(ready), "threaded_http": True}}

    def create_process(self, name: str, burst: int, priority: str = "normal"):
        name = str(name).strip()[:60]
        priority = str(priority).lower()
        if not name or not 1 <= int(burst) <= 1000 or priority not in PRIORITY_RANK:
            raise ValueError("Enter a process name, CPU burst from 1 to 1000, and valid priority.")
        with self._lock:
            pid = self._next_pid; self._next_pid += 1; self._sequence += 1
            p = Process(pid, name, int(burst), priority, "READY", int(burst), self._sequence)
            self._processes[pid] = p; self._ready.append(pid)
            self._event("PROCESS_CREATED", f"PID {pid} ({name}) entered READY state with {burst} CPU units")
        return p.public()

    def terminate_process(self, pid: int):
        with self._lock:
            p = self._processes.get(int(pid))
            if not p or p.state == "TERMINATED":
                raise ValueError("Process not found or already terminated.")
            p.state = "TERMINATED"; p.finished_at = time(); p.turnaround = max(0, p.waiting + p.burst - p.remaining)
            self._ready = deque(x for x in self._ready if x != p.pid)
            self._event("PROCESS_TERMINATED", f"PID {p.pid} ({p.name}) terminated")
            return p.public()

    def simulate(self, algorithm="PRIORITY", quantum=2):
        algorithm = str(algorithm).upper()
        if algorithm not in VALID_ALGORITHMS:
            raise ValueError("Choose FCFS, SJF, PRIORITY, or ROUND_ROBIN.")
        quantum = max(1, min(int(quantum), 20))
        # Snapshot and simulate on copies while holding the mutex; no partial state leaks.
        with self._lock:
            jobs = [p for p in self._processes.values() if p.state in ("READY", "WAITING")]
            jobs.sort(key=lambda p: p.arrival_order)
            if not jobs:
                self._event("SCHEDULER_IDLE", "No READY processes to schedule")
                return {"algorithm": algorithm, "timeline": [], "message": "No READY processes to schedule.", "averages": {"waiting": 0, "turnaround": 0}}
            for p in jobs: p.state = "READY"
            timeline = []; clock = 0
            if algorithm == "FCFS":
                ordered = sorted(jobs, key=lambda p: p.arrival_order)
                for p in ordered:
                    timeline.append({"pid": p.pid, "name": p.name, "start": clock, "end": clock+p.remaining, "units": p.remaining})
                    clock += p.remaining
                    p.waiting = timeline[-1]["start"]; p.turnaround = clock
                    p.remaining = 0; p.state = "TERMINATED"; p.finished_at = time()
            elif algorithm in ("SJF", "PRIORITY"):
                if algorithm == "SJF": ordered = sorted(jobs, key=lambda p: (p.remaining, p.arrival_order))
                else: ordered = sorted(jobs, key=lambda p: (PRIORITY_RANK[p.priority], p.arrival_order))
                for p in ordered:
                    start = clock; clock += p.remaining
                    timeline.append({"pid": p.pid, "name": p.name, "start": start, "end": clock, "units": p.remaining})
                    p.waiting = start; p.turnaround = clock; p.remaining = 0; p.state = "TERMINATED"; p.finished_at = time()
            else:
                rr = deque(jobs)
                while rr:
                    p = rr.popleft(); used = min(quantum, p.remaining)
                    timeline.append({"pid": p.pid, "name": p.name, "start": clock, "end": clock+used, "units": used})
                    clock += used; p.remaining -= used
                    if p.remaining == 0:
                        p.state = "TERMINATED"; p.turnaround = clock; p.waiting = max(0, clock-p.burst); p.finished_at = time()
                    else:
                        p.state = "READY"; rr.append(p)
            self._ready = deque(p.pid for p in self._processes.values() if p.state == "READY")
            self._runs += 1; self._last_algorithm = algorithm
            self._event("CPU_SCHEDULED", f"{algorithm} scheduled {len(jobs)} process(es), simulated {clock} CPU units")
            waits = [p.waiting for p in jobs]; turns = [p.turnaround for p in jobs]
            return {"algorithm": algorithm, "quantum": quantum, "timeline": timeline,
                    "message": f"{len(jobs)} process(es) scheduled using {algorithm}.",
                    "averages": {"waiting": round(sum(waits)/len(waits), 2), "turnaround": round(sum(turns)/len(turns), 2)},
                    "total_cpu_units": clock}

    def acquire_runway(self, runway: str, flight_code: str):
        if runway not in self._runway_semaphores: raise ValueError("Unknown runway resource.")
        sem = self._runway_semaphores[runway]
        # Non-blocking acquisition demonstrates semaphore protection without hanging a web request.
        if not sem.acquire(blocking=False):
            raise ValueError(f"{runway} is already held by another process (semaphore unavailable).")
        with self._resource_lock:
            self._resource_owners[runway] = str(flight_code)
        with self._lock: self._event("SEMAPHORE_ACQUIRED", f"{flight_code} acquired exclusive resource {runway}")
        return True

    def release_runway(self, runway: str, flight_code: str | None = None):
        if runway not in self._runway_semaphores: return False
        with self._resource_lock:
            owner = self._resource_owners[runway]
            if owner is None or (flight_code and owner != str(flight_code)): return False
            self._resource_owners[runway] = None
        self._runway_semaphores[runway].release()
        with self._lock: self._event("SEMAPHORE_RELEASED", f"{owner} released resource {runway}")
        return True

    def reset_processes(self):
        with self._lock:
            self._processes.clear(); self._ready.clear(); self._next_pid = 1001; self._sequence = 0
            self._event("OS_RESET", "OS process table and ready queue cleared")

KERNEL = OSKernel()
