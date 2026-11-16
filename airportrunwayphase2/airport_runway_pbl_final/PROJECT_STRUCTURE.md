# Project Structure

- `run_windows.bat` — starts the local demo on Windows.
- `app/server.py` — threaded HTTP server, API routes, SQLite persistence and runway dispatch logic.
- `app/os_kernel.py` — educational OS layer: process table, ready queue, scheduling algorithms, mutexes, runway semaphores, event trace.
- `web/index.html` — dashboard and OS Lab interface.
- `web/styles.css` — responsive dashboard styling.
- `web/app.js` — frontend API integration, flight management, process/scheduler/semaphore controls.
- `data/airops.sqlite3` — local demo database created on first run (not required in a clean ZIP).
- `src/` — C++17 application and MySQL C API implementation.
- `sql/schema.sql` — MySQL schema.
- `tests/` — C++ scheduling tests.
- `docs/` — report, viva notes, test plan and team roles.
- `presentation.pptx` — presentation.
- `OS_IMPLEMENTATION.md` — OS concepts and demo guide.
