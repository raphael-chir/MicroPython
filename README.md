[![Generic badge](https://img.shields.io/badge/Version-1.0-<COLOR>.svg)](https://shields.io/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://GitHub.com/Naereen/StrapDown.js/graphs/commit-activity)
![Maintainer](https://img.shields.io/badge/maintainer-raphael.chir@gmail.com-blue)

# MicroPython = Python Flask SQL Server microservices 

## Architecture setup
Everything is easier with docker, so a docker-compose.yml is used to setup the architecture stack
```yml
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
```sql
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
```k
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

## Deploy on an instance

You can launch an ec2 instance for instance with a Ubuntu AMI and git clone this repository on it. We will install docker and docker-compose later. We won't use snap to do it to get more control on user/group we will assign to docker cmd.

Now we want to collect metrics, logs and perform APM with Datadog

## Install a Datadog Agent on the host

### Live Process activation

We suppose that you are registered to https://app.datadoghq.com/ and you have get a key

Pay attention on the environment where datadog agent collects data (metrics, ...). So we export an env var, for instance :
'''
export DD_ENV=agent-host-staging
'''

Simply use UI to configure the setup command to execute, for instance
```
DD_API_KEY=56b1eb243863e9b37cd81d0b344638ff DD_SITE="datadoghq.com" bash -c "$(curl -L https://install.datadoghq.com/scripts/install_script_agent7.sh)"
```

When finished check the status :
```
sudo datadog-agent status
```
And the config, in particular regarding the env :
```
sudo datadog-agent config|grep ^env
```
*Note that if you want to remove the agent, simply execute*
```
sudo apt-get remove --purge datadog-agent -y
```
Take a look on Datadog UI where you can already see system resources metrics, but for now we will activate Live Process feature by editing **datadog.yml** (I use **vim**) and uncomment these properties to obtain :
```
process_config
  process_collection
    enabled:true
```
In order to take effect, restart datadog agent service : 
```
sudo systemctl restart datadog-agent
```
Verify directly the Live Process config with :
```
sudo datadog-agent config  |grep process_collection -A1
```
Go to Datadog UI to check all metrics collected !

### Docker installation and configuration reminder

Docker installation commands
```bash
sudo apt update
sudo apt upgrade
sudo apt install apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install docker-ce
sudo docker --version
```
docker-compose installation commands
```
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
docker-compose --version
```
cd into MicroFlask and execute :
```
sudo docker-compose up
```
You will notice that there is a port issue ! Port 5000 is already in use.
Quick reminder on how to verify it is already uses. 
```
sudo netstat -tuln
```
or
```
sudo ss -tuln
```
or
```
sudo lsof -i -P -n
```
or
```
nc -zv 127.0.0.1 5000
```
Just change the port in docker-compose-yaml to expose 5050 that listen to 5000 in the container
Then try again
```
sudo docker-compose up
```

Test your api endpoints : 
```
curl -X POST http://ec2-15-237-37-208.eu-west-3.compute.amazonaws.com:5050/bookings \                                             
-H "Content-Type: application/json" \
-d '{"customer_name": "John Doe", "date": "2024-10-15"}'
```
```
curl -i http://ec2-15-237-37-208.eu-west-3.compute.amazonaws.com:5050/bookings | jq 
```
### Logs Activation

How to collect log from the docker containers and sent them to Datadog ? We need to configure datadog agent !

Edit **datadog.yml** (I use **vim**) and uncomment these properties to obtain :
```
logs_enabled:true
logs_config:
  container_collect_all:true
```
In order to take effect, restart datadog agent service : 
```
sudo systemctl restart datadog-agent
```
But it won't work because dd-agent user is not part of docker group. And it is too bad due to the docker installation I performed with root. 
Firstly we find the path of docker command
```
whereis docker
```
then when we **ll into /usr/bin/docker** and list all groups of the system with **getent group**, docker group doesn't exist. We need to create it :
```
sudo groupadd docker
sudo chgrp docker /usr/bin/docker
```
Well it's done, now we can attach the user dd-agent to this group :
```
sudo usermod -a -G docker dd-agent
sudo getent group docker 
```
And to take effect, datadog-agent must be restarsted
```
sudo systemctl restart datadog-agent
```

Seems to be finished at thi point, go to Datadog UI and 
- Go to Log Explorer
- Filter with env:agent-host-staging
- Try Live Tail
- Execute API resources to see the logs collected

### APM Activation

Edit **datadog.yml** (I use **vim**) and uncomment these properties to obtain :
```
apm_config:
  apm_non_local_traffic:true
```
In order to take effect, restart datadog agent service : 
```
sudo systemctl restart datadog-agent
```

Now we must declare **ddtrace** in **requirements.txt** to activate Datadog APM. Just uncomment the line.

For a first test, we don't use Dockerfile but configure **docker-compose.yml** (specifically the MicroPython service named web) - Just uncomment the related line : 

``` yml
# Version of docker-compose without Dockerfile usage
# To configure APM uncomment related section and replace command: by the other one

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
    # environment:
    #   - ENV DD_SERVICE="bookings"
    #   - ENV DD_ENV="agent-host-staging"
    #   - ENV DD_VERSION="0.1.0"
    #   - DD_AGENT_HOST=host.docker.internal
    # labels:
    #   - com.datadoghq.tags.service="bookings"
    #   - com.datadoghq.tags.env="agent-host-staging"
    #   - com.datadoghq.tags.version="0.1.0"
    ports:
      - "5050:5000"
    command: >
      bash -c "pip install -r requirements.txt && python app.py"
    #command: [ "bash", "-c", "pip install -r requirements.txt && ddtrace-run python app.py" ]
    depends_on:
      - sqlserver
    # extra_hosts:
    #   - "host.docker.internal:host-gateway"

```
Then
```
sudo docker-compose up
```

## Useful commands
```
adduser <user>
groupadd <group>
ss -tuln
nc -zv <host> <port>
usermod -a -G <group> <user>
getent group
getent group <group>
chgrp <group> <path to file>
chown <user:group> <path to file>
df -h
du -sh
...

With vim
:set nu
:/regexp
:<line number>
:dd
:i
:wq
...
```
