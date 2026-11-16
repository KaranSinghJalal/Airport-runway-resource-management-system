"""AirOps demo web server: Python standard library + SQLite; no pip installs required."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse
import json, sqlite3, threading, os, mimetypes
from os_kernel import KERNEL

ROOT = Path(__file__).resolve().parents[1]
WEB = ROOT / 'web'
DB_PATH = ROOT / 'data' / 'airops.sqlite3'
DB_PATH.parent.mkdir(parents=True, exist_ok=True)
DB_LOCK = threading.RLock()

RUNWAY_SEEDS = [
    ('RWY-09', 2400, 'North runway'), ('RWY-27', 3000, 'Central runway'),
    ('RWY-18', 3600, 'South runway')
]
FLIGHT_SEEDS = [
    ('AI101', 'Delhi', 'Boeing 737', 2500, 'normal'),
    ('6E204', 'Mumbai', 'Airbus A320', 2400, 'high'),
    ('SG412', 'Jaipur', 'ATR 72', 1800, 'normal'),
    ('AI999', 'Lucknow', 'Airbus A321', 3100, 'emergency'),
]

def connect():
    con = sqlite3.connect(DB_PATH, timeout=10)
    con.row_factory = sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON')
    return con

def init_db():
    with DB_LOCK, connect() as con:
        con.executescript('''
        CREATE TABLE IF NOT EXISTS runways(
          id INTEGER PRIMARY KEY AUTOINCREMENT, code TEXT UNIQUE NOT NULL,
          length_m INTEGER NOT NULL CHECK(length_m > 0), description TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','occupied')),
          current_flight_id INTEGER
        );
        CREATE TABLE IF NOT EXISTS flights(
          id INTEGER PRIMARY KEY AUTOINCREMENT, flight_code TEXT UNIQUE NOT NULL,
          destination TEXT NOT NULL, aircraft TEXT NOT NULL, required_length_m INTEGER NOT NULL CHECK(required_length_m > 0),
          priority TEXT NOT NULL CHECK(priority IN ('emergency','high','normal','low')),
          status TEXT NOT NULL DEFAULT 'waiting' CHECK(status IN ('waiting','assigned','completed','cancelled')),
          runway_id INTEGER REFERENCES runways(id), created_at TEXT NOT NULL DEFAULT (datetime('now','localtime')),
          assigned_at TEXT, completed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS activity_log(
          id INTEGER PRIMARY KEY AUTOINCREMENT, event TEXT NOT NULL, details TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now','localtime'))
        );
        ''')
        if con.execute('SELECT COUNT(*) FROM runways').fetchone()[0] == 0:
            con.executemany('INSERT INTO runways(code,length_m,description) VALUES(?,?,?)', RUNWAY_SEEDS)
        if con.execute('SELECT COUNT(*) FROM flights').fetchone()[0] == 0:
            con.executemany('INSERT INTO flights(flight_code,destination,aircraft,required_length_m,priority) VALUES(?,?,?,?,?)', FLIGHT_SEEDS)
            con.execute("INSERT INTO activity_log(event,details) VALUES('SYSTEM_READY','Demo flights and runways initialized')")

def log(con, event, details):
    con.execute('INSERT INTO activity_log(event,details) VALUES(?,?)', (event, details))

def rows(con, sql, args=()):
    return [dict(r) for r in con.execute(sql, args).fetchall()]

class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB), **kwargs)
    def log_message(self, fmt, *args):
        print('[AirOps]', fmt % args)
    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status); self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Content-Length',str(len(body))); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(body)
    def read_json(self):
        try:
            length = int(self.headers.get('Content-Length','0'))
            if length > 100_000: raise ValueError('Request is too large')
            return json.loads(self.rfile.read(length) or b'{}')
        except (ValueError, json.JSONDecodeError) as e:
            raise ValueError('Please send valid JSON data.') from e
    def do_GET(self):
        path = urlparse(self.path).path
        if path == '/api/health': return self.send_json({'ok': True, 'app':'AirOps', 'database':'SQLite', 'os_layer':'online'})
        if path == '/api/os': return self.send_json(KERNEL.snapshot())
        if path.startswith('/api/'):
            with DB_LOCK, connect() as con:
                if path == '/api/dashboard':
                    flights=rows(con, '''SELECT f.*,r.code AS runway_code FROM flights f LEFT JOIN runways r ON r.id=f.runway_id ORDER BY CASE f.status WHEN 'waiting' THEN 0 WHEN 'assigned' THEN 1 WHEN 'completed' THEN 2 ELSE 3 END, f.id DESC''')
                    runways=rows(con,'SELECT * FROM runways ORDER BY length_m')
                    logs=rows(con,'SELECT * FROM activity_log ORDER BY id DESC LIMIT 12')
                    counts={s:con.execute('SELECT COUNT(*) FROM flights WHERE status=?',(s,)).fetchone()[0] for s in ['waiting','assigned','completed','cancelled']}
                    return self.send_json({'flights':flights,'runways':runways,'logs':logs,'counts':counts})
                if path == '/api/flights': return self.send_json({'flights':rows(con,'SELECT f.*,r.code AS runway_code FROM flights f LEFT JOIN runways r ON r.id=f.runway_id ORDER BY f.id DESC')})
                return self.send_json({'error':'API endpoint not found'},404)
        if path == '/': self.path='/index.html'
        return super().do_GET()
    def do_POST(self):
        path=urlparse(self.path).path
        if not path.startswith('/api/'): return self.send_json({'error':'Not found'},404)
        try: data=self.read_json()
        except ValueError as e: return self.send_json({'error':str(e)},400)
        if path == '/api/os/process':
            try:
                process = KERNEL.create_process(data.get('name',''), int(data.get('burst',1)), data.get('priority','normal'))
                return self.send_json({'ok':True,'process':process,'message':f"Process PID {process['pid']} created in READY state."},201)
            except (ValueError, TypeError) as e:
                return self.send_json({'error':str(e)},400)
        if path == '/api/os/terminate':
            try:
                process = KERNEL.terminate_process(int(data.get('pid',0)))
                return self.send_json({'ok':True,'process':process,'message':f"PID {process['pid']} terminated."})
            except (ValueError, TypeError) as e:
                return self.send_json({'error':str(e)},400)
        if path == '/api/os/simulate':
            try:
                result = KERNEL.simulate(data.get('algorithm','PRIORITY'), int(data.get('quantum',2)))
                return self.send_json({'ok':True,**result})
            except (ValueError, TypeError) as e:
                return self.send_json({'error':str(e)},400)
        if path == '/api/os/reset':
            KERNEL.reset_processes()
            return self.send_json({'ok':True,'message':'OS process table reset.'})
        if path == '/api/os/resource/acquire':
            try:
                runway=str(data.get('runway','')); owner=str(data.get('owner','')).strip()
                if not owner: raise ValueError('Enter an owner/process label before acquiring a runway.')
                KERNEL.acquire_runway(runway, owner)
                return self.send_json({'ok':True,'message':f'{owner} acquired {runway}.'})
            except ValueError as e:
                return self.send_json({'error':str(e)},409)
        if path == '/api/os/resource/release':
            runway=str(data.get('runway','')); owner=str(data.get('owner','')).strip() or None
            if not KERNEL.release_runway(runway, owner):
                return self.send_json({'error':'Resource is free or the owner label does not match.'},409)
            return self.send_json({'ok':True,'message':f'{runway} released.'})
        with DB_LOCK, connect() as con:
            try:
                if path == '/api/flights':
                    code=str(data.get('flight_code','')).strip().upper()
                    dest=str(data.get('destination','')).strip(); aircraft=str(data.get('aircraft','')).strip()
                    try: length=int(data.get('required_length_m',0))
                    except (TypeError,ValueError): length=0
                    priority=str(data.get('priority','normal')).lower()
                    if not code or len(code)>16 or not dest or not aircraft or length < 500 or length > 10000 or priority not in {'emergency','high','normal','low'}:
                        return self.send_json({'error':'Enter a flight code, destination, aircraft, runway length (500–10000 m), and valid priority.'},400)
                    con.execute('INSERT INTO flights(flight_code,destination,aircraft,required_length_m,priority) VALUES(?,?,?,?,?)',(code,dest,aircraft,length,priority))
                    log(con,'FLIGHT_ADDED',f'{code} added with {priority} priority')
                    con.commit(); return self.send_json({'ok':True,'message':f'Flight {code} added.'},201)
                if path == '/api/schedule':
                    # One atomic DB transaction chooses the best suitable available runway.
                    waiting=rows(con,"SELECT * FROM flights WHERE status='waiting' ORDER BY CASE priority WHEN 'emergency' THEN 0 WHEN 'high' THEN 1 WHEN 'normal' THEN 2 ELSE 3 END, created_at, id")
                    assigned=[]; skipped=[]
                    for flight in waiting:
                        runway=con.execute("SELECT * FROM runways WHERE status='available' AND length_m>=? ORDER BY length_m ASC LIMIT 1",(flight['required_length_m'],)).fetchone()
                        if not runway:
                            skipped.append(flight['flight_code']); continue
                        try:
                            KERNEL.acquire_runway(runway['code'], flight['flight_code'])
                        except ValueError:
                            skipped.append(flight['flight_code']); continue
                        con.execute("UPDATE runways SET status='occupied',current_flight_id=? WHERE id=? AND status='available'",(flight['id'],runway['id']))
                        if con.execute("UPDATE flights SET status='assigned',runway_id=?,assigned_at=datetime('now','localtime') WHERE id=? AND status='waiting'",(runway['id'],flight['id'])).rowcount:
                            assigned.append({'flight':flight['flight_code'],'runway':runway['code']})
                            log(con,'RUNWAY_ASSIGNED',f"{flight['flight_code']} assigned to {runway['code']}")
                        else:
                            con.execute("UPDATE runways SET status='available',current_flight_id=NULL WHERE id=?",(runway['id'],))
                            KERNEL.release_runway(runway['code'], flight['flight_code'])
                    con.commit()
                    msg=f"Assigned {len(assigned)} flight(s)."
                    if skipped: msg += ' No suitable free runway for: ' + ', '.join(skipped) + '.'
                    if not assigned and not skipped: msg='No waiting flights to schedule.'
                    return self.send_json({'ok':True,'message':msg,'assigned':assigned,'skipped':skipped})
                if path == '/api/complete':
                    try: fid=int(data.get('flight_id',0))
                    except (ValueError,TypeError): fid=0
                    f=con.execute("SELECT * FROM flights WHERE id=? AND status='assigned'",(fid,)).fetchone()
                    if not f: return self.send_json({'error':'Choose a flight that is currently assigned to a runway.'},400)
                    con.execute("UPDATE flights SET status='completed',completed_at=datetime('now','localtime') WHERE id=?",(fid,))
                    con.execute("UPDATE runways SET status='available',current_flight_id=NULL WHERE id=? AND current_flight_id=?",(f['runway_id'],fid))
                    runway_row = con.execute('SELECT code FROM runways WHERE id=?',(f['runway_id'],)).fetchone()
                    if runway_row: KERNEL.release_runway(runway_row['code'], f['flight_code'])
                    log(con,'FLIGHT_COMPLETED',f"{f['flight_code']} completed; runway released")
                    con.commit(); return self.send_json({'ok':True,'message':f"{f['flight_code']} completed and runway released."})
                if path == '/api/cancel':
                    try: fid=int(data.get('flight_id',0))
                    except (ValueError,TypeError): fid=0
                    f=con.execute("SELECT * FROM flights WHERE id=? AND status='waiting'",(fid,)).fetchone()
                    if not f: return self.send_json({'error':'Only waiting flights can be cancelled.'},400)
                    con.execute("UPDATE flights SET status='cancelled' WHERE id=?",(fid,)); log(con,'FLIGHT_CANCELLED',f"{f['flight_code']} cancelled")
                    con.commit(); return self.send_json({'ok':True,'message':f"{f['flight_code']} cancelled."})
                if path == '/api/reset-demo':
                    con.execute('DELETE FROM activity_log'); con.execute('DELETE FROM flights'); con.execute('UPDATE runways SET status=\'available\',current_flight_id=NULL')
                    for rr in con.execute('SELECT code FROM runways').fetchall(): KERNEL.release_runway(rr['code'])
                    con.executemany('INSERT INTO flights(flight_code,destination,aircraft,required_length_m,priority) VALUES(?,?,?,?,?)',FLIGHT_SEEDS)
                    log(con,'DEMO_RESET','Demo data reset to initial state'); con.commit()
                    return self.send_json({'ok':True,'message':'Demo data restored.'})
                return self.send_json({'error':'API endpoint not found'},404)
            except sqlite3.IntegrityError as e:
                con.rollback()
                msg='That flight code already exists. Use a unique flight code.' if 'UNIQUE' in str(e).upper() else 'The data violates a database constraint.'
                return self.send_json({'error':msg},409)
            except Exception as e:
                con.rollback(); return self.send_json({'error':'The operation failed safely. Please refresh and try again.'},500)

if __name__ == '__main__':
    init_db()
    host=os.environ.get('AIROPS_HOST','127.0.0.1'); port=int(os.environ.get('AIROPS_PORT','8000'))
    print(f'AirOps running at http://{host}:{port}  |  Demo database: {DB_PATH}')
    print('Academic simulation only — not for real-world air traffic control.')
    ThreadingHTTPServer((host,port),Handler).serve_forever()
