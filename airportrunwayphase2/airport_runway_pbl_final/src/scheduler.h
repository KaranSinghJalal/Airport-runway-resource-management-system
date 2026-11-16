#ifndef AIROPS_SCHEDULER_H
#define AIROPS_SCHEDULER_H
#include <string>
#include <vector>

enum class Priority { LOW=1, NORMAL=2, HIGH=3, EMERGENCY=4 };
enum class FlightStatus { WAITING, IN_PROGRESS, COMPLETED, CANCELLED };
struct Flight {
    long long id{};
    std::string number, arrival;
    Priority priority{Priority::NORMAL};
    int requiredRunwayM{1800};
    FlightStatus status{FlightStatus::WAITING};
};
struct Runway {
    long long id{};
    std::string name;
    int lengthM{};
    bool available{true};
};
enum class SchedulingMode { FCFS, PRIORITY_AGING };

int priorityRank(Priority p);
int effectivePriority(const Flight& f, const std::string& now, int agingIntervalMinutes=15);
int chooseFlightIndex(const std::vector<Flight>& flights, SchedulingMode mode,
                      const std::string& now, int agingIntervalMinutes=15);
int chooseRunwayIndex(const std::vector<Runway>& runways, int requiredLengthM);
std::string toString(Priority p);
Priority priorityFromString(const std::string& s);
std::string toString(FlightStatus s);
#endif
