from app.database import SessionLocal, get_password_hash
from app.models.user import User

db = SessionLocal()
email = "malatsujacob@gmail.com"
password = "Jack.02.+ma"

user = db.query(User).filter(User.email == email).first()

if user:
    user.password_hash = get_password_hash(password)
    user.role = "MANAGEMENT"
    db.commit()
    print(f"✅ Password for {email} has been reset and hashed correctly.")
else:
    print(f"❌ User {email} does not exist in the database.")
    
db.close()
