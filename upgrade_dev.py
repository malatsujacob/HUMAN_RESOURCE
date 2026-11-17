from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
email = "malatsujacob@gmail.com"

user = db.query(User).filter(User.email == email).first()

if user:
    user.role = "MANAGEMENT" # This gives you full developer/HR access
    db.commit()
    print(f"✅ Successfully upgraded {email} to MANAGEMENT role!")
else:
    print(f"❌ User {email} not found. Did you register with a different email?")
