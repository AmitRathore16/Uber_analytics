# create_database.py

import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, DATABASE_NAME


def create_database():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD
    )

    cursor = conn.cursor()

    cursor.execute(
        f"CREATE DATABASE IF NOT EXISTS {DATABASE_NAME}"
    )

    conn.commit()
    cursor.close()
    conn.close()

    print(f"Database '{DATABASE_NAME}' ready")


if __name__ == "__main__":
    create_database()