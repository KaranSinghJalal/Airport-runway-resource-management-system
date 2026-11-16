# Operating Systems Implementation — AirOps

## OS concepts implemented in the runnable web application

1. **Process management / PCB** — every simulated process has a PID, name, priority, CPU burst, remaining time, arrival order, waiting time, turnaround time, timestamps, and process state.
2. **Process states** — READY and TERMINATED are explicitly tracked; the model includes RUNNING and WAITING state labels for extension.
3. **Ready queue** — newly created processes enter a FIFO ready queue; scheduler algorithms select from the process table and update the queue.
4. **CPU scheduling** — FCFS, non-preemptive SJF, non-preemptive priority scheduling, and Round Robin with a configurable time quantum.
5. **Scheduling metrics** — Gantt-style CPU timeline, average waiting time, average turnaround time, and total simulated CPU units.
6. **Mutual exclusion** — Python `Lock` protects process-table and scheduler mutations; a separate lock protects resource ownership.
7. **Semaphore-based resource synchronization** — each runway has a binary semaphore; non-blocking acquire prevents two simulated owners from holding one runway at once; release validates ownership.
8. **Kernel event trace** — process creation/termination, scheduler runs, and resource acquisition/release are recorded in a bounded event log.
9. **Threaded server** — `ThreadingHTTPServer` handles requests with threads, making synchronization meaningful for concurrent requests.

## How to demonstrate this for the OS subject

- Open **OS Lab** in the website.
- Create at least three processes with different burst lengths and priorities.
- Run FCFS, SJF, Priority, then Round Robin and compare the timelines and metrics.
- Acquire `RWY-09` with one owner label, then attempt a second acquisition. The second should be rejected while the semaphore is unavailable.
- Release the runway using the matching owner and observe the permit return to 1.
- Terminate a READY process and observe the process table/event trace.

## Important scope note

This is an educational OS-concept simulation implemented in user space, not a replacement for the operating-system kernel. Scheduling time units are simulated. It is not an aviation control system.
