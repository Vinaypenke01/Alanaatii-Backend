from decouple import config
try:
    db_url = config('DATABASE_URL')
    print(f"DATABASE_URL found: {db_url[:10]}...")
except Exception as e:
    print(f"Error: {e}")
