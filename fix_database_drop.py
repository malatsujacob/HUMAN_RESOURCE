from app.database import engine
from sqlalchemy import text

# 1. Forcefully drop the tables with CASCADE to ignore foreign key links
print("Wiping old tables...")
with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS candidates CASCADE;"))
    conn.execute(text("DROP TABLE IF EXISTS job_requisitions CASCADE;"))
    conn.commit()

# 2. Recreate them
from app.models.recruitment import Candidate, JobRequisition
JobRequisition.__table__.create(bind=engine, checkfirst=True)
Candidate.__table__.create(bind=engine, checkfirst=True)

print("✅ Database tables successfully rebuilt!")

# 3. Re-run the API creation (The code you already have is safe, we just need to execute it)
exec(open('perfect_recruitment_all.py', encoding='utf-8').read().split("# Rebuild Database tables")[0])
print("✅ Backend API updated successfully!")
