from weasyprint import HTML, CSS

html = HTML(string='<h1>Test</h1>')
css = CSS(string='@page { @bottom-center { content: "test"; } }')
pdf = html.write_pdf(stylesheets=[css])
print(len(pdf))
