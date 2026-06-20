
import psycopg2

DB_PARAMS = {
    "host": "seal-users.c180so2u4aci.us-east-2.rds.amazonaws.com",
    "database": "Interacciones", 
    "user": "postgres",
    "password": "********",
    "port": "5432"
}

conn = psycopg2.connect(**DB_PARAMS)
cursor = conn.cursor()

print(f"\n Conectado a la base de datos: {DB_PARAMS['database']}\n")

cursor.execute("SELECT COUNT(*) FROM interacciones;")
total = cursor.fetchone()[0]
print(f"Total de interacciones registradas: {total}")

if total > 0:
    cursor.execute("SELECT * FROM interacciones ORDER BY id_interaccion DESC LIMIT 5;")
    rows = cursor.fetchall()
    print("\nÚltimas 5 interacciones:")
    for row in rows:
        print(row)

cursor.close()
conn.close()