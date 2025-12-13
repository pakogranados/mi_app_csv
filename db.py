import mysql.connector
from mysql.connector import pooling
import os
from dotenv import load_dotenv

load_dotenv()

def conexion_db():
    """Conexión sin pool para evitar problemas de conexiones agotadas"""
    try:
        return mysql.connector.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            user=os.environ.get('DB_USER', 'root'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'miapp'),
            autocommit=False,
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
    except mysql.connector.Error as err:
        print(f"❌ Error conectando a la base de datos: {err}")
        print(f"   Host: {os.environ.get('DB_HOST', 'localhost')}")
        print(f"   User: {os.environ.get('DB_USER', 'root')}")
        print(f"   Database: {os.environ.get('DB_NAME', 'miapp')}")
        raise