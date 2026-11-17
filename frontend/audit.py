import os

print("📊 PROJECT AUDIT: FRONTEND PAGES")
print("=================================")

base_dir = 'src/pages'

if not os.path.exists(base_dir):
    print("❌ 'src/pages' folder not found. Are you in the frontend directory?")
else:
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(base_dir, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}📁 {os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            if f.endswith('.jsx') or f.endswith('.js'):
                print(f"{subindent}📄 {f}")
