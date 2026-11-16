#ifndef AIROPS_MYSQL_STORE_H
#define AIROPS_MYSQL_STORE_H
#include "scheduler.h"
#include <mysql/mysql.h>
#include <string>
#include <vector>

class MySQLStore {
public:
    MySQLStore();
    ~MySQLStore();
    MySQLStore(const MySQLStore&) = delete;
    MySQLStore& operator=(const MySQLStore&) = delete;
    bool connected() const;
    std::string error() const;
    bool listFlights();
    bool listRunways();
    bool addFlight(const std::string& number,const std::string& arrival,const std::string& type,
                   Priority priority,int requiredLength,int duration);
    bool addRunway(const std::string& name,int length);
    bool dispatch(SchedulingMode mode);
    bool completeAllocation(long long allocationId);
    bool showQueue();
    bool showHistory();
private:
    MYSQL* conn_{nullptr};
    std::string error_;
    bool query(const std::string& sql);
    bool executePrepared(const std::string& sql, const std::vector<std::string>& values);
    void logEvent(const std::string& type,const std::string& message);
};
#endif
