# AirOps — Intelligent Airport Runway and Resource Management System
**Six-member PBL | C++ scheduling engine + MySQL database**

> Academic simulation only. Not for real-world air traffic control or safety-critical decisions.

## What is implemented
- C++17 scheduling engine with **FCFS** and **Priority Scheduling**.
- Priority order: Emergency > High > Normal > Low; arrival time breaks ties.
- Runway resource inventory and allocation/release lifecycle.
- Mutual-exclusion guard: a runway cannot be allocated twice while occupied.
- Deadlock-prevention design: allocation takes one runway resource at a time, in a single transaction; no process holds one runway while waiting for another.
- Starvation mitigation: priority aging raises the effective priority of long-waiting flights.
- Runway suitability: shortest available runway that meets the aircraft's required runway length is selected, helping preserve longer runways for aircraft that need them.
- MySQL 8 schema, foreign keys, uniqueness constraints, indexes, audit events, and transaction boundaries.
- C++ MySQL C API adapter (`mysql.h`) with prepared statements for core CRUD and allocation operations.
- Automated algorithm tests that run without MySQL, plus a MySQL integration test plan.
- Project report, ER diagram, six-member role plan, viva notes, and presentation.

## Prerequisites
- C++17 compiler (GCC 9+, Clang 10+, or recent MSVC with adjustments).
- MySQL Server 8.0+ and a MySQL C client development library.
- On Ubuntu/Debian: `sudo apt install g++ default-libmysqlclient-dev mysql-server`
- Windows: install MySQL Server and MySQL Connector/C (C API headers/library), then set include/library paths for your compiler.

## Database setup
1. Open MySQL Workbench or MySQL CLI.
2. Run the complete `sql/schema.sql` script.
3. It creates `airport_runway_db` and its tables, indexes, seed runways, and demo flights.
4. Create a least-privilege database user for the app rather than using the MySQL root account.

Example (adapt the password before use):
```sql
CREATE USER 'airops_app'@'localhost' IDENTIFIED BY 'change-this-password';
GRANT SELECT, INSERT, UPDATE, DELETE ON airport_runway_db.* TO 'airops_app'@'localhost';
FLUSH PRIVILEGES;
```

## Configure and compile
Set environment variables (do not commit secrets):
```bash
export DB_HOST=127.0.0.1
export DB_PORT=3306
export DB_NAME=airport_runway_db
export DB_USER=airops_app
export DB_PASSWORD='your-local-password'
```
On Windows PowerShell, use `$env:DB_HOST="127.0.0.1"` etc.

Compile on Linux:
```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic src/main.cpp src/scheduler.cpp src/mysql_store.cpp \
  -o airops $(mysql_config --cflags --libs)
./airops
```
If `mysql_config` is not available, use the include and link flags documented by your MySQL Connector/C package. The program expects a running MySQL server and the schema above.

## Menu
- List flights/runways
- Add a flight
- Add a runway
- Dispatch next flight using FCFS or Priority + Aging
- Complete an active allocation and release its runway
- Show current waiting queue
- Show allocation history
- Exit

## Scheduling model
### FCFS
Select the eligible waiting flight with the earliest arrival time; ID is the deterministic tie-breaker.

### Priority with aging
Base ranks: Low=1, Normal=2, High=3, Emergency=4. For each configured aging interval (default 15 minutes), a waiting flight gains one effective rank, capped at Emergency. Effective rank is compared first, then earlier arrival. This is a teaching-oriented fairness policy; it is not an aviation-standard rule.

### Runway utilization
The system selects the **shortest available runway whose declared length is at least the flight's required runway length**. This best-fit rule is a simple resource-utilization heuristic. It does not account for runway direction, weather, aircraft performance, or regulatory restrictions.

### Synchronization and deadlock prevention
- Every allocation begins a MySQL transaction and locks the selected flight and runway rows using `SELECT ... FOR UPDATE`.
- The transaction checks both flight status and runway status before inserting an allocation.
- The runway is marked occupied and flight marked in-progress before commit.
- The application reserves only one runway per operation; it does not acquire multiple runway locks in different orders.
- Completion locks the allocation/runway/flight rows, records the end time, releases the runway, and marks the flight complete in one transaction.
- Foreign keys and unique constraints protect data integrity.
- Transactions are rolled back on failure. Retry transient deadlocks at the application layer if productionizing; this classroom app reports the failure clearly.

## Testing
Run algorithm tests:
```bash
g++ -std=c++17 -Wall -Wextra -Wpedantic tests/test_scheduler.cpp src/scheduler.cpp -o test_scheduler
./test_scheduler
```
This suite does not need MySQL. MySQL integration tests are described in `docs/TEST_PLAN.md`.

## Project structure
```text
airport_runway_pbl_final/
├── src/                 C++ application and MySQL adapter
├── sql/schema.sql       MySQL schema and demo data
├── tests/               Algorithm tests
├── docs/                Report, ER model, roles, test plan, viva notes
├── presentation.pptx    Six-member PBL presentation
└── README.md
```

## Limitations and future scope
This is a simplified teaching simulation. It does not integrate live flight feeds, runway weather conditions, aircraft separation standards, taxiways, air traffic control, or certification processes. It must never be used to dispatch real aircraft. Future extensions include a web dashboard, role-based authentication, MySQL connection pooling, configurable aircraft-runway compatibility, and a graphical utilization chart.
