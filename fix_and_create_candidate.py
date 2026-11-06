import os

# 1. Add phone_number to the Candidate Model
model_path = 'app/models/recruitment.py'
with open(model_path, 'r', encoding='utf-8') as f:
    model = f.read()

if 'phone_number' not in model:
    model = model.replace('email = Column(String(100))', 'email = Column(String(100))\n    phone_number = Column(String(30))')
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(model)
    print("✅ Backend Model updated with phone_number!")

# 2. Drop and recreate the candidates table so it picks up the new column
from app.database import engine
from app.models.recruitment import Candidate
Candidate.__table__.drop(bind=engine, checkfirst=True)
Candidate.__table__.create(bind=engine, checkfirst=True)
print("✅ Database table updated!")

# 3. Run the candidate creation script again
from app.database import SessionLocal
from app.models.recruitment import JobRequisition
from app.models.department import Department
import uuid

db = SessionLocal()
req = db.query(JobRequisition).first()
if not req:
    dept = db.query(Department).filter(Department.code == "TECH").first()
    req = JobRequisition(id=uuid.uuid4(), department_id=dept.id, job_title="Software Engineer", min_education="Bachelor", min_experience=2, status="APPROVED")
    db.add(req)
    db.commit()

new_cand = Candidate(
    id=uuid.uuid4(), requisition_id=req.id, first_name="Alice", last_name="Kamya",
    email="alice.kamya@test.com", phone_number="0700111222", education_level="Bachelor", experience_years=5,
    cover_letter="I am a great engineer.", status="OFFERED"
)
db.add(new_cand)
db.commit()
print(f"✅ Successfully created candidate: {new_cand.first_name} with OFFERED status.")
