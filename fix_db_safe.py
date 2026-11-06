from app.database import engine
from sqlalchemy import text

print("Fixing database structure...")

with engine.connect() as conn:
    # 1. Recreate departments table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS departments (
            id UUID PRIMARY KEY,
            code VARCHAR(30) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL
        );
    """))
    conn.commit()
    
    # 2. Recreate job_requisitions table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS job_requisitions (
            id UUID PRIMARY KEY,
            department_id UUID REFERENCES departments(id),
            job_title VARCHAR(100),
            min_education VARCHAR(50),
            min_experience INT,
            status VARCHAR(30) DEFAULT 'PENDING_HR'
        );
    """))
    conn.commit()

    # 3. Recreate candidates table
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS candidates (
            id UUID PRIMARY KEY,
            requisition_id UUID REFERENCES job_requisitions(id),
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            email VARCHAR(100),
            phone_number VARCHAR(30),
            education_level VARCHAR(50),
            experience_years INT,
            cover_letter TEXT,
            status VARCHAR(30) DEFAULT 'IN_PIPELINE',
            interview_grade VARCHAR(30),
            rejection_reason TEXT,
            onboarding_requirements TEXT
        );
    """))
    conn.commit()

print("✅ Tables fixed!")

# 4. Re-run the API creation script safely (Only the backend part)
from app.api import recruitment
# This reads the file but doesn't try to drop tables
import importlib
importlib.reload(recruitment)

print("✅ Backend API updated safely!")
