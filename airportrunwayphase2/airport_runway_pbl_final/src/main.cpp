#include "mysql_store.h"
#include <iostream>
#include <limits>
#include <string>

static int readInt(const std::string& prompt,int min,int max){
    int n;
    while(true){std::cout<<prompt;if(std::cin>>n&&n>=min&&n<=max){std::cin.ignore(std::numeric_limits<std::streamsize>::max(),'\n');return n;}
        std::cout<<"Enter a number between "<<min<<" and "<<max<<".\n";std::cin.clear();std::cin.ignore(std::numeric_limits<std::streamsize>::max(),'\n');}
}
static std::string readText(const std::string& prompt){
    std::string s;std::cout<<prompt;std::getline(std::cin,s);return s;
}
int main(){
    std::cout<<"====================================================\n"
             <<" AirOps | Airport Runway Resource Management (PBL)\n"
             <<" C++17 + MySQL | Academic simulation only\n"
             <<"====================================================\n";
    MySQLStore store;
    if(!store.connected()){std::cerr<<"Cannot connect to MySQL: "<<store.error()<<"\n"
        <<"Check MySQL service, sql/schema.sql, and DB_HOST/DB_USER/DB_PASSWORD/DB_NAME.\n";return 1;}
    std::cout<<"Connected to MySQL database.\n";
    while(true){
        std::cout<<"\n1. List flights\n2. List runways\n3. Add flight\n4. Add runway\n"
                 <<"5. Dispatch next flight (FCFS)\n6. Dispatch next flight (Priority + Aging)\n"
                 <<"7. Complete allocation / release runway\n8. Show waiting queue\n9. Allocation history\n0. Exit\n";
        const int choice=readInt("Choose: ",0,9);
        switch(choice){
        case 1: store.listFlights();break;
        case 2: store.listRunways();break;
        case 3:{
            auto n=readText("Flight number (e.g. AI-208): ");
            auto a=readText("Arrival time (YYYY-MM-DD HH:MM:SS): ");
            auto t=readText("Type DOMESTIC/INTERNATIONAL/CARGO/MEDICAL: ");
            auto p=readText("Priority LOW/NORMAL/HIGH/EMERGENCY: ");
            int len=readInt("Required runway length in metres (500-6000): ",500,6000);
            int dur=readInt("Estimated runway time in minutes (5-240): ",5,240);
            store.addFlight(n,a,t,priorityFromString(p),len,dur);break;}
        case 4:{auto n=readText("Runway name: ");int len=readInt("Runway length in metres (500-6000): ",500,6000);store.addRunway(n,len);break;}
        case 5: store.dispatch(SchedulingMode::FCFS);break;
        case 6: store.dispatch(SchedulingMode::PRIORITY_AGING);break;
        case 7: store.completeAllocation(readInt("Active allocation ID to complete: ",1,2147483647));break;
        case 8: store.showQueue();break;
        case 9: store.showHistory();break;
        case 0: std::cout<<"Goodbye.\n";return 0;
        }
    }
}
