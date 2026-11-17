import os

os.makedirs('src/pages/training', exist_ok=True)

frontend_code = '''import { useState, useEffect } from 'react';
import axios from 'axios';

export default function TrainingDashboard() {
  const [activeTab, setActiveTab] = useState('catalog');
  const [courses, setCourses] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [employees, setEmployees] = useState([]);
  
  // Modals
  const [showCourseModal, setShowCourseModal] = useState(false);
  const [showSessionModal, setShowSessionModal] = useState(false);
  const [showEnrollModal, setShowEnrollModal] = useState(false);
  const [selectedSession, setSelectedSession] = useState(null);
  const [selectedEmps, setSelectedEmps] = useState([]);

  // Forms
  const [courseData, setCourseData] = useState({ title: '', description: '', is_mandatory: 'NO' });
  const [sessionData, setSessionData] = useState({ course_id: '', target_audience: 'Whole Company', trainer: '', venue_link: '', scheduled_date: '' });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    const resC = await axios.get('http://localhost:8000/api/training/courses');
    const resS = await axios.get('http://localhost:8000/api/training/sessions');
    const resE = await axios.get('http://localhost:8000/api/employees/');
    setCourses(resC.data);
    setSessions(resS.data);
    setEmployees(resE.data);
  };

  const handleCreateCourse = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/training/courses', courseData);
    setShowCourseModal(false);
    fetchData();
  };

  const handleScheduleSession = async (e) => {
    e.preventDefault();
    await axios.post('http://localhost:8000/api/training/sessions', sessionData);
    setShowSessionModal(false);
    fetchData();
  };

  const handleEnroll = async () => {
    if (selectedEmps.length === 0) return alert("Select at least one employee");
    await axios.post(`http://localhost:8000/api/training/sessions/${selectedSession.id}/enroll`, { employee_ids: selectedEmps });
    setShowEnrollModal(false);
    setSelectedEmps([]);
    alert(`Enrolled ${selectedEmps.length} employees. Notifications sent!`);
  };

  const toggleEmp = (id) => {
    if (selectedEmps.includes(id)) setSelectedEmps(selectedEmps.filter(x => x !== id));
    else setSelectedEmps([...selectedEmps, id]);
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div>
          <h1>Training & Development</h1>
          <p style={{ color: '#64748b' }}>Manage course catalog, schedule sessions, and enroll employees.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-primary" style={{ background: '#64748b' }} onClick={() => setShowCourseModal(true)}>+ Add Course</button>
          <button className="btn-primary" onClick={() => setShowSessionModal(true)}>+ Schedule Session</button>
        </div>
      </div>
      
      <div className="tabs">
        <button onClick={() => setActiveTab('catalog')} className={`tab ${activeTab === 'catalog' ? 'active' : ''}`}>Course Catalog</button>
        <button onClick={() => setActiveTab('sessions')} className={`tab ${activeTab === 'sessions' ? 'active' : ''}`}>Scheduled Sessions</button>
      </div>

      {activeTab === 'catalog' && (
        <div className="card">
          <table>
            <thead><tr><th>Course Title</th><th>Description</th><th>Mandatory?</th></tr></thead>
            <tbody>
              {courses.map(c => (
                <tr key={c.id}>
                  <td><strong>{c.title}</strong></td>
                  <td>{c.description}</td>
                  <td><span style={{ color: c.is_mandatory === 'YES' ? '#dc2626' : '#64748b', fontWeight: 'bold' }}>{c.is_mandatory}</span></td>
                </tr>
              ))}
              {courses.length === 0 && <tr><td colSpan="3" style={{ textAlign: 'center' }}>No courses in catalog yet.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {activeTab === 'sessions' && (
        <div className="card">
          <table>
            <thead><tr><th>Course</th><th>Date</th><th>Trainer</th><th>Audience</th><th>Action</th></tr></thead>
            <tbody>
              {sessions.map(s => (
                <tr key={s.id}>
                  <td><strong>{s.course_title}</strong></td>
                  <td>{s.date}</td>
                  <td>{s.trainer}</td>
                  <td>{s.audience}</td>
                  <td>
                    <button className="btn-primary" style={{ padding: '6px 12px', fontSize: '12px' }} onClick={() => { setSelectedSession(s); setShowEnrollModal(true); }}>
                      Enroll Employees
                    </button>
                  </td>
                </tr>
              ))}
              {sessions.length === 0 && <tr><td colSpan="5" style={{ textAlign: 'center' }}>No sessions scheduled.</td></tr>}
            </tbody>
          </table>
        </div>
      )}

      {/* Add Course Modal */}
      {showCourseModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '400px' }}>
            <h2>Add Course to Catalog</h2>
            <form onSubmit={handleCreateCourse}>
              <div className="input-group"><label>Course Title</label><input required value={courseData.title} onChange={e => setCourseData({...courseData, title: e.target.value})} /></div>
              <div className="input-group"><label>Description</label><textarea required value={courseData.description} onChange={e => setCourseData({...courseData, description: e.target.value})}></textarea></div>
              <div className="input-group"><label>Mandatory?</label><select value={courseData.is_mandatory} onChange={e => setCourseData({...courseData, is_mandatory: e.target.value})}><option value="NO">No</option><option value="YES">Yes</option></select></div>
              <button type="submit" className="btn-primary">Save Course</button>
            </form>
          </div>
        </div>
      )}

      {/* Schedule Session Modal */}
      {showSessionModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '500px' }}>
            <h2>Schedule Training Session</h2>
            <form onSubmit={handleScheduleSession}>
              <div className="input-group"><label>Select Course</label><select required value={sessionData.course_id} onChange={e => setSessionData({...sessionData, course_id: e.target.value})}><option value="">-- Select --</option>{courses.map(c => <option key={c.id} value={c.id}>{c.title}</option>)}</select></div>
              <div className="input-group"><label>Target Audience</label><select value={sessionData.target_audience} onChange={e => setSessionData({...sessionData, target_audience: e.target.value})}><option>Whole Company</option><option>Specific Department</option><option>HODs Only</option><option>Specific Individuals</option></select></div>
              <div className="input-group"><label>Trainer</label><input required value={sessionData.trainer} onChange={e => setSessionData({...sessionData, trainer: e.target.value})} /></div>
              <div className="input-group"><label>Venue / Link</label><input required value={sessionData.venue_link} onChange={e => setSessionData({...sessionData, venue_link: e.target.value})} /></div>
              <div className="input-group"><label>Date</label><input type="date" required value={sessionData.scheduled_date} onChange={e => setSessionData({...sessionData, scheduled_date: e.target.value})} /></div>
              <button type="submit" className="btn-primary">Schedule</button>
            </form>
          </div>
        </div>
      )}

      {/* Enroll Employees Modal */}
      {showEnrollModal && (
        <div className="modal-overlay" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
          <div className="card" style={{ width: '600px', maxHeight: '80vh', overflowY: 'auto' }}>
            <h2>Enroll in {selectedSession?.course_title}</h2>
            <p style={{ marginBottom: '15px' }}>Select employees to enroll. (Audience filter: {selectedSession?.audience})</p>
            <table style={{ marginBottom: '20px' }}>
              <thead><tr><th>Select</th><th>Name</th><th>Job Title</th></tr></thead>
              <tbody>
                {employees.map(e => (
                  <tr key={e.id}>
                    <td><input type="checkbox" checked={selectedEmps.includes(e.id)} onChange={() => toggleEmp(e.id)} /></td>
                    <td>{e.first_name} {e.last_name}</td>
                    <td>{e.job_title}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <button className="btn-primary" style={{ width: '100%' }} onClick={handleEnroll}>Enroll Selected ({selectedEmps.length}) & Notify</button>
          </div>
        </div>
      )}
    </div>
  );
}
'''

with open('src/pages/training/TrainingDashboard.jsx', 'w', encoding='utf-8') as f:
    f.write(frontend_code)
print("✅ Training Frontend created!")

# Update App.jsx and Layout.jsx
with open('src/App.jsx', 'r', encoding='utf-8') as f:
    app = f.read()
if 'TrainingDashboard' not in app:
    app = app.replace("import PerformanceDashboard from", "import TrainingDashboard from './pages/training/TrainingDashboard';\nimport PerformanceDashboard from")
    app = app.replace('<Route path="/performance"', '<Route path="/training" element={<ProtectedRoute><TrainingDashboard /></ProtectedRoute>} />\n<Route path="/performance"')
    with open('src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(app)
    print("✅ App.jsx updated.")

with open('src/components/Layout.jsx', 'r', encoding='utf-8') as f:
    layout = f.read()
if '/training' not in layout:
    layout = layout.replace("{ path: '/performance', label: 'Performance', icon: <Target size={20} />, hideForStaff: true },", "{ path: '/performance', label: 'Performance', icon: <Target size={20} />, hideForStaff: true },\n    { path: '/training', label: 'Training', icon: <BookOpen size={20} />, hideForStaff: true },")
    layout = layout.replace("import { LayoutDashboard", "import { BookOpen, LayoutDashboard")
    with open('src/components/Layout.jsx', 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Layout.jsx Sidebar updated.")
