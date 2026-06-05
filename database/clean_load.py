# clean_load.py
import pandas as pd
from sqlalchemy import create_engine, Date, Time, String, Text, Numeric
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, DATABASE_NAME

engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}/{DATABASE_NAME}"
)

def clean_and_load_uber():
    print("Loading uber.csv...")
    df = pd.read_csv("../dataset/uber.csv", low_memory=False)

    print("Cleaning columns...")
    # Clean Date column
    df['Date'] = pd.to_datetime(df['Date'], format='mixed')
    
    # Clean Time column
    # Ensure time strings are formatted as HH:MM:SS
    # In pandas, we can keep them as string, and mapping to Time type in to_sql will convert them.
    # Let's clean nulls if any
    
    # For to_sql, mapping dictionary
    dtype_dict = {
        'Date': Date(),
        'Time': String(100), # Using string for Time is highly safe and compatible
        'Booking ID': String(100),
        'Booking Status': String(100),
        'Customer ID': String(100),
        'Vehicle Type': String(100),
        'Pickup Location': String(255),
        'Drop Location': String(255),
        'Cancelled Rides by Customer': Numeric(5, 2),
        'Reason for cancelling by Customer': Text(),
        'Cancelled Rides by Driver': Numeric(5, 2),
        'Driver Cancellation Reason': Text(),
        'Incomplete Rides': Numeric(5, 2),
        'Incomplete Rides Reason': Text(),
        'Booking Value': Numeric(10, 2),
        'Ride Distance': Numeric(10, 2),
        'Driver Ratings': Numeric(3, 2),
        'Customer Rating': Numeric(3, 2),
        'Payment Method': String(100)
    }

    print("Writing to MySQL table uber_rides...")
    df.to_sql(
        "uber_rides",
        engine,
        if_exists="replace",
        index=False,
        dtype=dtype_dict
    )
    print("Table uber_rides updated with clean schemas successfully!")

if __name__ == "__main__":
    clean_and_load_uber()
