import os
from sqlalchemy import create_engine
import pandas as pd

# Database connection
DATABASE_URL = os.environ.get("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL)

# Query to retrieve data
query = "SELECT * FROM work_time;"  # Adjust the query as needed
df = pd.read_sql(query, engine)

# Save data to a CSV file (or process it as needed)
df.to_csv("daily_data_export.csv", index=False)
print("Data retrieved and saved successfully!")
