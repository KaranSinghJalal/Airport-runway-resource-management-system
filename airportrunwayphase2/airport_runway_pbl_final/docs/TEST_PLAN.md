# Test plan

## Algorithm tests (no MySQL required)
Compile and run `tests/test_scheduler.cpp` with `src/scheduler.cpp`.
1. FCFS selects the earliest waiting arrival.
2. Priority + aging selects the highest effective rank.
3. Cancelled/ineligible flights are ignored.
4. Best-fit runway selection chooses the shortest suitable available runway.
5. No suitable runway returns `-1`.
6. Aging caps the effective rank at Emergency.

## MySQL integration checks
Run these only after loading `sql/schema.sql`:
1. Valid flight insert appears in `flights`.
2. Duplicate flight number is rejected by UNIQUE constraint.
3. Dispatch creates one ACTIVE allocation, sets runway OCCUPIED, and sets flight IN_PROGRESS.
4. A second dispatch cannot reuse the occupied runway.
5. If all suitable runways are unavailable, dispatch rolls back and leaves the flight WAITING.
6. Completing an ACTIVE allocation sets allocation COMPLETED, sets end_time, marks flight COMPLETED, and runway AVAILABLE.
7. Foreign keys reject allocation rows referencing nonexistent flights/runways.
8. Confirm activity_log contains FLIGHT_ADDED, RUNWAY_ALLOCATED, and RUNWAY_RELEASED events.
9. Two concurrent dispatch attempts should not allocate the same runway due to transaction and row locks; test using two app processes/sessions.
10. Invalid runway length and duration are rejected by the application.

## Expected limitations
The algorithm unit tests are included and runnable without MySQL. A live MySQL integration test was not run in the packaging environment because a MySQL server and connector development package may not be installed there. Do not claim those integration checks passed until your team runs them against your MySQL instance.
