
from database import get_connection

conn = get_connection()

try:
    with conn.cursor() as cursor:
        cursor.execute(
            "SELECT current_database(), current_user"
        )
        result = cursor.fetchone()

        print("Database:", result[0])
        print("User:", result[1])
finally:
    conn.close()
