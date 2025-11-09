# setting this file up for an initial entry point for docker set up.
import mysql.connector
from mysql.connector import Error

conn = mysql.connector.connect(
        host="app_database",          # matches the service name in docker-compose.yml
        port=3306,
        database="appdb",
        user="appuser",
        password="apppassword"
    )

print("✅ Connected to MySQL successfully!")
conn.close()