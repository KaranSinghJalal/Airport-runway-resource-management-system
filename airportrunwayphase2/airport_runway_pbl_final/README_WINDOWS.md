# AirOps — Complete Project with Frontend (Windows Quick Start)

This package now includes a browser-based dashboard that runs locally with Python's standard library and SQLite. **No `pip install`, MySQL connector, Node.js, or Code Runner is needed for the demo UI.** The existing C++17 + MySQL implementation, SQL schema, report, presentation, scheduler tests and viva notes remain included for the academic submission.

## Run the working dashboard
1. Extract the entire ZIP folder first (do not run files from inside the ZIP preview).
2. Install Python 3.10+ from https://www.python.org/downloads/ if it is not already installed. During setup, tick **Add Python to PATH**.
3. Double-click `run_windows.bat`.
4. Wait until the terminal says `AirOps running at http://127.0.0.1:8000`.
5. Open Chrome and visit **http://127.0.0.1:8000**.
6. Keep the terminal window open while using the site. To stop the server, press `Ctrl+C` in that window.

## Dashboard features
- Responsive frontend with live dashboard cards.
- Add and search flights; filter by status.
- Emergency/high/normal/low priority scheduling.
- Best-fit runway assignment: shortest free runway long enough for the aircraft.
- Runway exclusivity and safe completion/release lifecycle.
- Cancel waiting flights, activity audit log, resettable demo data.
- Persistent local SQLite database at `data/airops.sqlite3`.

## Important architecture note
The out-of-the-box dashboard is a runnable demonstration using Python's built-in HTTP server and SQLite. The original `src/` C++17 scheduling/MySQL implementation and `sql/schema.sql` are retained as the native academic implementation. The browser demo does **not** connect to MySQL and is not a real airport control system. This is a learning simulation only.

## Existing C++/MySQL implementation
See `README.md` for the C++17 build/database setup, `src/` for code, `sql/schema.sql` for MySQL schema, `tests/` for scheduler tests, `docs/Project_Report.docx`, `presentation.pptx`, and `docs/VIVA_NOTES.md`.

## Troubleshooting
- **`python` is not recognized:** install Python and enable “Add Python to PATH”, then reopen the terminal.
- **Port 8000 is in use:** open a terminal in the project folder and run `set AIROPS_PORT=8001` then `python app\server.py`; visit `http://127.0.0.1:8001`.
- **Page does not load:** confirm the terminal still shows the server running and that you opened the exact local URL.
- **Demo data reset:** use the dashboard's “Reset demo data” action. It restores the seed data in the local SQLite database.

Academic simulation only. Do not use for real-world air traffic control or safety-critical decisions.

## New: Operating Systems Lab
Scroll to **OS Lab** on the dashboard. This module is a real interactive implementation of OS concepts in the app layer:
- Process table with PIDs, process state, priority, CPU burst, terminate action.
- FCFS, SJF, Priority and Round Robin CPU scheduling.
- Gantt-style execution timeline and waiting/turnaround metrics.
- Mutex-protected shared state and binary semaphore for each runway.
- Acquire/release controls to demonstrate mutual exclusion and resource ownership.
- Kernel event log to inspect process and resource lifecycle events.

See `OS_IMPLEMENTATION.md` for a guided college demonstration and the OS concepts covered.
