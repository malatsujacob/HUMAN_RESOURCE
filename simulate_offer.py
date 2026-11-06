from app.database import SessionLocal
from app.models.recruitment import Candidate

db = SessionLocal()
c = db.query(Candidate).first()

if c:
    c.status = 'OFFERED'
    db.commit()
    print(f"✅ Success: {c.first_name} is now marked as OFFERED.")
else:
    print("❌ No candidates found in the database. Go to /apply and submit one first.")
