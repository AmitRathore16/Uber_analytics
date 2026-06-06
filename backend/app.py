# app.py
import os
import sys
import json
import decimal
import mysql.connector
from flask import Flask, request, jsonify
from flask_cors import CORS
from groq import Groq

# Support decimals in JSON serialization across all Flask versions
try:
    from flask.json.provider import DefaultJSONProvider
    class CustomJSONProvider(DefaultJSONProvider):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return super().default(o)
    HAS_PROVIDER = True
except ImportError:
    class DecimalEncoder(json.JSONEncoder):
        def default(self, o):
            if isinstance(o, decimal.Decimal):
                return float(o)
            return super(DecimalEncoder, self).default(o)
    HAS_PROVIDER = False

# Manual .env parser
def load_dotenv():
    # .env is located in the parent directory (the project root)
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, val = line.split('=', 1)
                    os.environ[key.strip()] = val.strip()

load_dotenv()

# Append parent dir for DB config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'database')))
try:
    # pyrefly: ignore [missing-import]
    from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, DATABASE_NAME
except ImportError:
    MYSQL_HOST     = os.environ["MYSQL_HOST"]
    MYSQL_USER     = os.environ["MYSQL_USER"]
    MYSQL_PASSWORD = os.environ["MYSQL_PASSWORD"]
    DATABASE_NAME  = os.environ["DATABASE_NAME"]

app = Flask(__name__)
# Allow CORS for dev environment
CORS(app)

if HAS_PROVIDER:
    app.json = CustomJSONProvider(app)
else:
    app.json_encoder = DecimalEncoder

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
client = Groq(api_key=GROQ_API_KEY)

def get_db_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=DATABASE_NAME,
        use_pure=True
    )
# Predefined 15 advanced SQL questions
SQL_QUESTIONS = [
    {
        "id": 1,
        "question": "Retrieve the top 5 pickup locations by total revenue where the average customer rating is greater than 4.0.",
        "query": "SELECT `Pickup Location`, SUM(`Booking Value`) AS `Total Revenue`, AVG(`Customer Rating`) AS `Avg Customer Rating` FROM uber_rides GROUP BY `Pickup Location` HAVING AVG(`Customer Rating`) > 4.0 ORDER BY `Total Revenue` DESC LIMIT 5;",
        "topics": ["GROUP BY", "ORDER BY", "HAVING", "Aggregate Functions", "LIMIT"]
    },
    {
        "id": 2,
        "question": "Find the monthly trend of completed bookings count and total revenue for each month.",
        "query": "SELECT DATE_FORMAT(`Date`, '%Y-%m') AS `Month`, COUNT(*) AS `Completed Bookings`, SUM(`Booking Value`) AS `Total Revenue` FROM uber_rides WHERE `Booking Status` = 'Completed' GROUP BY `Month` ORDER BY `Month`;",
        "topics": ["DATE_FORMAT", "GROUP BY", "ORDER BY", "Aggregate Functions"]
    },
    {
        "id": 3,
        "question": "Calculate the percentage of cancelled rides for each vehicle type.",
        "query": "SELECT `Vehicle Type`, COUNT(*) AS `Total Bookings`, SUM(CASE WHEN `Booking Status` LIKE 'Cancelled%' OR `Booking Status` = 'No Driver Found' THEN 1 ELSE 0 END) AS `Cancelled Bookings`, ROUND(SUM(CASE WHEN `Booking Status` LIKE 'Cancelled%' OR `Booking Status` = 'No Driver Found' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS `Cancellation Percentage` FROM uber_rides GROUP BY `Vehicle Type` ORDER BY `Cancellation Percentage` DESC;",
        "topics": ["CASE WHEN", "GROUP BY", "Aggregate Functions", "Arithmetic Operations"]
    },
    {
        "id": 4,
        "question": "Identify the customers who have booked more than 10 rides, along with their total completed rides, total spending, and average rating.",
        "query": "SELECT `Customer ID`, COUNT(*) AS `Total Rides`, SUM(CASE WHEN `Booking Status` = 'Completed' THEN 1 ELSE 0 END) AS `Completed Rides`, SUM(`Booking Value`) AS `Total Spending`, ROUND(AVG(`Customer Rating`), 2) AS `Avg Rating` FROM uber_rides GROUP BY `Customer ID` HAVING COUNT(*) > 10 ORDER BY `Total Spending` DESC LIMIT 10;",
        "topics": ["GROUP BY", "HAVING", "COUNT", "SUM", "AVG"]
    },
    # {
    #     "id": 5,
    #     "question": "Determine the top vehicle type by completed bookings for each pickup location using ROW_NUMBER().",
    #     "query": "WITH RankedVehicles AS (\n    SELECT `Pickup Location`, `Vehicle Type`, COUNT(*) AS `Completed Rides`,\n    ROW_NUMBER() OVER (PARTITION BY `Pickup Location` ORDER BY COUNT(*) DESC) as rn\n    FROM uber_rides\n    WHERE `Booking Status` = 'Completed'\n    GROUP BY `Pickup Location`, `Vehicle Type`\n)\nSELECT `Pickup Location`, `Vehicle Type`, `Completed Rides`\nFROM RankedVehicles\nWHERE rn = 1\nORDER BY `Completed Rides` DESC\nLIMIT 10;",
    #     "topics": ["CTE (Common Table Expression)", "WINDOW FUNCTION", "ROW_NUMBER()", "PARTITION BY", "GROUP BY"]
    # },
    {
        "id": 6,
        "question": "Find the pickup-to-drop location pairs that have the highest number of bookings, along with the average ride distance and total booking value.",
        "query": "SELECT `Pickup Location`, `Drop Location`, COUNT(*) AS `Total Bookings`, ROUND(AVG(`Ride Distance`), 2) AS `Avg Distance`, SUM(`Booking Value`) AS `Total Revenue` FROM uber_rides GROUP BY `Pickup Location`, `Drop Location` ORDER BY `Total Bookings` DESC LIMIT 5;",
        "topics": ["GROUP BY", "ORDER BY", "COUNT", "AVG", "SUM"]
    },
    {
        "id": 7,
        "question": "Find the distribution of cancellation reasons by drivers, listing the reasons and their percentages of total driver cancellations.",
        "query": "SELECT `Driver Cancellation Reason`, COUNT(*) AS `Cancellations`, ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM uber_rides WHERE `Booking Status` = 'Cancelled by Driver'), 2) AS `Percentage` FROM uber_rides WHERE `Booking Status` = 'Cancelled by Driver' AND `Driver Cancellation Reason` IS NOT NULL AND `Driver Cancellation Reason` != '' GROUP BY `Driver Cancellation Reason` ORDER BY `Cancellations` DESC;",
        "topics": ["GROUP BY", "CASE WHEN", "COUNT", "Subquery", "Arithmetic Operations"]
    },
    # {
    #     "id": 8,
    #     "question": "Retrieve the booking details for the longest ride distance for each vehicle type using DENSE_RANK().",
    #     "query": "WITH RankedRides AS (\n    SELECT `Booking ID`, `Vehicle Type`, `Ride Distance`, `Booking Value`, `Booking Status`,\n    DENSE_RANK() OVER (PARTITION BY `Vehicle Type` ORDER BY `Ride Distance` DESC) as rk\n    FROM uber_rides\n    WHERE `Ride Distance` IS NOT NULL\n)\nSELECT `Vehicle Type`, `Booking ID`, `Ride Distance`, `Booking Value`, `Booking Status`\nFROM RankedRides\nWHERE rk = 1\nORDER BY `Ride Distance` DESC;",
    #     "topics": ["CTE (Common Table Expression)", "WINDOW FUNCTION", "DENSE_RANK()", "PARTITION BY", "ORDER BY"]
    # },
    # {
    #     "id": 9,
    #     "question": "Calculate the running total of revenue day-by-day for Completed bookings in the month of May 2025.",
    #     "query": "SELECT `Date`, SUM(`Booking Value`) AS `Daily Revenue`, ROUND(SUM(SUM(`Booking Value`)) OVER (ORDER BY `Date`), 2) AS `Running Total` FROM uber_rides WHERE `Booking Status` = 'Completed' AND `Date` >= '2025-05-01' AND `Date` <= '2025-05-31' GROUP BY `Date` ORDER BY `Date`;",
    #     "topics": ["WINDOW FUNCTION", "SUM() OVER()", "GROUP BY", "DATE Filter", "ORDER BY"]
    # },
    {
        "id": 10,
        "question": "Find the average customer rating for each driver rating bucket (1.0-2.0, 2.0-3.0, 3.0-4.0, 4.0-5.0).",
        "query": "SELECT \n    CASE \n        WHEN `Driver Ratings` >= 1.0 AND `Driver Ratings` < 2.0 THEN '1.0 - 2.0'\n        WHEN `Driver Ratings` >= 2.0 AND `Driver Ratings` < 3.0 THEN '2.0 - 3.0'\n        WHEN `Driver Ratings` >= 3.0 AND `Driver Ratings` < 4.0 THEN '3.0 - 4.0'\n        WHEN `Driver Ratings` >= 4.0 AND `Driver Ratings` <= 5.0 THEN '4.0 - 5.0'\n        ELSE 'Unknown/No Rating'\n    END AS `Driver Rating Bucket`,\n    COUNT(*) AS `Ride Count`,\n    ROUND(AVG(`Customer Rating`), 2) AS `Avg Customer Rating`\nFROM uber_rides\nWHERE `Driver Ratings` IS NOT NULL AND `Customer Rating` IS NOT NULL\nGROUP BY `Driver Rating Bucket`\nORDER BY `Driver Rating Bucket`;",
        "topics": ["CASE WHEN", "GROUP BY", "ORDER BY", "AVG", "NULL Filters"]
    },
    {
        "id": 11,
        "question": "Identify the peak hours of the day (hour 0-23) with the highest booking count and revenue.",
        "query": "SELECT HOUR(`Time`) AS `Hour`, COUNT(*) AS `Total Bookings`, SUM(`Booking Value`) AS `Total Revenue` FROM uber_rides GROUP BY `Hour` ORDER BY `Total Bookings` DESC LIMIT 5;",
        "topics": ["HOUR() Function", "GROUP BY", "ORDER BY", "LIMIT"]
    },
    # {
    #     "id": 12,
    #     "question": "Calculate the month-over-month revenue growth percentage for completed rides.",
    #     "query": "WITH MonthlyRev AS (\n    SELECT DATE_FORMAT(`Date`, '%Y-%m') AS `Month`, SUM(`Booking Value`) AS `Revenue`\n    FROM uber_rides\n    WHERE `Booking Status` = 'Completed'\n    GROUP BY `Month`\n)\nSELECT `Month`, `Revenue`,\nLAG(`Revenue`, 1) OVER (ORDER BY `Month`) AS `Previous Month Revenue`,\nROUND((`Revenue` - LAG(`Revenue`, 1) OVER (ORDER BY `Month`)) * 100.0 / LAG(`Revenue`, 1) OVER (ORDER BY `Month`), 2) AS `Growth Percentage`\nFROM MonthlyRev\nORDER BY `Month`;",
    #     "topics": ["CTE (Common Table Expression)", "WINDOW FUNCTION", "LAG()", "Arithmetic Operations", "DATE_FORMAT"]
    # },
    {
        "id": 13,
        "question": "Retrieve the customer IDs who have cancelled rides more than 3 times, along with their average ratings.",
        "query": "SELECT `Customer ID`, COUNT(*) AS `CancellationsCount`, ROUND(AVG(`Customer Rating`), 2) AS `Avg Customer Rating` FROM uber_rides WHERE `Booking Status` LIKE 'Cancelled%' GROUP BY `Customer ID` HAVING COUNT(*) > 3 ORDER BY `CancellationsCount` DESC LIMIT 10;",
        "topics": ["GROUP BY", "HAVING", "COUNT", "LIKE operator", "LIMIT"]
    },
    {
        "id": 14,
        "question": "Find the average ride distance and average booking value for rides completed using each Payment Method.",
        "query": "SELECT `Payment Method`, COUNT(*) AS `Completed RidesCount`, ROUND(AVG(`Ride Distance`), 2) AS `Avg Ride Distance`, ROUND(AVG(`Booking Value`), 2) AS `Avg Booking Value` FROM uber_rides WHERE `Booking Status` = 'Completed' AND `Payment Method` IS NOT NULL AND `Payment Method` != '' GROUP BY `Payment Method` ORDER BY `Completed RidesCount` DESC;",
        "topics": ["GROUP BY", "AVG", "WHERE Filters", "ORDER BY"]
    },
    {
        "id": 15,
        "question": "Find the vehicle types that have a higher average ride distance than the overall average ride distance of all bookings.",
        "query": "SELECT `Vehicle Type`, ROUND(AVG(`Ride Distance`), 2) AS `Vehicle Avg Distance` FROM uber_rides GROUP BY `Vehicle Type` HAVING AVG(`Ride Distance`) > (SELECT AVG(`Ride Distance`) FROM uber_rides) ORDER BY `Vehicle Avg Distance` DESC;",
        "topics": ["SUBQUERY", "GROUP BY", "HAVING", "AVG"]
    }
]

# Helper to serialize cursor results to dict
def fetch_all_to_dict(cursor):
    columns = [col[0] for col in cursor.description]
    results = []
    for row in cursor.fetchall():
        row_dict = {}
        for i, val in enumerate(row):
            # Convert decimals/dates for JSON serialization
            if isinstance(val, decimal.Decimal):
                row_dict[columns[i]] = float(val)
            elif hasattr(val, 'isoformat'): # date/datetime
                row_dict[columns[i]] = val.isoformat()
            else:
                row_dict[columns[i]] = val
        results.append(row_dict)
    return results

@app.route('/metrics', methods=['GET'])
def get_metrics():
    vehicle_type = request.args.get('vehicle_type', None)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 1. Base Query filters
        where_clause = ""
        params = []
        if vehicle_type and vehicle_type.lower() != 'all':
            if vehicle_type.lower() == 'bike':
                # Combines Bike and eBike as done in the Power BI dashboard metrics
                where_clause = "WHERE `Vehicle Type` IN ('Bike', 'eBike')"
            else:
                where_clause = "WHERE `Vehicle Type` = %s"
                params.append(vehicle_type)
        
        # 2. Top-level Cards
        # - Completed Bookings
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause} {'AND' if where_clause else 'WHERE'} `Booking Status` = 'Completed'", params)
        completed_bookings = cursor.fetchone()[0]
        
        # - Lost Bookings
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause} {'AND' if where_clause else 'WHERE'} `Booking Status` != 'Completed'", params)
        lost_bookings = cursor.fetchone()[0]
        
        # - Revenue (Sum of all Booking Value where value exists)
        cursor.execute(f"SELECT SUM(`Booking Value`) FROM uber_rides {where_clause}", params)
        revenue = cursor.fetchone()[0] or 0.0
        
        # - Total Distance (Sum of all Ride Distance)
        cursor.execute(f"SELECT SUM(`Ride Distance`) FROM uber_rides {where_clause}", params)
        total_distance = cursor.fetchone()[0] or 0.0
        
        # - Avg Distance (Avg of all Ride Distance)
        cursor.execute(f"SELECT AVG(`Ride Distance`) FROM uber_rides {where_clause}", params)
        avg_distance = cursor.fetchone()[0] or 0.0

        # - Avg Customer Rating
        cursor.execute(f"SELECT AVG(`Customer Rating`) FROM uber_rides {where_clause}", params)
        avg_customer_rating = cursor.fetchone()[0] or 0.0
        
        # - Avg Driver Rating
        cursor.execute(f"SELECT AVG(`Driver Ratings`) FROM uber_rides {where_clause}", params)
        avg_driver_rating = cursor.fetchone()[0] or 0.0

        # - Top Pickup Location
        cursor.execute(f"SELECT `Pickup Location`, COUNT(*) as c FROM uber_rides {where_clause} GROUP BY `Pickup Location` ORDER BY c DESC LIMIT 1", params)
        top_pickup_res = cursor.fetchone()
        top_pickup = top_pickup_res[0] if top_pickup_res else "N/A"
        
        # - Top Drop Location
        cursor.execute(f"SELECT `Drop Location`, COUNT(*) as c FROM uber_rides {where_clause} GROUP BY `Drop Location` ORDER BY c DESC LIMIT 1", params)
        top_drop_res = cursor.fetchone()
        top_drop = top_drop_res[0] if top_drop_res else "N/A"

        # 3. Sidebar/Left Card ring metrics (percentages relative to the total bookings of selected vehicle)
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause}", params)
        total_vehicle_bookings = cursor.fetchone()[0] or 1 # avoid division by zero
        
        # - Completed %
        # Completed rides count for this specific filter has been fetched, but let's query directly to ensure consistency
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause} {'AND' if where_clause else 'WHERE'} `Booking Status` = 'Completed'", params)
        comp_count = cursor.fetchone()[0]
        completed_pct = (comp_count / total_vehicle_bookings) * 100
        
        # - Cancelled % (Cancelled by Customer + Cancelled by Driver + No Driver Found)
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause} {'AND' if where_clause else 'WHERE'} (`Booking Status` LIKE 'Cancelled%%' OR `Booking Status` = 'No Driver Found')", params)
        canc_count = cursor.fetchone()[0]
        cancelled_pct = (canc_count / total_vehicle_bookings) * 100
        
        # - Incomplete %
        cursor.execute(f"SELECT COUNT(*) FROM uber_rides {where_clause} {'AND' if where_clause else 'WHERE'} `Booking Status` = 'Incomplete'", params)
        inc_count = cursor.fetchone()[0]
        incomplete_pct = (inc_count / total_vehicle_bookings) * 100

        # 4. Revenue by Vehicle Type Chart data (grouped, combine Bike + eBike as 'Bike')
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN `Vehicle Type` IN ('Bike', 'eBike') THEN 'Bike' 
                    ELSE `Vehicle Type` 
                END as type, 
                SUM(`Booking Value`) as val 
            FROM uber_rides 
            GROUP BY type 
            ORDER BY val DESC
        """)
        revenue_by_vehicle = [{"vehicle_type": row[0], "revenue": float(row[1] or 0)} for row in cursor.fetchall()]

        # 5. Monthly trend of completed bookings count and total revenue (Jan - Dec)
        # We group by MONTH name or numerical month from parsed Date.
        # Since Date is a MySQL date type, we can group using DATE_FORMAT(Date, '%M') (Full Month Name) or MONTH(Date)
        cursor.execute(f"""
            SELECT 
                MONTH(`Date`) as m_num,
                DATE_FORMAT(`Date`, '%b') as m_name,
                COUNT(CASE WHEN `Booking Status` = 'Completed' THEN 1 END) as completed_rides,
                SUM(`Booking Value`) as revenue
            FROM uber_rides
            {where_clause}
            GROUP BY m_num, m_name
            ORDER BY m_num
        """, params)
        monthly_raw = cursor.fetchall()
        
        # Format monthly trend
        monthly_trend = []
        month_order = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        monthly_dict = {row[1]: {"completed_bookings": int(row[2]), "revenue": float(row[3] or 0)} for row in monthly_raw}
        
        # Ensure all 12 months exist in response
        for m in month_order:
            if m in monthly_dict:
                monthly_trend.append({
                    "month": m,
                    "completed_bookings": monthly_dict[m]["completed_bookings"],
                    "revenue": monthly_dict[m]["revenue"]
                })
            else:
                monthly_trend.append({
                    "month": m,
                    "completed_bookings": 0,
                    "revenue": 0.0
                })

        # Return comprehensive metrics payload
        payload = {
            "completed_bookings": completed_bookings,
            "lost_bookings": lost_bookings,
            "revenue": float(revenue),
            "total_distance": float(total_distance),
            "avg_distance": float(avg_distance),
            "avg_customer_rating": float(avg_customer_rating),
            "avg_driver_rating": float(avg_driver_rating),
            "top_pickup": top_pickup,
            "top_drop": top_drop,
            "completed_pct": float(completed_pct),
            "cancelled_pct": float(cancelled_pct),
            "incomplete_pct": float(incomplete_pct),
            "revenue_by_vehicle": revenue_by_vehicle,
            "monthly_trend": monthly_trend
        }
        
        return jsonify(payload)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/sql-questions', methods=['GET'])
def get_sql_questions():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        response_questions = []
        for q in SQL_QUESTIONS:
            cursor.execute(q["query"])
            results = fetch_all_to_dict(cursor)
            response_questions.append({
                "id": q["id"],
                "question": q["question"],
                "query": q["query"],
                "topics": q["topics"],
                "results": results
            })
        return jsonify(response_questions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# System prompt outlining database schemas and AI requirements
SYSTEM_PROMPT = """
You are an expert SQL translator and Uber data analyst. You have access to a MySQL database with a single table `uber_rides` that stores ride booking logs.

The schema of `uber_rides` is as follows:
- `Date` (DATE): date of the ride booking (ranges from Jan 2025 to Dec 2025)
- `Time` (VARCHAR): time of the ride (e.g. '06:39:39')
- `Booking ID` (VARCHAR): unique identifier for the booking
- `Booking Status` (VARCHAR): status of the booking. Values are:
  * 'Completed'
  * 'Cancelled by Customer'
  * 'Cancelled by Driver'
  * 'No Driver Found'
  * 'Incomplete'
- `Customer ID` (VARCHAR): unique identifier for customer
- `Vehicle Type` (VARCHAR): type of vehicle. Values are:
  * 'Auto'
  * 'Go Mini'
  * 'Go Sedan'
  * 'Bike'
  * 'Premier Sedan'
  * 'eBike'
  * 'Uber XL'
- `Pickup Location` (VARCHAR): pickup location
- `Drop Location` (VARCHAR): drop location
- `Cancelled Rides by Customer` (DECIMAL): contains 1.0 if cancelled by customer, otherwise NULL
- `Reason for cancelling by Customer` (TEXT): cancellation reason
- `Cancelled Rides by Driver` (DECIMAL): contains 1.0 if cancelled by driver, otherwise NULL
- `Driver Cancellation Reason` (TEXT): driver cancellation reason
- `Incomplete Rides` (DECIMAL): contains 1.0 if ride was incomplete, otherwise NULL
- `Incomplete Rides Reason` (TEXT): reason for incomplete ride
- `Booking Value` (DECIMAL): pricing in Indian Rupees
- `Ride Distance` (DECIMAL): ride distance in kilometers
- `Driver Ratings` (DECIMAL): rating given to driver (1.0 to 5.0)
- `Customer Rating` (DECIMAL): rating given to customer (1.0 to 5.0)
- `Payment Method` (VARCHAR): payment method ('UPI', 'Cash', 'Uber Wallet', 'Credit Card', 'Debit Card')

CRITICAL RULES:
1. Columns with spaces in their names MUST be enclosed in backticks, e.g., `Booking Status`, `Vehicle Type`, `Pickup Location`, `Booking Value`, etc.
2. If the user asks a question that can be answered by querying the database, you MUST set `is_sql` to true and provide the `query`.
   Example user queries:
   - "how many rides did customer C123 take?"
   - "what's the average booking value for Uber XL?"
   - "why are there less rides of sedan?" -> For trends/forensics, write a query that helps inspect this (e.g. comparing ride counts or cancellation reasons of Go Sedan/Premier Sedan vs other rides) so that we have actual data to analyze!
3. If the user asks a greeting or general off-topic question, set `is_sql` to false, `query` to null, and write a friendly message in `fallback_response`.
4. You must output ONLY a valid JSON object. Do not include markdown wraps or anything except the JSON.

Expected JSON Output Schema:
{
  "is_sql": boolean,
  "query": "SELECT ...",
  "explanation": "Brief description of what this query will find.",
  "fallback_response": "Conversational greeting or off-topic answer (null if is_sql is true)"
}
"""

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json or {}
    message = data.get('message', '')
    history = data.get('history', []) # list of {role: 'user'/'assistant', content: '...'}
    
    # Construct LLM context messages
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Append recent chat history
    for h in history[-5:]: # limit to last 5 messages for brevity
        messages.append({"role": "user" if h["role"] == "user" else "assistant", "content": h["content"]})
        
    messages.append({"role": "user", "content": message})
    
    try:
        # Pass 1: Ask Groq if we need SQL, and generate it if so
        chat_completion = client.chat.completions.create(
            messages=messages,
            model="llama-3.3-70b-versatile",
            temperature=0.1, # Keep it deterministic for SQL writing
            response_format={"type": "json_object"}
        )
        
        response_json = json.loads(chat_completion.choices[0].message.content)
        
        is_sql = response_json.get("is_sql", False)
        sql_query = response_json.get("query", None)
        explanation = response_json.get("explanation", "")
        fallback_response = response_json.get("fallback_response", "")
        
        if is_sql and sql_query:
            # Pass 2: Execute SQL query on MySQL
            conn = get_db_connection()
            cursor = conn.cursor()
            query_results = []
            error_msg = None
            try:
                # Limit execution rows to 50 for stability
                # If query already has limit, keep it, else we append a safe limit or trust the LLM
                cursor.execute(sql_query)
                query_results = fetch_all_to_dict(cursor)[:50]
            except Exception as sql_err:
                error_msg = str(sql_err)
            finally:
                cursor.close()
                conn.close()
                
            if error_msg:
                # If SQL fails, return the error details so the user sees the query error
                return jsonify({
                    "answer": f"I formulated a SQL query to answer your question, but encountered a database execution error: {error_msg}",
                    "query": sql_query,
                    "query_results": [],
                    "success": False,
                    "error": error_msg
                })
            
            # Pass 3: Send query results back to LLM to synthesize final natural language answer
            synthesis_prompt = f"""
            The user asked: "{message}"
            We executed the following SQL query to retrieve data:
            ```sql
            {sql_query}
            ```

            The database returned the following result rows:
            {json.dumps(query_results, indent=2)}

            Synthesize a clear, helpful, and natural language response that directly answers the user's question using the retrieved data. Avoid raw JSON dumps in your text; describe findings nicely. Keep it professional.
            """
            
            synthesis_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a professional Uber business analyst explaining insights derived from database queries."},
                    {"role": "user", "content": synthesis_prompt}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.3
            )
            
            final_answer = synthesis_completion.choices[0].message.content
            
            return jsonify({
                "answer": final_answer,
                "query": sql_query,
                "query_results": query_results,
                "success": True
            })
            
        else:
            # Non-SQL conversational response
            return jsonify({
                "answer": fallback_response,
                "query": None,
                "query_results": [],
                "success": True
            })
            
    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": str(e),
            "success": False
        }), 500

if __name__ == '__main__':
    # Flask runs on port 5001 (debug reloader disabled to avoid conflicts with node_modules file watch events)
    app.run(host='0.0.0.0', port=5001, debug=False)
