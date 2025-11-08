# setting this file up for an initial entry point for docker set up.
import mysql.connector
from mysql.connector import Error

conn = mysql.connector.connect(
        host="localhost",          # matches the service name in docker-compose.yml
        port=3307,
        database="appdb",
        user="appuser",
        password="apppassword"
    )

print("✅ Connected to MySQL successfully!")
conn.close()



''' if you are to run a test for this code run: 

docker-compose up db 

in your terminal, output should look something like the following

[+] Running 2/2
 ✔ Network capstone-project-team-2_app_network  Created                                                                                                                                                                           0.2s 
 ✔ Container app_database                       Created                                                                                                                                                                           0.3s 
Attaching to app_database
app_database  |
app_database  | PostgreSQL Database directory appears to contain a database; Skipping initialization
app_database  |                                                                                                                                                                                                                        
app_database  | 2025-11-01 23:21:45.584 UTC [1] LOG:  starting PostgreSQL 15.14 on x86_64-pc-linux-musl, compiled by gcc (Alpine 14.2.0) 14.2.0, 64-bit
app_database  | 2025-11-01 23:21:45.586 UTC [1] LOG:  listening on IPv4 address "0.0.0.0", port 5432
app_database  | 2025-11-01 23:21:45.586 UTC [1] LOG:  listening on IPv6 address "::", port 5432
app_database  | 2025-11-01 23:21:45.600 UTC [1] LOG:  listening on Unix socket "/var/run/postgresql/.s.PGSQL.5432"
app_database  | 2025-11-01 23:21:45.625 UTC [29] LOG:  database system was shut down at 2025-11-01 22:21:04 UTC
app_database  | 2025-11-01 23:21:45.656 UTC [1] LOG:  database system is ready to accept connections
app_database  | 2025-11-01 23:26:45.702 UTC [27] LOG:  checkpoint starting: time
app_database  | 2025-11-01 23:26:45.761 UTC [27] LOG:  checkpoint complete: wrote 3 buffers (0.0%); 0 WAL file(s) added, 0 removed, 0 recycled; write=0.014 s, sync=0.006 s, total=0.060 s; sync files=2, longest=0.003 s, average=0.003 s; distance=0 kB, estimate=0 kB

once we create the data base and wish to set up actual credentials

update the python code as well as lines 28-33 and run:

docker-compose down -v  # -v removes old data
docker-compose up db
 '''