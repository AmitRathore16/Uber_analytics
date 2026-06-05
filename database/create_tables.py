# create_tables.py

import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, DATABASE_NAME


def create_tables():

    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME
    )

    cursor = conn.cursor()

    # Drop tables if they already exist
    cursor.execute("DROP TABLE IF EXISTS uber_rides")
    cursor.execute("DROP TABLE IF EXISTS vehicle_images")
    cursor.execute("DROP TABLE IF EXISTS booking_status_images")

    # Uber data table
    cursor.execute("""
    CREATE TABLE uber_rides (

        `Date` DATE,
        `Time` TIME,
        `Booking ID` VARCHAR(100),
        `Booking Status` VARCHAR(100),
        `Customer ID` VARCHAR(100),
        `Vehicle Type` VARCHAR(100),
        `Pickup Location` VARCHAR(255),
        `Drop Location` VARCHAR(255),
        `Cancelled Rides by Customer` VARCHAR(100),
        `Reason for cancelling by Customer` TEXT,
        `Cancelled Rides by Driver` VARCHAR(100),
        `Driver Cancellation Reason` TEXT,
        `Incomplete Rides` VARCHAR(100),
        `Incomplete Rides Reason` TEXT,
        `Booking Value` DECIMAL(10,2),
        `Ride Distance` DECIMAL(10,2),
        `Driver Ratings` DECIMAL(3,2),
        `Customer Rating` DECIMAL(3,2),
        `Payment Method` VARCHAR(100)

    )
    """)

    # Vehicle image mapping table
    cursor.execute("""
    CREATE TABLE vehicle_images (

        `Vehicle Type` VARCHAR(100),
        `Img` TEXT

    )
    """)

    # Booking status image mapping table
    cursor.execute("""
    CREATE TABLE booking_status_images (

        `Booking Status` VARCHAR(100),
        `Img` TEXT

    )
    """)

    conn.commit()

    cursor.close()
    conn.close()

    print("Tables created successfully")


if __name__ == "__main__":
    create_tables()