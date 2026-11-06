from app.database import SessionLocal
from app.models.recruitment import Candidate, JobRequisition
from app.models.department import Department
import uuid

db = SessionLocal()

# 1. Find a requisition (or create one if none exist)
req = db.query(JobRequisition).first()
if not req:
    dept = db.query(Department).filter(Department.code == "TECH").first()
    req = JobRequisition(
        id=uuid.uuid4(),
        department_id=dept.id,
        job_title="Software Engineer",
        min_education="Bachelor",
        min_experience=2,
        status="APPROVED"
    )
    db.add(req)
    db.commit()

# 2. Create the candidate with OFFERED status
new_cand = Candidate(
    id=uuid.uuid4(),
    requisition_id=req.id,
    first_name="Alice",
    last_name="Kamya",
    email="alice.kamya@test.com",
    phone_number="0700111222",
    education_level="Bachelor",
    experience_years=5,
    cover_letter="I am a great engineer.",
    status="OFFERED"
)
db.add(new_cand)
db.commit()

print(f"✅ Successfully created candidate: {new_cand.first_name} with OFFERED status.")
