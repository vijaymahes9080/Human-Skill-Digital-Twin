import os
import uvicorn
from backend.app.core.database import engine

def main():
    db_file = "digital_twin.db"
    
    # Run seed script if DB is not initialized
    if not os.path.exists(db_file):
        print("Database file not found. Initializing and seeding...")
        from backend.app.seed import seed_db
        seed_db()
        
    print("Starting FastAPI Backend Server on http://localhost:8000 ...")
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
