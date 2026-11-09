import os

# 1. Add 'description' to RequisitionCreate
api_path = 'app/api/recruitment.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

if 'description: str' not in api:
    api = api.replace("min_experience: int", "min_experience: int\n    description: str = None")

# 2. Add the Bulk Email Endpoint
if '/send-email' not in api:
    api += '''

class BulkEmail(BaseModel):
    candidate_ids: list[str]
    email_type: str
    subject: str
    message: str

@router.post("/send-email")
def send_bulk_email(req: BulkEmail, db: Session = Depends(get_db)):
    for cid in req.candidate_ids:
        cand = db.query(Candidate).filter(Candidate.id == cid).first()
        if cand:
            print(f"[EMAIL MOCK] Sent to {cand.email}: {req.subject}")
            # Update status based on email type
            if req.email_type == "OFFER":
                cand.status = "OFFERED"
            elif req.email_type == "REJECTION":
                cand.status = "REJECTED"
                cand.rejection_reason = "Rejected via Email Campaign"
            elif req.email_type == "INTERVIEW":
                cand.status = "INTERVIEW_SCHEDULED"
    db.commit()
    return {"message": f"Emails sent to {len(req.candidate_ids)} candidates"}
'''
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("✅ Backend added Description field and Bulk Email endpoint!")

# 3. Add 'description' to Database (Safely)
from app.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE job_requisitions ADD COLUMN description TEXT;"))
        conn.commit()
        print("✅ Database updated with description column!")
    except:
        print("✅ Description column already exists.")
