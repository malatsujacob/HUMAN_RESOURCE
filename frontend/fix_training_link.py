import os

# 1. Verify we are in the right place
if not os.path.exists('src/App.jsx'):
    print("❌ ERROR: You must run this from the FRONTEND terminal!")
else:
    # 2. Update App.jsx
    with open('src/App.jsx', 'r', encoding='utf-8') as f:
        app = f.read()
    
    if 'TrainingDashboard' not in app:
        app = app.replace("import PerformanceDashboard from", "import TrainingDashboard from './pages/training/TrainingDashboard';\nimport PerformanceDashboard from")
        app = app.replace('<Route path="/performance"', '<Route path="/training" element={<ProtectedRoute><TrainingDashboard /></ProtectedRoute>} />\n<Route path="/performance"')
        with open('src/App.jsx', 'w', encoding='utf-8') as f:
            f.write(app)
        print("✅ App.jsx updated with Training route!")

    # 3. Update Layout.jsx
    with open('src/components/Layout.jsx', 'r', encoding='utf-8') as f:
        layout = f.read()
    
    if '/training' not in layout:
        # Add the link after Performance
        if "path: '/performance'" in layout:
            layout = layout.replace(
                "{ path: '/performance', label: 'Performance', icon: <Target size={20} />, hideForStaff: true },",
                "{ path: '/performance', label: 'Performance', icon: <Target size={20} />, hideForStaff: true },\n    { path: '/training', label: 'Training', icon: <BookOpen size={20} />, hideForStaff: true },"
            )
        else:
            # Fallback if Performance line doesn't match exactly
            layout = layout.replace(
                "const navItems = [",
                "const navItems = [\n    { path: '/training', label: 'Training', icon: <BookOpen size={20} />, hideForStaff: true },"
            )
            
        # Ensure the BookOpen icon is imported
        if "BookOpen" not in layout:
            layout = layout.replace("import { LayoutDashboard", "import { BookOpen, LayoutDashboard")
            
        with open('src/components/Layout.jsx', 'w', encoding='utf-8') as f:
            f.write(layout)
        print("✅ Layout.jsx sidebar updated with Training link!")
