import mysql.connector
from mysql.connector import Error

def test_db():
    try:
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",      # si usas contraseña colócala aquí
            database="miapp"
        )
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tablas = cur.fetchall()

        print("✅ Conexión OK. Total tablas:", len(tablas))
        for t in tablas:
            print("-", t[0])

        cur.close()
        conn.close()

    except Error as e:
        print("❌ Error de conexión:", e)

if __name__ == "__main__":
    test_db()
