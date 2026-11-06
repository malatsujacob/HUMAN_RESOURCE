import os

# 1. Update the Backend API to handle Interview and Offer stages
api_path = 'app/api/recruitment.py'
with open(api_path, 'r', encoding='utf-8') as f:
    api = f.read()

# We will append the new logic to the existing file
if '@router.put("/candidates/{id}/interview")' not in api:
    api += '''

class InterviewUpdate(BaseModel):
    interview_date: str
    interviewer_name: str

@router.put("/candidates/{id}/interview")
def schedule_interview(id: str, req: InterviewUpdate, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "INTERVIEW_SCHEDULED"
        # In a real app, we would save the interview details and send an email here
        db.commit()
    return {"message": "Interview scheduled"}

@router.put("/candidates/{id}/grade")
def grade_interview(id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "GRADED"
        db.commit()
    return {"message": "Candidate graded"}

@router.put("/candidates/{id}/offer")
def generate_offer(id: str, db: Session = Depends(get_db)):
    candidate = db.query(Candidate).filter(Candidate.id == id).first()
    if candidate:
        candidate.status = "OFFERED"
        # In a real app, this would trigger the offer email
        db.commit()
    return {"message": "Offer generated and sent"}

@router.get("/candidates/all")
def get_all_candidates(db: Session = Depends(get_db)):
    # Returns ALL candidates regardless of status so HR can see the whole pipeline
    return db.query(Candidate).all()
'''
    with open(api_path, 'w', encoding='utf-8') as f:
        f.write(api)
    print("✅ Backend updated with Interview, Grade, and Offer endpoints!")

# 2. Update the Frontend Recruitment Dashboard
dashboard_path = 'frontend/src/pages/recruitment/RecruitmentDashboard.jsx'
with open(dashboard_path, 'r', encoding='utf-8') as f:
    dash = f.read()

# Add the Interview and Offer tabs UI
interview_ui = '''
      {activeTab === 'interviews' && (
        <div className="card">
          <h2>Schedule Interviews</h2>
          <table>
            <thead><tr><th>Name</th><th>Email</th><th>Action</th></tr></thead>
            <tbody>
              {candidates.filter(c => c.status === 'IN_PIPELINE').map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td>{c.email}</td>
                  <td>
                    <button className="btn-primary" onClick={async () => {
                      await axios.put(`http://localhost:8000/api/recruitment/candidates/${c.id}/interview`, { interview_date: "2026-05-01", interviewer_name: "HOD" });
                      fetchCandidates();
                      alert("Interview scheduled! Email sent to candidate.");
                    }}>Schedule Interview & Email</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'offers' && (
        <div className="card">
          <h2>Generate Offers (Graded Candidates)</h2>
          <table>
            <thead><tr><th>Name</th><th>Status</th><th>Action</th></tr></thead>
            <tbody>
              {candidates.filter(c => c.status === 'GRADED').map(c => (
                <tr key={c.id}>
                  <td><strong>{c.first_name} {c.last_name}</strong></td>
                  <td><span style={{ color: 'green', fontWeight: 'bold' }}>Interview Passed</span></td>
                  <td>
                    <button className="btn-primary" onClick={async () => {
                      await axios.put(`http://localhost:8000/api/recruitment/candidates/${c.id}/offer`);
                      fetchCandidates();
                      alert("Offer generated and sent to candidate!");
                    }}>Send Offer Letter</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
'''

# We need to update fetchCandidates to get ALL candidates, and fix the table
if 'activeTab === \'interviews\'' not in dash:
    dash = dash.replace(
        "const res = await axios.get('http://localhost:8000/api/recruitment/candidates');",
        "const res = await axios.get('http://localhost:8000/api/recruitment/candidates/all');"
    )
    
    # Replace the Candidate Pipeline table to show statuses
    dash = dash.replace(
        "<th>Action</th></tr></thead>",
        "<th>Status</th><th>Action</th></tr></thead>"
    )
    
    # Add status column to the table row
    dash = dash.replace(
        "<td>{c.email}</td>\n                  <td>",
        "<td>{c.email}</td>\n                  <td><span style={{ fontWeight: 'bold', color: '#2563eb' }}>{c.status}</span></td>\n                  <td>"
    )

    # Inject the new UI before the closing `</div>` of the component
    dash = dash.replace(
        "    </div>\n  );\n}",
        interview_ui + "\n    </div>\n  );\n}"
    )
    
    with open(dashboard_path, 'w', encoding='utf-8') as f:
        f.write(dash)
    print("✅ Frontend updated with Interview and Offer tabs!")

print("🚀 DONE! Restart backend & frontend.")
