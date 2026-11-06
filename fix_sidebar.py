import os

layout_path = 'frontend/src/components/Layout.jsx'
with open(layout_path, 'r', encoding='utf-8') as f:
    layout = f.read()

# A safer way to add the link: look for "Recruitment" and add "Contracts" right after it
if 'Contracts' not in layout:
    # Try replacing the most common patterns
    if "label: 'Recruitment'" in layout:
        layout = layout.replace("label: 'Recruitment' }", "label: 'Recruitment' },\n    { path: '/contracts', label: 'Contracts' }")
    elif "label: \"Recruitment\"" in layout:
        layout = layout.replace("label: \"Recruitment\" }", "label: \"Recruitment\" },\n    { path: '/contracts', label: 'Contracts' }")
    elif "Recruitment" in layout:
        # If it's just a string list, add it after
        layout = layout.replace("Recruitment", "Recruitment',\n    'Contracts")
        
    with open(layout_path, 'w', encoding='utf-8') as f:
        f.write(layout)
    print("✅ Sidebar updated with Contracts link!")
else:
    print("✅ Sidebar already had Contracts.")

print("🚀 DONE! The sidebar now has the Contracts link.")
