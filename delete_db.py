
import os

db_path = "C:/Users/zamor/UltiBotInversiones/ultibot_local.db"
if os.path.exists(db_path):
    os.remove(db_path)
    print(f"Successfully deleted {db_path}")
else:
    print(f"{db_path} does not exist.")
