import glob
import re

files = glob.glob(r'C:\Users\Djiba Kourouma\Desktop\platforme_releve\*\templates\*\*.html')
pattern = re.compile(r'<a href=\"{% url \'import_csv\' %}\".*?</a>', re.DOTALL)

for f in files:
    with open(f, 'r', encoding='utf-8') as file:
        content = file.read()
    
    if '{% url \'import_csv\' %}' in content:
        new_content = pattern.sub('', content)
        with open(f, 'w', encoding='utf-8') as file:
            file.write(new_content)
        print('Fixed: ' + f)
