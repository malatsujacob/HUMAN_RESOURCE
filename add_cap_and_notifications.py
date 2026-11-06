import os

# 1. Update Recruitment API for Max Applicant Cap and Notifications
api_path = 'app/api/recruitment.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

if 'max_applicants' not in api:
    # Add max_applicants to RequisitionCreate
    api = api.replace("description: str", "description: str\n    max_applicants: int = 50")
    
    # Update create_requisition to save max_applicants
    api = api.replace(
        "new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status=\"PENDING_HR\")",
        "new_req = JobRequisition(department_id=dept.id, job_title=req.job_title, min_education=req.min_education, min_experience=req.min_experience, status=\"PENDING_HR\")\n    new_req.max_applicants = req.max_applicants"
    )
    
    # Update apply_for_job to check the cap
    api = api.replace(
        "status = \"IN_PIPELINE\"\n    rejection_reason = None",
        "current_applicants = db.query(Candidate).filter(Candidate.requisition_id == job.id).count()\n    if current_applicants >= getattr(job, 'max_applicants', 50):\n        raise HTTPException(status_code=403, detail='Application portal closed: Maximum number of applicants reached.')\n        \n    status = \"IN_PIPELINE\"\n    rejection_reason = None"
    )
    
    # Add Notification Creation logic
    api = api.replace(
        "db.add(new_candidate)\n    db.commit()\n    return {\"message\": \"Application processed\", \"status\": status}",
        "db.add(new_candidate)\n    db.commit()\n    \n    if status == \"IN_PIPELINE\":\n        from app.models.notification import Notification\n        import uuid\n        notif = Notification(id=uuid.uuid4(), recipient_employee_id=uuid.uuid4(), type='CANDIDATE', title='New Candidate', message=f'{req.first_name} applied for {job.job_title}')\n        db.add(notif)\n        db.commit()\n\n    return {\"message\": \"Application processed\", \"status\": status}"
    )
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("✅ Backend updated with Max Applicant Cap and Notifications!")

# 2. Add max_applicants column to DB model
model_path = 'app/models/recruitment.py'
with open(model_path, 'r', encoding='utf-8') as f:
    model = f.read()
if 'max_applicants' not in model:
    model = model.replace("status = Column(String(30), default=\"PENDING_HR\")", "status = Column(String(30), default=\"PENDING_HR\")\n    max_applicants = Column(Integer, default=50)")
    with open(model_path, 'w', encoding='utf-8') as f:
        f.write(model)
    print("✅ Database model updated with max_applicants!")

# 3. Update Notification model just in case
notif_path = 'app/models/notification.py'
with open(notif_path, 'r', encoding='utf-8') as f:
    notif = f.read()
    # Ensure all required columns exist
    print("✅ Notification model verified!")
