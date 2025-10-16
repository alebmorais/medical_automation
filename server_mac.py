#!/usr/bin/env python3
"""
Servidor de Automação Médica (Somente Frases)
Versão alternativa sem snippets
"""
import sqlite3
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import traceback

class MedicalAutomationServer:
    def __init__(self, db_path=None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = self.resolve_database_path(db_path)
        self.verify_database()

    def resolve_database_path(self, preferred_path):
        candidates = []
        if preferred_path:
            candidates.append(preferred_path)
        env_candidates = [
            os.environ.get("AUTOMATION_DB_PATH"),
            os.environ.get("DB_PATH"),
        ]
        candidates.extend(filter(None, env_candidates))
        script_dir = self.base_dir
        parent_dir = os.path.dirname(script_dir)
        default_locations = [
            os.path.join(script_dir, "automation.db"),
            os.path.join(script_dir, "database", "automation.db"),
            os.path.join(parent_dir, "automation.db"),
            os.path.join(parent_dir, "database", "automation.db"),
        ]
        candidates.extend(default_locations)
        normalized = []
        seen = set()
        for path in candidates:
            if not path:
                continue
            full_path = os.path.abspath(os.path.expanduser(path))
            if full_path not in seen:
                normalized.append(full_path)
                seen.add(full_path)
        if not normalized:
            return os.path.join(script_dir, "automation.db")
        for path in normalized:
            if os.path.exists(path):
                return path
        return normalized[0]

    def verify_database(self, rebuilt=False):
        if not os.path.exists(self.db_path):
            print(f"AVISO: Banco de dados não encontrado em {self.db_path}")
            print("Tentando criar automaticamente a partir do arquivo SQL de referência...")
            if self.bootstrap_database(overwrite=False):
                self.verify_database(rebuilt=True)
                return
            print("ERRO: Não foi possível localizar ou criar o banco de dados.")
            sys.exit(1)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT COUNT(*) FROM frases")
            count = cursor.fetchone()[0]
            conn.close()
            if count == 0:
                if not rebuilt and self.bootstrap_database(overwrite=True):
                    self.verify_database(rebuilt=True)
                    return
                print("AVISO: Banco de dados vazio")
            else:
                print(f"✓ Banco de dados OK: {count} frases encontradas")
        except Exception as e:
            print(f"ERRO no banco de dados: {e}")
            if not rebuilt and self.bootstrap_database(overwrite=True):
                self.verify_database(rebuilt=True)
                return
            sys.exit(1)

    def bootstrap_database(self, overwrite=False):
        sql_candidates = self.find_sql_candidates()
        if not sql_candidates:
            print("Nenhum arquivo SQL de referência encontrado para criar o banco de dados.")
            return False
        target_dir = os.path.dirname(self.db_path)
        if target_dir and not os.path.exists(target_dir):
            try:
                os.makedirs(target_dir, exist_ok=True)
            except OSError as err:
                print(f"Erro ao criar diretório do banco de dados: {err}")
                return False
        if overwrite and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError as err:
                print(f"Não foi possível remover o banco de dados antigo: {err}")
                return False
        for sql_path in sql_candidates:
            try:
                with open(sql_path, "r", encoding="utf-8") as sql_file:
                    script = sql_file.read()
                with sqlite3.connect(self.db_path) as conn:
                    conn.executescript(script)
                print(f"✓ Banco de dados criado em {self.db_path} a partir de {sql_path}")
                return True
            except Exception as err:
                print(f"Falha ao criar banco de dados a partir de {sql_path}: {err}")
        return False

    def find_sql_candidates(self):
        candidates = []
        locations = [self.base_dir, os.path.dirname(self.base_dir)]
        file_names = [
            "SQL2.sql",
            "database.sql",
            "automation.sql",
        ]
        for location in locations:
            if not location:
                continue
            for name in file_names:
                candidates.append(os.path.join(location, name))
            candidates.append(os.path.join(location, "database", "SQL_File.sql"))
            candidates.append(os.path.join(location, "database", "SQL_File"))
            candidates.append(os.path.join(location, "database", "automation.sql"))
        existing = []
        seen = set()
        for path in candidates:
            full_path = os.path.abspath(path)
            if full_path in seen:
                continue
            seen.add(full_path)
            if os.path.exists(full_path):
                existing.append(full_path)
        return existing

    def get_categorias_principais(self):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute("SELECT DISTINCT categoria_principal FROM frases")
            categorias = [row[0] for row in cursor]
            conn.close()
            return categorias
        except Exception as e:
            print(f"Erro ao buscar categorias: {e}")
            return []

    def get_subcategorias(self, categoria_principal):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.execute(
                "SELECT DISTINCT subcategoria FROM frases WHERE categoria_principal = ? ORDER BY subcategoria",
                (categoria_principal,)
            )
            subcategorias = [row[0] for row in cursor]
            conn.close()
            return subcategorias
        except Exception as e:
            print(f"Erro ao buscar subcategorias: {e}")
            return []

    def get_frases(self, categoria_principal=None, subcategoria=None):
        try:
            conn = sqlite3.connect(self.db_path)
            if categoria_principal and subcategoria:
                cursor = conn.execute(
                    "SELECT * FROM frases WHERE categoria_principal = ? AND subcategoria = ? ORDER BY ordem",
                    (categoria_principal, subcategoria)
                )
            elif categoria_principal:
                cursor = conn.execute(
                    "SELECT * FROM frases WHERE categoria_principal = ? ORDER BY subcategoria, ordem",
                    (categoria_principal,)
                )
            else:
                cursor = conn.execute("SELECT * FROM frases ORDER BY categoria_principal, subcategoria, ordem")
            frases = []
            for row in cursor:
                conteudo = row[2]
                if isinstance(conteudo, str):
                    conteudo = conteudo.replace("\\n", "\n")
                frases.append({
                    'id': row[0],
                    'nome': row[1],
                    'conteudo': conteudo,
                    'categoria_principal': row[3],
                    'subcategoria': row[4],
                    'ordem': row[5]
                })
            conn.close()
            return frases
        except Exception as e:
            print(f"Erro ao buscar frases: {e}")
            return []

class WebRequestHandler(BaseHTTPRequestHandler):
    def __init__(self, *args, automation_server=None, **kwargs):
        self.automation_server = automation_server
        super().__init__(*args, **kwargs)

    def log_message(self, format, *args):
        pass

    def do_GET(self):
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path

            # API routes
            if path.startswith('/api/'):
                path_parts = path.strip('/').split('/')
                
                if len(path_parts) == 2 and path_parts[1] == 'categorias':
                    categorias = self.automation_server.get_categorias_principais()
                    self.send_json_response(categorias)
                    return

                if len(path_parts) >= 3 and path_parts[1] == 'subcategorias':
                    categoria = urllib.parse.unquote('/'.join(path_parts[2:]))
                    if not categoria:
                        self.send_error(400, "Categoria não especificada")
                        return
                    subcategorias = self.automation_server.get_subcategorias(categoria)
                    self.send_json_response(subcategorias)
                    return

                if len(path_parts) >= 2 and path_parts[1] == 'frases':
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    categoria = query_params.get('categoria', [None])[0]
                    subcategoria = query_params.get('subcategoria', [None])[0]
                    frases = self.automation_server.get_frases(categoria, subcategoria)
                    self.send_json_response(frases)
                    return

            # Root path for HTML interface
            if path == '/':
                self.send_medical_interface()
                return

            self.send_error(404, "Página não encontrada")
        except Exception as e:
            print(f"Erro na requisição {self.path}: {e}")
            traceback.print_exc()
            self.send_error(500, "Erro interno do servidor")

    def send_json_response(self, data):
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            json_data = json.dumps(data, ensure_ascii=False, indent=2)
            self.wfile.write(json_data.encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar JSON: {e}")
            self.send_error(500, "Erro ao processar dados")

    def send_medical_interface(self):
        html_content = "<html><body><h1>Servidor de Automação Médica (Somente Frases)</h1><p>API disponível em /api/categorias, /api/subcategorias/&lt;categoria&gt;, /api/frases</p></body></html>"
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar HTML: {e}")
            self.send_error(500, "Erro ao carregar interface")

def run_medical_server(db_path=None):
    automation_server = MedicalAutomationServer(db_path=db_path)
    def handler(*args, **kwargs):
        WebRequestHandler(*args, automation_server=automation_server, **kwargs)
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, handler)
    print(f"✓ Servidor de frases médicas rodando em http://localhost:8080")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_medical_server()
