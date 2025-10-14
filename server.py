#!/usr/bin/env python3
"""
Servidor de Automação Médica
Versão Beta
"""
import sqlite3
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import traceback
import datetime
from threading import Thread

# Flask imports for snippet server
from flask import Flask, jsonify, request

# --- Snippet Server (Flask App on port 5000) ---
snippet_app = Flask(__name__)
SNIPPET_DATABASE = 'snippets.db'

def get_snippet_db_connection():
    """Create a database connection for snippets."""
    conn = sqlite3.connect(SNIPPET_DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_snippet_db():
    """Initialize the snippets database and create tables if they don't exist."""
    with snippet_app.app_context():
        conn = get_snippet_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS snippets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                abbreviation TEXT NOT NULL UNIQUE,
                phrase TEXT NOT NULL,
                usage_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
        print("✓ Banco de dados de snippets inicializado.")

@snippet_app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for snippet server."""
    return jsonify({"status": "healthy", "timestamp": datetime.datetime.now().isoformat()})

@snippet_app.route('/snippets', methods=['GET'])
def get_snippets():
    """Get all snippets for the expander client."""
    conn = get_snippet_db_connection()
    snippets = conn.execute('SELECT abbreviation, phrase FROM snippets').fetchall()
    conn.close()
    return jsonify({row['abbreviation']: row['phrase'] for row in snippets})

@snippet_app.route('/snippets/all', methods=['GET'])
def get_all_snippets_full():
    """Get all snippets with full details for the manager GUI."""
    conn = get_snippet_db_connection()
    snippets = conn.execute('SELECT id, abbreviation, phrase, usage_count FROM snippets').fetchall()
    conn.close()
    return jsonify([dict(row) for row in snippets])

@snippet_app.route('/snippets', methods=['POST'])
def create_snippet():
    """Create a new snippet."""
    data = request.get_json()
    if not data or 'abbreviation' not in data or 'phrase' not in data:
        return jsonify({"error": "Missing abbreviation or phrase"}), 400

    conn = get_snippet_db_connection()
    try:
        conn.execute('INSERT INTO snippets (abbreviation, phrase) VALUES (?, ?)', (data['abbreviation'], data['phrase']))
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Abbreviation already exists"}), 409
    finally:
        conn.close()
    return jsonify({"message": "Snippet created successfully"}), 201

@snippet_app.route('/snippets/<string:abbreviation>', methods=['PUT'])
def update_snippet(abbreviation):
    """Update an existing snippet."""
    data = request.get_json()
    if not data or 'phrase' not in data:
        return jsonify({"error": "Missing phrase"}), 400

    conn = get_snippet_db_connection()
    conn.execute('UPDATE snippets SET phrase = ? WHERE abbreviation = ?', (data['phrase'], abbreviation))
    conn.commit()
    conn.close()
    return jsonify({"message": "Snippet updated successfully"})

@snippet_app.route('/snippets/<string:abbreviation>', methods=['DELETE'])
def delete_snippet(abbreviation):
    """Delete a snippet."""
    conn = get_snippet_db_connection()
    conn.execute('DELETE FROM snippets WHERE abbreviation = ?', (abbreviation,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Snippet deleted successfully"})

# --- End of Snippet Server ---


class MedicalAutomationServer:
    def __init__(self, db_path=None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.db_path = self.resolve_database_path(db_path)
        self.verify_database()

    def resolve_database_path(self, preferred_path):
        """Determina o caminho do banco considerando múltiplas possibilidades."""
        candidates = []

        # Ordem de preferência: argumento explícito, variáveis de ambiente e caminhos padrões.
        if preferred_path:
            candidates.append(preferred_path)

        env_candidates = [
            os.environ.get("AUTOMATION_DB_PATH"),
            os.environ.get("DB_PATH"),
        ]
        candidates.extend(filter(None, env_candidates))

        # Caminhos relativos ao arquivo atual e ao diretório pai (para execução fora do repo).
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

        # Nenhum caminho existente encontrado: usar o primeiro candidato para tentar criar o banco.
        return normalized[0]

    def verify_database(self, rebuilt=False):
        """Verificar se banco de dados existe e tem dados"""
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
        """Cria o banco a partir de um arquivo SQL se disponível."""
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
        """Retorna possíveis caminhos de arquivos SQL para popular o banco."""
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
        """Buscar categorias principais"""
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
        """Buscar subcategorias de uma categoria"""
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
        """Buscar frases com filtros opcionais"""
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
        """Suprimir logs desnecessarios"""
        pass

    def do_GET(self):
        """Processar requisicoes GET"""
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path or '/'

            if path == '/':
                self.send_medical_interface()
                return

            stripped_path = path.strip('/')
            path_parts = stripped_path.split('/') if stripped_path else []

            if path == '/api/categorias':
                categorias = self.automation_server.get_categorias_principais()
                self.send_json_response(categorias)
                return

            if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'subcategorias':
                if len(path_parts) == 2:
                    self.send_error(400, "Categoria não especificada")
                    return

                categoria = urllib.parse.unquote('/'.join(path_parts[2:]))
                if not categoria:
                    self.send_error(400, "Categoria não especificada")
                    return

                subcategorias = self.automation_server.get_subcategorias(categoria)
                self.send_json_response(subcategorias)
                return

            if len(path_parts) >= 2 and path_parts[0] == 'api' and path_parts[1] == 'frases':
                if len(path_parts) == 2:
                    query_params = urllib.parse.parse_qs(parsed_url.query)
                    categoria = query_params.get('categoria', [None])[0] or None
                    subcategoria = query_params.get('subcategoria', [None])[0] or None
                    frases = self.automation_server.get_frases(categoria, subcategoria)
                    self.send_json_response(frases)
                    return

                categoria = urllib.parse.unquote(path_parts[2]) if len(path_parts) >= 3 else None
                subcategoria = urllib.parse.unquote(path_parts[3]) if len(path_parts) >= 4 else None

                if categoria in (None, ''):
                    self.send_error(400, "Categoria não especificada")
                    return

                if len(path_parts) >= 4 and subcategoria == '':
                    self.send_error(400, "Subcategoria não especificada")
                    return

                frases = self.automation_server.get_frases(categoria, subcategoria)
                self.send_json_response(frases)
                return

            self.send_error(404, "Página não encontrada")
        except Exception as e:
            print(f"Erro na requisição {self.path}: {e}")
            traceback.print_exc()
            self.send_error(500, "Erro interno do servidor")

    def send_json_response(self, data):
        """Enviar resposta JSON"""
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
        """Enviar interface HTML"""
        html_content = self.get_html_template()
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar HTML: {e}")
            self.send_error(500, "Erro ao carregar interface")

    def get_html_template(self):
        """Template HTML completo e funcional"""
        return '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servidor de Automação Médica</title>
<style>
        :root {
            color-scheme: light dark;
            --bg-primary: #0f172a;
            --bg-secondary: #1e293b;
            --bg-surface: #ffffff;
            --bg-surface-alt: #f1f5f9;
            --bg-selected: rgba(15, 23, 42, 0.08);
            --text-primary: #0f172a;
            --text-muted: #475569;
            --accent: #1d4ed8;
            --accent-strong: #1e3a8a;
            --accent-light: #e0f2fe;
            --success: #16a34a;
            --warning: #f97316;
            font-family: "Inter", "Segoe UI", "Helvetica Neue", Arial, sans-serif;
        }

        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            min-height: 100vh;
            background: linear-gradient(160deg, #0f172a 0%, #1e293b 35%, #0f172a 100%);
            color: var(--text-primary);
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            padding: 1.5rem;
        }

        header.app-header {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            color: #f8fafc;
        }

        header.app-header h1 {
            margin: 0;
            font-size: 1.8rem;
            font-weight: 700;
        }

        header.app-header p {
            margin: 0.25rem 0 0;
            font-size: 1rem;
            color: rgba(248, 250, 252, 0.78);
        }

        .status-indicator {
            background: rgba(15, 23, 42, 0.35);
            border: 1px solid rgba(148, 163, 184, 0.35);
            padding: 0.75rem 1rem;
            border-radius: 0.75rem;
            min-width: 220px;
            text-align: right;
            font-size: 0.95rem;
        }

        .status-indicator strong {
            display: block;
            color: #bae6fd;
            margin-bottom: 0.25rem;
        }

        main.layout {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(14px);
            border-radius: 1.25rem;
            padding: 1.5rem;
            display: grid;
            grid-template-columns: minmax(260px, 0.9fr) minmax(260px, 0.9fr) minmax(320px, 1.2fr);
            gap: 1.5rem;
            box-shadow: 0 24px 60px rgba(15, 23, 42, 0.28);
        }

        .panel {
            background: var(--bg-surface);
            border-radius: 1rem;
            padding: 1rem 1.25rem 1.5rem;
            display: flex;
            flex-direction: column;
            min-height: 340px;
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.6);
        }

        .panel-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 0.75rem;
            margin-bottom: 1rem;
        }

        .panel h2 {
            margin: 0;
            font-size: 1.1rem;
            color: var(--text-primary);
        }

        .panel small {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .list-container {
            flex: 1;
            overflow: hidden;
            border-radius: 0.75rem;
            border: 1px solid #e2e8f0;
            background: var(--bg-surface-alt);
            display: flex;
            flex-direction: column;
        }

        .list-scroll {
            overflow-y: auto;
            flex: 1;
            padding: 0.5rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }

        .list-item {
            border: none;
            border-radius: 0.75rem;
            padding: 0.85rem 1rem;
            background: #ffffff;
            color: var(--text-primary);
            text-align: left;
            font-size: 0.95rem;
            line-height: 1.4;
            cursor: pointer;
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
            transition: all 0.2s ease;
            box-shadow: 0 1px 0 rgba(15, 23, 42, 0.04);
        }

        .list-item:hover,
        .list-item:focus {
            outline: none;
            transform: translateY(-1px);
            background: var(--accent-light);
            box-shadow: 0 6px 18px rgba(30, 64, 175, 0.18);
        }

        .list-item.active {
            background: var(--bg-selected);
            border: 1px solid rgba(30, 64, 175, 0.3);
            box-shadow: inset 0 0 0 1px rgba(30, 64, 175, 0.4);
        }

        .list-item-title {
            font-weight: 600;
        }

        .list-item-subtitle {
            color: var(--text-muted);
            font-size: 0.8rem;
        }

        .empty-state {
            padding: 1.5rem;
            text-align: center;
            color: var(--text-muted);
            font-size: 0.95rem;
        }

        .controls {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
            margin-bottom: 0.75rem;
        }

        .controls input[type="search"] {
            flex: 1;
            min-width: 160px;
            padding: 0.65rem 0.75rem;
            border-radius: 0.7rem;
            border: 1px solid #cbd5f5;
            font-size: 0.95rem;
            box-shadow: inset 0 1px 0 rgba(148, 163, 184, 0.18);
        }

        .controls button,
        .panel-header button,
        .preview-actions button,
        .quick-actions button {
            background: var(--accent);
            color: #f8fafc;
            border: none;
            border-radius: 0.7rem;
            padding: 0.6rem 1.1rem;
            font-size: 0.9rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s ease;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            box-shadow: 0 8px 16px rgba(30, 64, 175, 0.22);
        }

        .controls button.secondary,
        .panel-header button.secondary,
        .quick-actions button.secondary {
            background: #ffffff;
            color: var(--accent);
            border: 1px solid rgba(30, 64, 175, 0.4);
            box-shadow: none;
        }

        .controls button:hover,
        .panel-header button:hover,
        .preview-actions button:hover,
        .quick-actions button:hover {
            transform: translateY(-1px);
            box-shadow: 0 12px 28px rgba(30, 64, 175, 0.28);
        }

        .preview-panel {
            position: relative;
            gap: 1rem;
        }

        .preview-actions {
            display: flex;
            flex-wrap: wrap;
            gap: 0.75rem;
        }

        .preview-actions span {
            font-size: 0.85rem;
            color: var(--text-muted);
            align-self: center;
        }

        #phrase-preview {
            width: 100%;
            min-height: 180px;
            resize: vertical;
            padding: 1rem;
            border-radius: 0.9rem;
            border: 1px solid #cbd5f5;
            background: var(--bg-surface-alt);
            font-size: 1rem;
            line-height: 1.5;
        }

        #phrase-preview:focus {
            outline: 2px solid rgba(30, 64, 175, 0.4);
        }

        .quick-actions {
            background: #f8fafc;
            border-radius: 0.9rem;
            padding: 1rem;
            border: 1px solid rgba(148, 163, 184, 0.35);
            display: flex;
            flex-direction: column;
            gap: 0.75rem;
        }

        .quick-actions h3 {
            margin: 0;
            font-size: 1rem;
            color: var(--text-primary);
        }

        .quick-actions p {
            margin: 0;
            font-size: 0.85rem;
            color: var(--text-muted);
        }

        .quick-actions-list {
            display: grid;
            gap: 0.5rem;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }

        .toast {
            position: fixed;
            bottom: 1.5rem;
            right: 1.5rem;
            background: rgba(15, 23, 42, 0.9);
            color: #f8fafc;
            padding: 0.85rem 1.2rem;
            border-radius: 0.8rem;
            box-shadow: 0 18px 34px rgba(15, 23, 42, 0.3);
            opacity: 0;
            pointer-events: none;
            transform: translateY(10px);
            transition: opacity 0.25s ease, transform 0.25s ease;
            z-index: 50;
        }

        .toast.show {
            opacity: 1;
            transform: translateY(0);
        }

        .badge {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            min-width: 1.6rem;
            padding: 0.15rem 0.55rem;
            font-size: 0.75rem;
            border-radius: 999px;
            background: rgba(30, 64, 175, 0.14);
            color: var(--accent-strong);
            font-weight: 600;
        }

        .statistics {
            display: flex;
            gap: 1rem;
            font-size: 0.8rem;
            color: var(--text-muted);
        }

        .statistics span strong {
            color: var(--accent-strong);
        }

        @media (max-width: 1200px) {
            main.layout {
                grid-template-columns: repeat(2, minmax(260px, 1fr));
            }
        }

        @media (max-width: 900px) {
            body {
                padding: 1rem;
            }

            main.layout {
                grid-template-columns: 1fr;
            }

            .status-indicator {
                text-align: left;
            }
        }

        @media (max-width: 600px) {
            header.app-header h1 {
                font-size: 1.4rem;
            }

            .controls {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
<header class="app-header">
        <div>
            <h1>Servidor de Automação Médica</h1>
            <p>Selecione uma categoria, depois uma subcategoria e clique na frase para visualizar e copiar.</p>
        </div>
        <div class="status-indicator" aria-live="polite">
            <strong>Status do servidor</strong>
            <span id="status-message">Carregando dados…</span>
        </div>
    </header>
    <main class="layout">
        <section class="panel" aria-labelledby="categorias-titulo">
            <div class="panel-header">
                <div>
                    <h2 id="categorias-titulo">Categorias principais</h2>
                    <small>Organizam os protocolos por tema clínico</small>
                </div>
                <button type="button" id="refresh-data" class="secondary">Recarregar</button>
            </div>
            <div class="list-container" role="navigation" aria-label="Categorias">
                <div id="category-list" class="list-scroll" data-empty="Aguardando carregamento…"></div>
            </div>
        </section>
        <section class="panel" aria-labelledby="subcategorias-titulo">
            <div class="panel-header">
                <div>
                    <h2 id="subcategorias-titulo">Subcategorias</h2>
                    <small>Refine a categoria para acessar protocolos específicos</small>
                </div>
            </div>
            <div class="list-container" role="navigation" aria-label="Subcategorias">
                <div id="subcategory-list" class="list-scroll" data-empty="Selecione uma categoria"></div>
            </div>
        </section>
        <section class="panel preview-panel" aria-labelledby="frases-titulo">
            <div class="panel-header">
                <div>
                    <h2 id="frases-titulo">Frases cadastradas</h2>
                    <small>Lista ordenada de frases prontas para uso</small>
                </div>
            </div>
            <div class="controls" role="search">
                <input type="search" id="phrase-search" placeholder="Pesquisar por termo, subcategoria ou conteúdo" aria-label="Pesquisar frases">
                <div class="statistics" aria-live="polite">
                    <span><strong id="phrase-count">0</strong> frases</span>
                    <span id="filter-count"></span>
                </div>
            </div>
            <div class="list-container" aria-label="Frases disponíveis">
                <div id="phrase-list" class="list-scroll" data-empty="Selecione uma subcategoria"></div>
            </div>
            <div class="preview-actions">
                <button type="button" id="copy-preview">Copiar frase selecionada</button>
                <span>Atalhos: Cmd/Ctrl + 1-5 para usar frases rápidas</span>
            </div>
            <textarea id="phrase-preview" readonly placeholder="Escolha uma frase para visualizar o conteúdo completo."></textarea>
            <div class="quick-actions">
                <div>
                    <h3>Atalhos rápidos</h3>
                    <p>Frases de saudação e orientações utilizadas com frequência. Pressione Cmd/Ctrl + número para ativar.</p>
                </div>
                <div id="quick-actions" class="quick-actions-list" role="list"></div>
            </div>
        </section>
    </main>
    <div id="toast" class="toast" role="status" aria-live="polite"></div>
    <script>
        document.addEventListener('DOMContentLoaded', () => {
            const state = {
                categories: [],
                subcategories: [],
                phrases: [],
                selectedCategory: null,
                selectedSubcategory: null,
                selectedPhraseId: null
            };

            const statusMessage = document.getElementById('status-message');
            const categoryList = document.getElementById('category-list');
            const subcategoryList = document.getElementById('subcategory-list');
            const phraseList = document.getElementById('phrase-list');
            const phraseSearch = document.getElementById('phrase-search');
            const phrasePreview = document.getElementById('phrase-preview');
            const phraseCount = document.getElementById('phrase-count');
            const filterCount = document.getElementById('filter-count');
            const copyButton = document.getElementById('copy-preview');
            const toast = document.getElementById('toast');
            const refreshButton = document.getElementById('refresh-data');
            const quickActionsContainer = document.getElementById('quick-actions');

            const quickPhrases = [
                { label: 'Bom dia', text: 'Bom dia, tudo bem? Qual seria a solicitação, por gentileza?' },
                { label: 'Boa tarde', text: 'Boa tarde, tudo bem? Qual seria a solicitação, por gentileza?' },
                { label: 'Boa noite', text: 'Boa noite, tudo bem? Qual seria a solicitação, por gentileza?' },
                { label: 'Encerramento', text: 'Disponha! Bom plantão!' },
                { label: 'Início TeleAVC', text: 'Bom dia! Me chamo Alessandra Morais, neurologista do programa TeleAVC. Estou disponível hoje das 07h às 19h. Bom plantão a todos!' }
            ];

            function escapeHTML(value) {
                if (value == null) {
                    return '';
                }
                const stringValue = String(value);
                const replacements = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;'
                };
                let result = '';
                for (let index = 0; index < stringValue.length; index += 1) {
                    const character = stringValue[index];
                    if (Object.prototype.hasOwnProperty.call(replacements, character)) {
                        result += replacements[character];
                    } else {
                        result += character;
                    }
                }
                return result;
            }

            function setStatus(message, isError = false) {
                statusMessage.textContent = message;
                statusMessage.style.color = isError ? '#fca5a5' : '#bae6fd';
            }

            function showToast(message) {
                toast.textContent = message;
                toast.classList.add('show');
                setTimeout(() => toast.classList.remove('show'), 2800);
            }

            function renderEmptyState(element, text) {
                element.innerHTML = `<div class="empty-state">${text}</div>`;
            }

            function renderCategories() {
                if (!state.categories.length) {
                    renderEmptyState(categoryList, categoryList.dataset.empty || 'Nenhuma categoria encontrada.');
                    return;
                }

                categoryList.innerHTML = '';
                state.categories.forEach(category => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'list-item';
                    if (category === state.selectedCategory) {
                        button.classList.add('active');
                    }
                    button.innerHTML = `<span class="list-item-title">${escapeHTML(category)}</span>`;
                    button.addEventListener('click', () => {
                        if (state.selectedCategory !== category) {
                            state.selectedCategory = category;
                            state.selectedSubcategory = null;
                            state.selectedPhraseId = null;
                            state.subcategories = [];
                            state.phrases = [];
                            phrasePreview.value = '';
                            phraseList.innerHTML = '';
                            renderCategories();
                            renderEmptyState(subcategoryList, 'Carregando subcategorias…');
                            loadSubcategories(category);
                        }
                    });
                    categoryList.appendChild(button);
                });
            }

            function renderSubcategories() {
                if (!state.subcategories.length) {
                    const message = state.selectedCategory ? 'Nenhuma subcategoria disponível.' : (subcategoryList.dataset.empty || 'Selecione uma categoria');
                    renderEmptyState(subcategoryList, message);
                    return;
                }

                subcategoryList.innerHTML = '';
                state.subcategories.forEach(subcategory => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'list-item';
                    if (subcategory === state.selectedSubcategory) {
                        button.classList.add('active');
                    }
                    button.innerHTML = `<span class="list-item-title">${escapeHTML(subcategory)}</span>`;
                    button.addEventListener('click', () => {
                        if (state.selectedSubcategory !== subcategory) {
                            state.selectedSubcategory = subcategory;
                            state.selectedPhraseId = null;
                            phrasePreview.value = '';
                            renderSubcategories();
                            renderEmptyState(phraseList, 'Carregando frases…');
                            loadPhrases(state.selectedCategory, subcategory);
                        }
                    });
                    subcategoryList.appendChild(button);
                });
            }

            function renderPhrases() {
                if (!state.phrases.length) {
                    const message = state.selectedSubcategory ? 'Nenhuma frase encontrada para este filtro.' : (phraseList.dataset.empty || 'Selecione uma subcategoria');
                    renderEmptyState(phraseList, message);
                    phraseCount.textContent = '0';
                    filterCount.textContent = '';
                    return;
                }

                const query = phraseSearch.value.trim().toLowerCase();
                const filtered = state.phrases.filter(phrase => {
                    if (!query) {
                        return true;
                    }
                    return (
                        phrase.nome.toLowerCase().includes(query) ||
                        (phrase.subcategoria && phrase.subcategoria.toLowerCase().includes(query)) ||
                        phrase.conteudo.toLowerCase().includes(query)
                    );
                });

                phraseCount.textContent = state.phrases.length.toString();
                filterCount.textContent = query ? `${filtered.length} exibidas` : '';

                if (!filtered.length) {
                    renderEmptyState(phraseList, 'Nenhuma frase corresponde à pesquisa.');
                    return;
                }

                phraseList.innerHTML = '';
                filtered.forEach(phrase => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'list-item';
                    if (phrase.id === state.selectedPhraseId) {
                        button.classList.add('active');
                    }
                    button.innerHTML = `
                        <span class="list-item-title">${escapeHTML(phrase.nome)}</span>
                        <span class="list-item-subtitle">${escapeHTML(phrase.subcategoria || state.selectedSubcategoria || '')}</span>
                    `;
                    button.addEventListener('click', () => {
                        state.selectedPhraseId = phrase.id;
                        phrasePreview.value = phrase.conteudo;
                        renderPhrases();
                    });
                    button.addEventListener('dblclick', async () => {
                        state.selectedPhraseId = phrase.id;
                        phrasePreview.value = phrase.conteudo;
                        await copyToClipboard(phrase.conteudo);
                        renderPhrases();
                    });
                    phraseList.appendChild(button);
                });
            }

            async function copyToClipboard(text) {
                if (!text) {
                    showToast('Nenhuma frase selecionada.');
                    return;
                }
                try {
                    if (navigator.clipboard && navigator.clipboard.writeText) {
                        await navigator.clipboard.writeText(text);
                    } else {
                        const temp = document.createElement('textarea');
                        temp.value = text;
                        temp.style.position = 'fixed';
                        temp.style.opacity = '0';
                        document.body.appendChild(temp);
                        temp.focus();
                        temp.select();
                        document.execCommand('copy');
                        document.body.removeChild(temp);
                    }
                    showToast('Frase copiada para a área de transferência.');
                } catch (error) {
                    console.error('Erro ao copiar', error);
                    showToast('Não foi possível copiar automaticamente. Utilize Ctrl/Cmd + C.');
                }
            }

            async function loadCategories() {
                setStatus('Carregando categorias…');
                try {
                    const response = await fetch('/api/categorias');
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const data = await response.json();
                    state.categories = Array.isArray(data) ? data : [];
                    if (!state.categories.length) {
                        setStatus('Nenhuma categoria cadastrada.', true);
                    } else {
                        setStatus('Categorias carregadas com sucesso.');
                    }
                    renderCategories();
                } catch (error) {
                    console.error('Erro ao carregar categorias', error);
                    setStatus('Erro ao carregar categorias.', true);
                    renderEmptyState(categoryList, 'Não foi possível carregar as categorias.');
                }
            }

            async function loadSubcategories(category) {
                if (!category) {
                    return;
                }
                try {
                    const response = await fetch(`/api/subcategorias/${encodeURIComponent(category)}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const data = await response.json();
                    state.subcategories = Array.isArray(data) ? data : [];
                    renderSubcategories();
                } catch (error) {
                    console.error('Erro ao carregar subcategorias', error);
                    renderEmptyState(subcategoryList, 'Erro ao carregar subcategorias.');
                }
            }

            async function loadPhrases(category, subcategory) {
                if (!category) {
                    return;
                }
                try {
                    const params = new URLSearchParams();
                    params.set('categoria', category);
                    if (subcategory) {
                        params.set('subcategoria', subcategoria);
                    }
                    const response = await fetch(`/api/frases?${params.toString()}`);
                    if (!response.ok) {
                        throw new Error(`HTTP ${response.status}`);
                    }
                    const data = await response.json();
                    state.phrases = Array.isArray(data) ? data : [];
                    renderPhrases();
                } catch (error) {
                    console.error('Erro ao carregar frases', error);
                    renderEmptyState(phraseList, 'Erro ao carregar frases.');
                }
            }

            function setupQuickActions() {
                quickActionsContainer.innerHTML = '';
                quickPhrases.forEach((item, index) => {
                    const button = document.createElement('button');
                    button.type = 'button';
                    button.className = 'secondary';
                    button.innerHTML = `${index + 1}. ${escapeHTML(item.label)}`;
                    button.addEventListener('click', () => {
                        phrasePreview.value = item.text;
                        state.selectedPhraseId = null;
                        copyToClipboard(item.text);
                    });
                    quickActionsContainer.appendChild(button);
                });
            }

            phraseSearch.addEventListener('input', () => renderPhrases());

            copyButton.addEventListener('click', () => {
                copyToClipboard(phrasePreview.value);
            });

            refreshButton.addEventListener('click', () => {
                state.selectedCategory = null;
                state.selectedSubcategory = null;
                state.selectedPhraseId = null;
                state.subcategories = [];
                state.phrases = [];
                phrasePreview.value = '';
                subcategoryList.innerHTML = '';
                phraseList.innerHTML = '';
                loadCategories();
            });

            document.addEventListener('keydown', event => {
                if ((event.metaKey || event.ctrlKey) && /^[1-5]$/.test(event.key)) {
                    const index = Number(event.key) - 1;
                    const quick = quickPhrases[index];
                    if (quick) {
                        event.preventDefault();
                        phrasePreview.value = quick.text;
                        state.selectedPhraseId = null;
                        copyToClipboard(quick.text);
                    }
                }
            });

            setupQuickActions();
            loadCategories();
        });
    </script>    
</body>
</html>'''


def run_medical_server(db_path):
    """Runs the medical phrases server on port 8080."""
    automation_server = MedicalAutomationServer(db_path=db_path)
    def handler(*args, **kwargs):
        WebRequestHandler(*args, automation_server=automation_server, **kwargs)
    server_address = ('', 8080)
    httpd = HTTPServer(server_address, handler)
    print(f"✓ Servidor de frases médicas rodando em http://localhost:8080")
    httpd.serve_forever()

def run_snippet_server():
    """Runs the snippet server on port 5000."""
    init_snippet_db()
    print(f"✓ Servidor de snippets rodando em http://localhost:5000")
    # Note: Flask's development server is not for production, but is fine for this use case.
    # threaded=True helps handle simultaneous requests more gracefully.
    snippet_app.run(host='0.0.0.0', port=5000, threaded=True)

def run_all_servers():
    db_path = os.environ.get('AUTOMATION_DB_PATH') or os.environ.get('DB_PATH')
    
    # Run medical server in a background thread
    medical_thread = Thread(target=run_medical_server, args=(db_path,), daemon=True)
    medical_thread.start()

    # Run snippet server in the main thread
    run_snippet_server()


if __name__ == "__main__":
    run_all_servers()
