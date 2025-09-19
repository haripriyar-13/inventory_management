import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = '23BCR020@hari'
    MYSQL_DB = 'inventory_db'
    MYSQL_CURSORCLASS = 'DictCursor'