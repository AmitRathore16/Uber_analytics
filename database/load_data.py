# load_data.py

import pandas as pd
from sqlalchemy import create_engine

from config import (
    MYSQL_HOST,
    MYSQL_USER,
    MYSQL_PASSWORD,
    DATABASE_NAME
)

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{DATABASE_NAME}"
)


def load_uber():

    df = pd.read_csv("../dataset/uber.csv")

    df.to_sql(
        "uber_rides",
        engine,
        if_exists="replace",
        index=False
    )

    print("uber.csv loaded")


def load_vehicle_images():

    df = pd.read_csv("../dataset/veh_img.csv")


    df.to_sql(
        "vehicle_images",
        engine,
        if_exists="replace",
        index=False
    )

    print("veh_img.csv loaded")


def load_booking_images():

    df = pd.read_csv("../dataset/book_img.csv")

    df.to_sql(
        "booking_status_images",
        engine,
        if_exists="replace",
        index=False
    )

    print("book_img.csv loaded")


if __name__ == "__main__":
    load_uber()
    load_vehicle_images()
    load_booking_images()