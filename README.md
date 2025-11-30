AI Day Manager - MySQL Setup (Branch: sonu)
This branch uses MySQL instead of SQLite.

🚀 Setup Steps
1. Clone and Switch Branch
```
   git clone <repository-url>
    cd ai_day_manager
    git checkout sonu
```
3. Start MySQL Container
```
docker-compose up -d
```
4. Create .env File
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
6. Install Dependencies
``` 
pip install -r requirements.txt
pip install mysqlclient python-dotenv
```
8. Run Migrations

```
python manage.py makemigrations
python manage.py migrate
```
10. Start Development Server
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

📝 Notes

Do NOT commit .env file
Keep Docker container running while developing
Always run migrations after pulling database changes
