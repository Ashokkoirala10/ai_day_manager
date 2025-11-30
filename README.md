AI Day Manager - MySQL Setup (Branch: sonu)
Setup Steps
1. Clone and Switch Branch
bashgit clone <repository-url>
cd ai_day_manager
git checkout sonu
2. Start MySQL
bashdocker-compose up -d
3. Create .env File
bashtouch .env
Add:
envDB_ENGINE=mysql
DB_NAME=planner_db
DB_USER=root
DB_PASSWORD=root@pass
DB_HOST=127.0.0.1
DB_PORT=3306
4. Install Dependencies
bashpip install -r requirements.txt
pip install mysqlclient python-dotenv
5. Run Migrations
bashpython manage.py makemigrations
python manage.py migrate
6. Run Server
bashpython manage.py runserver
Open: http://127.0.0.1:8000

Team Workflow
bashgit checkout sonu
git pull origin sonu
docker-compose up -d
# Create .env if missing
python manage.py migrate
python manage.py runserver

Troubleshooting
If port 3306 is in use: Change port in docker-compose.yml and .env
If mysqlclient fails: Install pymysql instead and add to settings.py:
pythonimport pymysql
pymysql.install_as_MySQLdb()Claude can make mistakes. Please double-check responses. Sonnet 4.5