# Viva notes

## 60-second project explanation
“Our project, AirOps, is an academic simulation of airport runway allocation using C++ and MySQL. Flights are modelled as processes and runways as shared resources. We implemented FCFS and Priority Scheduling with aging. The scheduler chooses an eligible flight, selects the shortest available runway that meets the required length, and records allocation in MySQL. Transactions and row-level locks keep the runway reservation, flight status, and allocation record consistent. Completing a flight releases the runway and records the end time. The project demonstrates OS scheduling, mutual exclusion, synchronization, deadlock-prevention design, resource allocation, and DBMS integrity.”

## Likely questions
**Q: Why model a flight as a process?**  
A: It has a lifecycle and competes for a limited resource, which makes it a useful teaching analogy for scheduling.

**Q: What is FCFS?**  
A: First-Come, First-Served selects the eligible waiting flight with the earliest arrival timestamp.

**Q: Why priority scheduling?**  
A: It models urgent requests. Emergency > High > Normal > Low in this simulation.

**Q: What is starvation? How do you reduce it?**  
A: A low-priority flight can wait indefinitely if higher-priority traffic keeps arriving. Aging raises effective priority for each configured waiting interval.

**Q: How is mutual exclusion achieved?**  
A: Only an AVAILABLE runway can be reserved. The app locks rows inside a transaction and updates the allocation, runway, and flight states before commit.

**Q: How is deadlock prevented?**  
A: Each dispatch operation acquires one runway resource and does not hold one runway while waiting for another. Locks are taken within a short transaction. In production, retry transient deadlocks and enforce a consistent lock order.

**Q: What does DBMS contribute?**  
A: Persistent records, primary/foreign keys, unique constraints, indexes, transactions, and an audit trail.

**Q: How does the runway best-fit rule improve utilization?**  
A: It selects the shortest available runway that meets the stated length requirement, leaving longer runways available for flights that need them. It is only a simplified heuristic.

**Q: Is this suitable for real airports?**  
A: No. It is an academic simulation and omits aviation safety rules, weather, runway direction, separation, and real-time ATC integration.

**Q: Which database is actually connected?**  
A: The final C++ CLI uses the MySQL C API. The live demo requires MySQL Server, Connector/C development files, and environment variables configured in the README.
