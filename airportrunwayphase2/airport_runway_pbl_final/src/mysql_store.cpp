#include "mysql_store.h"
#include <cstdlib>
#include <iostream>
#include <sstream>
#include <iomanip>
#include <ctime>
#include <algorithm>
#include <cstring>

static std::string envOr(const char* key,const char* fallback) {
    const char* value=std::getenv(key); return value && *value ? value : fallback;
}
static std::string nowSql() {
    std::time_t t=std::time(nullptr); std::tm tm{};
#ifdef _WIN32
    localtime_s(&tm,&t);
#else
    localtime_r(&t,&tm);
#endif
    std::ostringstream out; out<<std::put_time(&tm,"%Y-%m-%d %H:%M:%S"); return out.str();
}
MySQLStore::MySQLStore() {
    conn_=mysql_init(nullptr);
    if(!conn_){error_="mysql_init failed";return;}
    unsigned int timeout=5; mysql_options(conn_,MYSQL_OPT_CONNECT_TIMEOUT,&timeout);
    const auto host=envOr("DB_HOST","127.0.0.1"), user=envOr("DB_USER","airops_app");
    const auto pass=envOr("DB_PASSWORD","change-this-password"), db=envOr("DB_NAME","airport_runway_db");
    const auto port=static_cast<unsigned int>(std::stoi(envOr("DB_PORT","3306")));
    if(!mysql_real_connect(conn_,host.c_str(),user.c_str(),pass.c_str(),db.c_str(),port,nullptr,0)){
        error_=mysql_error(conn_); mysql_close(conn_); conn_=nullptr;
    } else mysql_set_character_set(conn_,"utf8mb4");
}
MySQLStore::~MySQLStore(){if(conn_)mysql_close(conn_);}
bool MySQLStore::connected()const{return conn_!=nullptr;}
std::string MySQLStore::error()const{return error_;}
bool MySQLStore::query(const std::string& sql){
    if(!conn_){std::cerr<<"Database unavailable: "<<error_<<"\n";return false;}
    if(mysql_query(conn_,sql.c_str())!=0){error_=mysql_error(conn_);std::cerr<<"SQL error: "<<error_<<"\n";return false;}
    return true;
}
bool MySQLStore::executePrepared(const std::string& sql,const std::vector<std::string>& values){
    if(!conn_)return false;
    MYSQL_STMT* stmt=mysql_stmt_init(conn_);
    if(!stmt){error_=mysql_error(conn_);return false;}
    bool ok=mysql_stmt_prepare(stmt,sql.c_str(),static_cast<unsigned long>(sql.size()))==0;
    std::vector<MYSQL_BIND> binds(values.size()); std::vector<unsigned long> lengths(values.size());
    if(ok){
        for(std::size_t i=0;i<values.size();++i){
            std::memset(&binds[i],0,sizeof(MYSQL_BIND));
            lengths[i]=static_cast<unsigned long>(values[i].size());
            binds[i].buffer_type=MYSQL_TYPE_STRING;
            binds[i].buffer=const_cast<char*>(values[i].c_str());
            binds[i].buffer_length=lengths[i]; binds[i].length=&lengths[i];
        }
        if(!values.empty()) ok=mysql_stmt_bind_param(stmt,binds.data())==0;
        if(ok) ok=mysql_stmt_execute(stmt)==0;
    }
    if(!ok){error_=mysql_stmt_error(stmt);std::cerr<<"Prepared statement error: "<<error_<<"\n";}
    mysql_stmt_close(stmt); return ok;
}
void MySQLStore::logEvent(const std::string& type,const std::string& message){
    executePrepared("INSERT INTO activity_log(event_type,message,created_at) VALUES(?,?,?)",{type,message,nowSql()});
}
bool MySQLStore::listFlights(){
    if(!query("SELECT id,flight_number,arrival_time,flight_type,priority,status,required_runway_m FROM flights ORDER BY arrival_time,id"))return false;
    MYSQL_RES* r=mysql_store_result(conn_);if(!r)return false;MYSQL_ROW row;
    std::cout<<"\nID  FLIGHT      ARRIVAL             TYPE          PRIORITY    STATUS        REQUIRED(m)\n";
    while((row=mysql_fetch_row(r)))std::cout<<std::left<<std::setw(4)<<row[0]<<std::setw(12)<<row[1]<<std::setw(20)<<row[2]<<std::setw(14)<<row[3]<<std::setw(12)<<row[4]<<std::setw(14)<<row[5]<<(row[6]?row[6]:"")<<"\n";
    mysql_free_result(r);return true;
}
bool MySQLStore::listRunways(){
    if(!query("SELECT id,runway_name,length_m,status FROM runways ORDER BY length_m,id"))return false;
    MYSQL_RES* r=mysql_store_result(conn_);if(!r)return false;MYSQL_ROW row;
    std::cout<<"\nID  RUNWAY       LENGTH(m)  STATUS\n";
    while((row=mysql_fetch_row(r)))std::cout<<std::left<<std::setw(4)<<row[0]<<std::setw(13)<<row[1]<<std::setw(11)<<row[2]<<(row[3]?row[3]:"")<<"\n";
    mysql_free_result(r);return true;
}
bool MySQLStore::addFlight(const std::string& n,const std::string& a,const std::string& type,Priority p,int length,int duration){
    if(length<500||length>6000||duration<5||duration>240){std::cout<<"Length must be 500-6000m and duration 5-240 minutes.\n";return false;}
    const bool ok=executePrepared("INSERT INTO flights(flight_number,arrival_time,flight_type,priority,status,required_runway_m,estimated_duration_min) VALUES(?,?,?,?, 'WAITING',?,?)",
        {n,a,type,toString(p),std::to_string(length),std::to_string(duration)});
    if(ok){logEvent("FLIGHT_ADDED","Flight "+n+" added.");std::cout<<"Flight added to queue.\n";}return ok;
}
bool MySQLStore::addRunway(const std::string& n,int length){
    if(length<500||length>6000){std::cout<<"Runway length must be 500-6000m.\n";return false;}
    const bool ok=executePrepared("INSERT INTO runways(runway_name,length_m,status) VALUES(?,?,'AVAILABLE')",{n,std::to_string(length)});
    if(ok){logEvent("RUNWAY_ADDED","Runway "+n+" added.");std::cout<<"Runway added.\n";}return ok;
}
bool MySQLStore::dispatch(SchedulingMode mode){
    if(!conn_)return false;
    if(!query("START TRANSACTION"))return false;
    // Lock eligible flights and runways in one consistent transaction. Only one runway is acquired per dispatch.
    if(!query("SELECT id,flight_number,arrival_time,priority,status,required_runway_m FROM flights WHERE status='WAITING' ORDER BY arrival_time,id FOR UPDATE")){query("ROLLBACK");return false;}
    MYSQL_RES* fr=mysql_store_result(conn_);std::vector<Flight> flights;MYSQL_ROW row;
    while((row=mysql_fetch_row(fr))){
        Flight f;f.id=std::stoll(row[0]);f.number=row[1]?row[1]:"";f.arrival=row[2]?row[2]:"";
        f.priority=priorityFromString(row[3]?row[3]:"NORMAL");f.status=FlightStatus::WAITING;f.requiredRunwayM=std::stoi(row[5]?row[5]:"1800");flights.push_back(f);
    }mysql_free_result(fr);
    const auto now=nowSql();
    const int fi=chooseFlightIndex(flights,mode,now,15);
    if(fi<0){query("ROLLBACK");std::cout<<"No waiting flights.\n";return false;}
    if(!query("SELECT id,runway_name,length_m,status FROM runways WHERE status='AVAILABLE' ORDER BY length_m,id FOR UPDATE")){query("ROLLBACK");return false;}
    MYSQL_RES* rr=mysql_store_result(conn_);std::vector<Runway> runways;
    while((row=mysql_fetch_row(rr))){runways.push_back({std::stoll(row[0]),row[1]?row[1]:"",std::stoi(row[2]),true});}
    mysql_free_result(rr);
    const int ri=chooseRunwayIndex(runways,flights[static_cast<std::size_t>(fi)].requiredRunwayM);
    if(ri<0){query("ROLLBACK");std::cout<<"No suitable available runway; flight remains in the queue.\n";return false;}
    const auto flight=flights[static_cast<std::size_t>(fi)];const auto runway=runways[static_cast<std::size_t>(ri)];
    bool ok=executePrepared("INSERT INTO allocations(flight_id,runway_id,start_time,status) VALUES(?,?,?,'ACTIVE')",
        {std::to_string(flight.id),std::to_string(runway.id),now});
    if(ok)ok=executePrepared("UPDATE runways SET status='OCCUPIED' WHERE id=? AND status='AVAILABLE'",{std::to_string(runway.id)});
    if(ok && mysql_affected_rows(conn_)!=1)ok=false;
    if(ok)ok=executePrepared("UPDATE flights SET status='IN_PROGRESS' WHERE id=? AND status='WAITING'",{std::to_string(flight.id)});
    if(ok && mysql_affected_rows(conn_)!=1)ok=false;
    if(ok)ok=executePrepared("INSERT INTO activity_log(event_type,message,created_at) VALUES(?,?,?)",
        {"RUNWAY_ALLOCATED",flight.number+" allocated to "+runway.name+"." ,now});
    if(ok)ok=query("COMMIT");else query("ROLLBACK");
    if(ok)std::cout<<"Allocated "<<flight.number<<" to "<<runway.name<<" using "<<(mode==SchedulingMode::FCFS?"FCFS":"Priority + Aging")<<".\n";
    else std::cout<<"Allocation rolled back; no partial reservation was kept.\n";
    return ok;
}
bool MySQLStore::completeAllocation(long long id){
    if(!query("START TRANSACTION"))return false;
    const auto sql="SELECT a.flight_id,a.runway_id,a.status,f.flight_number FROM allocations a JOIN flights f ON f.id=a.flight_id WHERE a.id="+std::to_string(id)+" FOR UPDATE";
    if(!query(sql)){query("ROLLBACK");return false;}MYSQL_RES* r=mysql_store_result(conn_);MYSQL_ROW row=mysql_fetch_row(r);
    if(!row||!row[2]||std::string(row[2])!="ACTIVE"){mysql_free_result(r);query("ROLLBACK");std::cout<<"Active allocation not found.\n";return false;}
    std::string fid=row[0],rid=row[1],flight=row[3]?row[3]:"";mysql_free_result(r);
    bool ok=executePrepared("UPDATE allocations SET status='COMPLETED',end_time=? WHERE id=? AND status='ACTIVE'",{nowSql(),std::to_string(id)});
    if(ok)ok=executePrepared("UPDATE runways SET status='AVAILABLE' WHERE id=? AND status='OCCUPIED'",{rid});
    if(ok)ok=executePrepared("UPDATE flights SET status='COMPLETED' WHERE id=? AND status='IN_PROGRESS'",{fid});
    if(ok)ok=executePrepared("INSERT INTO activity_log(event_type,message,created_at) VALUES(?,?,?)",{"RUNWAY_RELEASED",flight+" completed; runway released.",nowSql()});
    if(ok)ok=query("COMMIT");else query("ROLLBACK");
    std::cout<<(ok?"Flight completed and runway released.\n":"Completion rolled back due to an error.\n");return ok;
}
bool MySQLStore::showQueue(){
    if(!query("SELECT id,flight_number,priority,arrival_time,required_runway_m FROM flights WHERE status='WAITING' ORDER BY arrival_time,id"))return false;
    MYSQL_RES* r=mysql_store_result(conn_);MYSQL_ROW row;std::cout<<"\nWAITING QUEUE\n";
    while((row=mysql_fetch_row(r)))std::cout<<"#"<<row[0]<<" "<<row[1]<<" | "<<row[2]<<" | arrived "<<row[3]<<" | needs "<<row[4]<<"m runway\n";
    mysql_free_result(r);return true;
}
bool MySQLStore::showHistory(){
    if(!query("SELECT a.id,f.flight_number,r.runway_name,a.start_time,a.end_time,a.status FROM allocations a JOIN flights f ON f.id=a.flight_id JOIN runways r ON r.id=a.runway_id ORDER BY a.id DESC LIMIT 100"))return false;
    MYSQL_RES* r=mysql_store_result(conn_);MYSQL_ROW row;std::cout<<"\nALLOCATION HISTORY (latest 100)\n";
    while((row=mysql_fetch_row(r)))std::cout<<"#"<<row[0]<<" "<<row[1]<<" -> "<<row[2]<<" | "<<row[3]<<" to "<<(row[4]?row[4]:"—")<<" | "<<row[5]<<"\n";
    mysql_free_result(r);return true;
}
