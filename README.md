AI Day Manager - MySQL Setup (Branch: sonu)
This branch uses MySQL instead of SQLite.

Prerequisites

   Docker
   Python 3.11+
   Git

🚀 Setup Steps
1. Clone and Switch Branch
```
   git clone <repository-url>
    cd ai_day_manager
    git checkout sonu
```
2. Start MySQL Container
```
docker-compose up -d
```
Note: If docker-compose doesn't work, try docker compose up -d (without hyphen)

3. Create .env File
```
touch .env
```
Add the following configuration:
env
```
DB_ENGINE=mysql
DB_NAME=planner_db
DB_USER=root
DB_PASSWORD=root@pass
DB_HOST=127.0.0.1
DB_PORT=3306
```

⚠️ Important:

   Replace your_database_name, your_username, and your_password with your preferred values
   Never commit .env to version control
   
4. Update Docker Compose (Optional)
If you changed credentials in .env, update docker-compose.yml accordingly:
yaml
MYSQL_DATABASE: your_database_name
MYSQL_USER: your_username
MYSQL_PASSWORD: your_password

5. Install Dependencies
``` 
pip install -r requirements.txt
pip install mysqlclient python-dotenv
```
6. Run Migrations

```
python manage.py makemigrations
python manage.py migrate
```
7. Start Development Server
```
python manage.py runserver
```
Open: http://127.0.0.1:8000



⚠️ Troubleshooting
Port 3306 already in use:
Change port in docker-compose.yml and .env file
mysqlclient installation fails:
Install PyMySQL instead:
```
pip install pymysql
```
Add to settings.py
```
pythonimport pymysql
pymysql.install_as_MySQLdb()
```

Do NOT commit .env file
Keep Docker container running while developing
Always run migrations after pulling database changes
