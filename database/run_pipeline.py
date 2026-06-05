# run_pipeline.py

from create_database import create_database
from create_tables import create_tables
from load_data import (
    load_uber,
    load_vehicle_images,
    load_booking_images
)


def run_pipeline():

    print("Step 1: Creating database...")
    create_database()

    print("Step 2: Creating tables...")
    create_tables()

    print("Step 3: Loading uber.csv...")
    load_uber()

    print("Step 4: Loading veh_img.csv...")
    load_vehicle_images()

    print("Step 5: Loading book_img.csv...")
    load_booking_images()

    print("\nPipeline completed successfully")


if __name__ == "__main__":
    run_pipeline()