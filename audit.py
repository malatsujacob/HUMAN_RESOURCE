import os

modules = [
    "employees", "recruitment", "onboarding", "contracts",
    "attendance", "leave", "payroll", "performance",
    "training", "disciplinary", "exit", "analytics"
]

print("📊 CHAP CHAP HRMS - SYSTEM AUDIT 📊")
print("====================================")

for m in modules:
    backend_path = f"app/api/{m}.py"
    frontend_dir = f"frontend/src/pages/{m}"
    
    backend_exists = os.path.exists(backend_path)
    
    frontend_exists = False
    frontend_files = []
    if os.path.exists(frontend_dir):
        frontend_files = os.listdir(frontend_dir)
        if frontend_files:
            frontend_exists = True

    status = "✅" if (backend_exists and frontend_exists) else "❌"
    
    print(f"\n{status} MODULE: {m.upper()}")
    print(f"   Backend:  {'Found' if backend_exists else 'MISSING'}")
    print(f"   Frontend: {'Found ' + str(frontend_files) if frontend_exists else 'MISSING'}")

print("\n====================================")
print("AUDIT COMPLETE")
