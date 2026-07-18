with open('app/routers/public_quotes_final.py', 'r') as f:
    content = f.read()
with open('app/routers/public_quotes.py', 'w') as f:
    f.write(content)
print('Copied successfully')