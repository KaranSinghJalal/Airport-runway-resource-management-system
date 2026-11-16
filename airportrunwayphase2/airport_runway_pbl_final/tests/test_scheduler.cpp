#include "../src/scheduler.h"
#include <cassert>
#include <iostream>
#include <vector>
int main(){
    const std::string now="2026-10-16 12:00:00";
    std::vector<Flight> fs={
        {1,"NORMAL-EARLY","2026-10-16 11:50:00",Priority::NORMAL,1800,FlightStatus::WAITING},
        {2,"EMERGENCY-LATE","2026-10-16 11:59:00",Priority::EMERGENCY,2200,FlightStatus::WAITING},
        {3,"CANCELLED","2026-10-16 11:40:00",Priority::HIGH,1800,FlightStatus::CANCELLED}
    };
    assert(chooseFlightIndex(fs,SchedulingMode::FCFS,now)==0);
    assert(chooseFlightIndex(fs,SchedulingMode::PRIORITY_AGING,now)==1);
    std::vector<Runway> rs={{1,"Long",3600,true},{2,"Medium",3000,true},{3,"Short",2400,true},{4,"Occupied",2200,false}};
    assert(chooseRunwayIndex(rs,2200)==2); // shortest suitable available runway
    assert(chooseRunwayIndex(rs,4000)==-1);
    fs[1].priority=Priority::LOW;
    fs[1].arrival="2026-10-16 11:00:00";
    assert(effectivePriority(fs[1],now,15)==4); // 60 min waiting => rank capped at emergency
    std::cout<<"All scheduler tests passed.\n";
}
