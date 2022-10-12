import os

BASE_PATH = r'C:\Users\Gabe\Documents\GitHub\dnd_tools\scripts\dictionaries'

files = os.listdir(BASE_PATH)
filenames = [file.split(r'\\')[-1] for file in files]
print(f'Processing files: {filenames}')
for file in files:
    try:
        filepath = os.path.join(BASE_PATH, file)
        f = open(filepath, 'r')
        text = f.read()
        f.close()
        f = open(filepath, 'w', encoding='utf-8')
        f.write(text)
        f.close()
    except:
        print(f'Could not process "{file}".')
