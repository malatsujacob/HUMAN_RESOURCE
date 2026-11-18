from app.database import engine
from sqlalchemy import text

SQL = """
SELECT u.email, u.role, u.is_active,
       e.first_name, e.last_name,
       d.name AS dept
FROM users u
LEFT JOIN employees e ON e.id = u.employee_id
LEFT JOIN departments d ON d.id = e.department_id
WHERE u.role = 'HOD'
ORDER BY u.email
"""

with engine.connect() as c:
    rows = c.execute(text(SQL)).fetchall()
    if not rows:
        print("NO HOD USERS FOUND")
    else:
        for r in rows:
            print(f"{r.email:40} | active={r.is_active} | {r.first_name} {r.last_name} | dept={r.dept}")
