# setting this file up for an initial entry point for docker set up.
import mysql.connector
from mysql.connector import Error

conn = mysql.connector.connect(
        host="db",          # matches the service name in docker-compose.yml
        port=33060,
        database="appdb",
        user="appuser",
        password="apppassword"
    )

print("✅ Connected to MySQL successfully!")
conn.close()