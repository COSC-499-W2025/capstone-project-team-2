Database/docker instructions

 for docker set up run:

docker-compsoe build --no-cache
docker-compose up
docker exec -it ollama2 ollama pull qwen2.5-coder:1.5b
docker-compose up


reseting all docker data
docker-compose down -v  # -v removes old data




FOR SQL:

download mySQL at: https://dev.mysql.com/downloads/installer (use version 8.0.44 just what im using)

run through the installer and make sure PORT IS 3308 (this was an issue on my machine)

you can verify the server is running with 

netstat -ano | findstr 3308

results should look like the following 

  TCP    0.0.0.0:33060          0.0.0.0:0              LISTENING       30436
  TCP    [::]:33060             [::]:0                 LISTENING       30436

  to connect to the sql server:

  & "C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe" -u root -p --port=3308

  
then enter your password to connect and then run

mysql -u root -p --port=3308 < .\database.sql


you can verify the creation of the database tables and such by running

USE appdb

Show Tables

Describe project data 

+-------------+--------------+------+-----+-------------------+-------------------+
| Field       | Type         | Null | Key | Default           | Extra             |
+-------------+--------------+------+-----+-------------------+-------------------+
| id          | int          | NO   | PRI | NULL              | auto_increment    |
| filename    | varchar(255) | NO   |     | NULL              |                   |
| content     | json         | NO   |     | NULL              |                   |
| uploaded_at | timestamp    | YES  |     | CURRENT_TIMESTAMP | DEFAULT_GENERATED |
+-------------+--------------+------+-----+-------------------+-------------------+
 
TO RUN SET UP:

run these 3 commands in terminal:

docker compose down -v
docker compose build --no-cache
docker compose up