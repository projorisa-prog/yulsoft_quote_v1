with open('app/models/quote.py', 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
start_idx = 0
for i, line in enumerate(lines):
    if line.startswith('import enum'):
        start_idx = i
        break

new_content = '\n'.join(lines[start_idx:])

with open('app/models/quote.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('Fixed quote.py')