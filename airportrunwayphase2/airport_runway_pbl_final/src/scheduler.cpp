#include "scheduler.h"
#include <algorithm>
#include <ctime>
#include <cstdio>
#include <limits>

static std::time_t parseTime(const std::string& value) {
    std::tm tm{};
    // MySQL DATETIME format: YYYY-MM-DD HH:MM:SS; also accept T separator.
    std::string s=value;
    if (s.size()>10 && s[10]=='T') s[10]=' ';
    if (s.size() < 19) return 0;
    int y=0, mo=0, d=0, h=0, mi=0, sec=0;
    if (std::sscanf(s.c_str(), "%d-%d-%d %d:%d:%d", &y,&mo,&d,&h,&mi,&sec)!=6) return 0;
    tm.tm_year=y-1900; tm.tm_mon=mo-1; tm.tm_mday=d; tm.tm_hour=h; tm.tm_min=mi; tm.tm_sec=sec;
    tm.tm_isdst=-1;
    return std::mktime(&tm);
}
int priorityRank(Priority p) { return static_cast<int>(p); }
int effectivePriority(const Flight& f, const std::string& now, int agingIntervalMinutes) {
    int rank=priorityRank(f.priority);
    if (agingIntervalMinutes<=0) return rank;
    const auto arrival=parseTime(f.arrival), current=parseTime(now);
    if (arrival>0 && current>arrival) {
        const auto waited=static_cast<int>((current-arrival)/60);
        rank += waited/agingIntervalMinutes;
    }
    return std::min(rank, priorityRank(Priority::EMERGENCY));
}
int chooseFlightIndex(const std::vector<Flight>& flights, SchedulingMode mode,
                      const std::string& now, int agingIntervalMinutes) {
    int best=-1;
    for (std::size_t i=0;i<flights.size();++i) {
        if (flights[i].status!=FlightStatus::WAITING) continue;
        if (best<0) { best=static_cast<int>(i); continue; }
        const auto& a=flights[i]; const auto& b=flights[static_cast<std::size_t>(best)];
        if (mode==SchedulingMode::FCFS) {
            if (a.arrival < b.arrival || (a.arrival==b.arrival && a.id<b.id)) best=static_cast<int>(i);
        } else {
            const int pa=effectivePriority(a,now,agingIntervalMinutes);
            const int pb=effectivePriority(b,now,agingIntervalMinutes);
            if (pa>pb || (pa==pb && (a.arrival<b.arrival || (a.arrival==b.arrival && a.id<b.id)))) best=static_cast<int>(i);
        }
    }
    return best;
}
int chooseRunwayIndex(const std::vector<Runway>& runways, int requiredLengthM) {
    int best=-1;
    for (std::size_t i=0;i<runways.size();++i) {
        if (!runways[i].available || runways[i].lengthM<requiredLengthM) continue;
        if (best<0 || runways[i].lengthM<runways[static_cast<std::size_t>(best)].lengthM)
            best=static_cast<int>(i);
    }
    return best;
}
std::string toString(Priority p) {
    switch(p){case Priority::LOW:return "LOW";case Priority::NORMAL:return "NORMAL";case Priority::HIGH:return "HIGH";case Priority::EMERGENCY:return "EMERGENCY";}
    return "NORMAL";
}
Priority priorityFromString(const std::string& s) {
    if(s=="LOW") return Priority::LOW;
    if(s=="HIGH") return Priority::HIGH;
    if(s=="EMERGENCY") return Priority::EMERGENCY;
    return Priority::NORMAL;
}
std::string toString(FlightStatus s) {
    switch(s){case FlightStatus::WAITING:return "WAITING";case FlightStatus::IN_PROGRESS:return "IN_PROGRESS";case FlightStatus::COMPLETED:return "COMPLETED";case FlightStatus::CANCELLED:return "CANCELLED";}
    return "WAITING";
}
