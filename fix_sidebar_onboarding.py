layout_path = 'frontend/src/components/Layout.jsx'
with open(layout_path, 'r', encoding='utf-8') as f:
    layout = f.read()

if '/onboarding' not in layout:
    # Try to insert after Employees
    if "label: 'Employees' }" in layout:
        layout = layout.replace("label: 'Employees' }", "label: 'Employees' },\n    { path: '/onboarding', label: 'Onboarding' }")
    elif "Employees" in layout:
        layout = layout.replace("Employees", "Employees',\n    { path: '/onboarding', label: 'Onboarding")
        
    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Sidebar updated with Onboarding link!")
else:
    print("✅ Sidebar already had Onboarding.")
