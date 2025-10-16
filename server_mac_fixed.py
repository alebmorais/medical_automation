#!/usr/bin/env python3
"""
A small, separate server file for quick smoke testing that won't modify the
original `server_mac.py`. It reads the same 'database' file in the repo root.
"""
import json
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse

PORT = 8081
DATA_PATH = os.path.join(os.path.dirname(__file__), 'database')

class SimpleParser:
    def __init__(self, path):
        self.path = path
    def parse(self):
        if not os.path.exists(self.path):
            return {"categories":{}, "phrases": []}
        cats = {}
        phrases = []
        cur_cat = None
        cur_sub = None
        cur_lines = []
        pid = 1
        import re
        with open(self.path, 'r', encoding='utf-8') as f:
            for raw in f:
                s = raw.strip()
                if not s:
                    if cur_lines and cur_cat and cur_sub:
                        phrases.append({"id": pid, "nome": f"{cur_sub}", "conteudo": '\n'.join(cur_lines), "categoria_principal": cur_cat, "subcategoria": cur_sub})
                        pid += 1
                        cur_lines = []
                    continue
                m = re.match(r'^CATEGORIA:\s*(.*)', s, re.IGNORECASE)
                if m:
                    cur_cat = m.group(1).strip(); cur_sub = None; continue
                m = re.match(r'^SUBCATEGORIA:\s*(.*)', s, re.IGNORECASE)
                if m and cur_cat:
                    cur_sub = m.group(1).strip(); cats.setdefault(cur_cat, []).append(cur_sub); continue
                m = re.match(r'^\d+\.\s*(.*)', s)
                if m and cur_cat and cur_sub:
                    cur_lines.append(m.group(1).strip()); continue
                if cur_lines:
                    cur_lines.append(raw.rstrip('\n'))
        return {"categories": cats, "phrases": phrases}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        p = urllib.parse.urlparse(self.path)
        if p.path == '/':
            data = SimpleParser(DATA_PATH).parse()
            html = '<html><body><h1>OK</h1><pre>' + json.dumps(data, ensure_ascii=False, indent=2) + '</pre></body></html>'
            self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(html.encode('utf-8')); return
        if p.path.startswith('/api/'):
            data = SimpleParser(DATA_PATH).parse()
            if p.path == '/api/categorias':
                out = list(data['categories'].keys())
            elif p.path.startswith('/api/subcategorias'):
                parts = p.path.strip('/').split('/')
                cat = urllib.parse.unquote('/'.join(parts[2:])) if len(parts) > 2 else None
                out = data['categories'].get(cat, []) if cat else []
            elif p.path.startswith('/api/frases'):
                qs = urllib.parse.parse_qs(p.query)
                cat = qs.get('categoria', [None])[0]
                sub = qs.get('subcategoria', [None])[0]
                frases = data['phrases']
                if cat: frases = [f for f in frases if f['categoria_principal']==cat]
                if sub: frases = [f for f in frases if f['subcategoria']==sub]
                out = frases
            else:
                self.send_error(404); return
            self.send_response(200); self.send_header('Content-Type','application/json; charset=utf-8'); self.end_headers(); self.wfile.write(json.dumps(out, ensure_ascii=False, indent=2).encode('utf-8'))
            return
        self.send_error(404)

if __name__ == '__main__':
    httpd = HTTPServer(('', PORT), Handler)
    print(f'Serving test server on http://localhost:{PORT} (reads {DATA_PATH})')
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\nStopped')
    finally:
        httpd.server_close()
