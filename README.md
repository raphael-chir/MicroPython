[![Generic badge](https://img.shields.io/badge/Version-1.0-<COLOR>.svg)](https://shields.io/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Maintainer](https://img.shields.io/badge/maintainer-raphael.chir@gmail.com-blue)

# MicroPython = Python Flask SQL Server microservices 

## Architecture setup
Everything is easier with docker, so a docker-compose.yml is used to setup the architecture stack
```
version: '3.8'

services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2022-latest
    environment:
      - SA_PASSWORD=StrongPassword123!
      - ACCEPT_EULA=Y
    ports:
      - "1433:1433"

  initdb:
    image: mcr.microsoft.com/mssql-tools
    depends_on:
      - sqlserver
    environment:
      SA_PASSWORD: 'StrongPassword123!'
    volumes:
      - ./init.sql:/init.sql
    entrypoint: /bin/bash -c "sleep 30 && /opt/mssql-tools/bin/sqlcmd -S sqlserver -U sa -P 'StrongPassword123!' -i /init.sql -C"

  web:
    image: python:3.10-slim
    volumes:
      - ./app.py:/app/app.py
      - ./requirements.txt:/app/requirements.txt
    working_dir: /app
    ports:
      - "5000:5000"
    command: >
      bash -c "pip install -r requirements.txt && python app.py"
    depends_on:
      - sqlserver

```

- Warn to the password format rules, here I use the value **StrongPassword123!** 
- To init the database, a best practise is to launch a dedicated container to initialize the schema of the database. See init.sql and don't forget to add **GO** to execute the statements
- Microservice is embedded in a python docker image, so it is easier to get drivers to interact with SQL Server. (Too many config with Mac OS even if possible)

init.sql
```
-- init.sql
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'BookingDB')
BEGIN
    CREATE DATABASE BookingDB;
END
GO

USE BookingDB;
GO

IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = N'bookings')
BEGIN
    CREATE TABLE bookings (
        id INT PRIMARY KEY IDENTITY(1,1),
        customer_name NVARCHAR(100) NOT NULL,
        date NVARCHAR(10) NOT NULL
    );
END
GO
```
Too easy :)

## A one file python code

Even if DDD is a good pattern, here I want to simplify as possible Rest API to be minimalistic. See **app.py**  

These are the libs used in requirements.txt
```
Flask==2.2.3
Flask-SQLAlchemy==3.0.2
pymssql==2.2.5
Werkzeug==2.2.2
```
To be updated to the last version to resolve compatibilities with Werkzeug

SQLAlchemy is the lib that will act as an ORM for a small aggregate model of a unique table. We will perform a simple CRUD on it. We also use pymssql to interact with SQL Server.

```
app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pymssql://sa:StrongPassword123!@sqlserver:1433/BookingDB'
```

## Execution

```
docker-compose up
```

- Add -D if needed, but leave this option out to track logs ...  
- Enjoy and modify the code 