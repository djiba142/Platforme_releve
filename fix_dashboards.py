import glob

files = glob.glob(r'C:\Users\Djiba Kourouma\Desktop\platforme_releve\templates\dashboards\*.html')

replacements = [
    ('rgba(0, 195, 163, 0.1)', 'rgba(25, 118, 210, 0.08)'),
    ('rgba(0, 195, 163, 0.15)', 'rgba(25, 118, 210, 0.12)'),
    ('rgba(0, 195, 163, 0.3)', 'rgba(25, 118, 210, 0.25)'),
    ('rgba(0, 195, 163, 0.03)', 'rgba(25, 118, 210, 0.03)'),
    ('rgba(0,195,163,0.1)', 'rgba(25,118,210,0.08)'),
    ('rgba(0,195,163,0.15)', 'rgba(25,118,210,0.12)'),
    # Sidebar background - make it dark navy
    ('background: #1565C0;\n            position: fixed;', 'background: #0D2137;\n            position: fixed;'),
    # Sidebar border
    ('border-right: 3px solid #1976D2;', 'border-right: none;'),
    # Navbar (etudiant dashboard) - make dark navy
    ('background: #1565C0;\n            border-bottom: 3px solid #1976D2;', 'background: #0D2137;\n            border-bottom: none;'),
    # Welcome banner gradient
    ('linear-gradient(135deg, #1565C0, #1D3A5F)', 'linear-gradient(135deg, #1976D2, #1565C0)'),
]

for f in files:
    with open(f, 'r', encoding='utf-8') as fh:
        content = fh.read()
    
    for old, new in replacements:
        content = content.replace(old, new)
    
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(content)
    
    basename = f.split('\\')[-1]
    print('Fixed: ' + basename)
