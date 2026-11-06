login_code = '''import { useState } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.post('http://localhost:8000/api/auth/login', { email, password });
      localStorage.setItem('token', res.data.access_token);
      localStorage.setItem('role', res.data.role);
      localStorage.setItem('email', res.data.email);
      navigate('/');
    } catch (err) {
      setError('Invalid email or password.');
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>CHAP CHAP HRMS</h2>
        <p style={{ textAlign: 'center', marginBottom: '24px' }}>Sign in to your account</p>
        
        {error && <div style={{ padding: '10px', background: '#fee2e2', color: '#991b1b', marginBottom: '15px', borderRadius: '8px', textAlign: 'center' }}>{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="input-group">
            <label>Email Address</label>
            <input type="email" required value={email} onChange={e => setEmail(e.target.value)} placeholder="admin@chapchapafrica.com" />
          </div>
          <div className="input-group">
            <label>Password</label>
            <input type="password" required value={password} onChange={e => setPassword(e.target.value)} placeholder="admin123" />
          </div>
          <button type="submit" className="btn-primary" style={{ width: '100%' }}>Login</button>
        </form>
      </div>
    </div>
  );
}
'''

with open('frontend/src/pages/Login.jsx', 'w', encoding='utf-8') as f:
    f.write(login_code)
print("✅ Login page rewritten!")
