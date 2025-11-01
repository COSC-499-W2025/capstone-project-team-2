# setting this file up for an initial entry point for docker set up.
import psycopg2

conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="appdb",
    user="appuser",
    password="apppassword"
)