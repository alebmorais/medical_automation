#!/usr/bin/env python3
"""
Servidor de Automação Médica
"""
import json
import os
import sys
from functools import partial
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import traceback
import re

class TextFileParser:
    """Lê e analisa o arquivo de texto 'database'."""

    def __init__(self, file_path):
        self.file_path = file_path

    def parse(self):
        """Analisa o arquivo e retorna os dados estruturados."""
        if not os.path.exists(self.file_path):
            print(f"ERRO: Arquivo de dados '{self.file_path}' não encontrado.")
            return {}

        all_data = {"categories": {}, "phrases": []}
        current_category = None
        current_subcategory = None
        order_in_subcategory = 1
        phrase_id_counter = 1
        current_phrase_lines = []

        def save_pending_phrase():
            nonlocal order_in_subcategory, phrase_id_counter
            if current_phrase_lines and current_category and current_subcategory:
                content = "\n".join(current_phrase_lines).strip()
                # Use the first line of the content as a base for the name, or a default
                phrase_name = content.split('\n')[0]
                if len(phrase_name) > 50: # Truncate long names
                    phrase_name = phrase_name[:47] + "..."

                all_data["phrases"].append({
                    "id": phrase_id_counter, "nome": phrase_name, "conteudo": content,
                    "categoria_principal": current_category, "subcategoria": current_subcategory,
                    "ordem": order_in_subcategory
                })
                order_in_subcategory += 1
                phrase_id_counter += 1
                current_phrase_lines.clear()

        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                stripped_line = line.strip()
                cat_match = re.match(r'^CATEGORIA:\s*(.*)', stripped_line, re.IGNORECASE)
                subcat_match = re.match(r'^SUBCATEGORIA:\s*(.*)', stripped_line, re.IGNORECASE)
                phrase_match = re.match(r'^\d+\.\s*(.*)', stripped_line)

                if cat_match:
                    save_pending_phrase()
                    current_category = cat_match.group(1).strip()
                    if current_category not in all_data["categories"]:
                        all_data["categories"][current_category] = []
                    current_subcategory = None
                elif subcat_match and current_category:
                    save_pending_phrase()
                    current_subcategory = subcat_match.group(1).strip()
                    if current_subcategory not in all_data["categories"][current_category]:
                        all_data["categories"][current_category].append(current_subcategory)
                    order_in_subcategory = 1
                elif phrase_match and current_category and current_subcategory:
                    # A new phrase is starting. Save any pending phrase content first.
                    save_pending_phrase()
                    current_phrase_lines.append(phrase_match.group(1).strip())
                elif stripped_line and current_phrase_lines:
                    # This is a continuation of a multi-line phrase
                    current_phrase_lines.append(stripped_line)

        save_pending_phrase() # Save the very last phrase in the file

        # Ordenar subcategorias
        for cat in all_data["categories"]:
            all_data["categories"][cat].sort()

        return all_data

class MedicalAutomationServer:
    def __init__(self, db_path=None):
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.data_path = self.resolve_database_path(db_path)
        self.all_data = self.load_data_from_source()

    def load_data_from_source(self):
        """Carrega os dados do arquivo de texto."""
        if not self.data_path:
            print("ERRO: Nenhum arquivo de dados ('database' ou 'MainD.txt') foi encontrado.")
            sys.exit(1)
        
        parser = TextFileParser(self.data_path)
        data = parser.parse()
        if not data.get("phrases"):
            print(f"AVISO: Nenhum dado foi carregado de '{self.data_path}'. A interface pode ficar vazia.")
        else:
            print(f"✓ Dados carregados de '{self.data_path}': {len(data['phrases'])} frases encontradas.")
        return data

    def resolve_database_path(self, preferred_path):
        """Determina o caminho do arquivo de dados (database ou MainD.txt)."""
        candidates = []

        # 1. Argumento explícito
        if preferred_path:
            candidates.append(preferred_path)

        # 2. Caminhos padrões relativos ao script
        script_dir = self.base_dir
        default_filenames = ["database", "MainD.txt"]
        for filename in default_filenames:
            candidates.append(os.path.join(script_dir, filename))
            candidates.append(os.path.join(script_dir, "database", filename))

        # 3. Procurar nos candidatos
        for path in candidates:
            if path and os.path.exists(path):
                return path
        
        return None

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
            path = parsed_url.path

            # API routes - This version serves all data at once, so API endpoints are not needed.
            # If you want to re-enable them, you would add them here.
            # Example:
            # if path.startswith('/api/'):
            #     ...

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
        html_content = self.get_html_template(self.automation_server.all_data)
        try:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar HTML: {e}")
            self.send_error(500, "Erro ao carregar interface")

    def get_html_template(self, data):
        """Template HTML completo e funcional"""
        # NOTE: The HTML template is very long and has not been changed.
        # It is omitted here for brevity but remains in the actual file.
        # A <script> tag is added to inject data.
        injected_data = json.dumps(data, ensure_ascii=False, indent=2)

        template = '''<!DOCTYPE html>
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
        // Data injected by the server
        const ALL_DATA = {injected_data};
    </script>
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
                        <span class="list-item-subtitle">${escapeHTML(phrase.subcategoria || state.selectedSubcategory || '')}</span>
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
                state.categories = Object.keys(ALL_DATA.categories || {}).sort();
                if (!state.categories.length) {
                    setStatus('Nenhuma categoria cadastrada.', true);
                } else {
                    setStatus('Categorias carregadas com sucesso.');
                }
                renderCategories();
            }

            async function loadSubcategories(category) {
                if (!category) {
                    return;
                }
                state.subcategories = ALL_DATA.categories[category] || [];
                renderSubcategories();
            }

            async function loadPhrases(category, subcategory) {
                if (!category) {
                    return;
                }
                try {
                    const params = new URLSearchParams();
                    params.set('categoria', category);
                    if (subcategory) {
                        params.set('subcategoria', subcategory);
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

        # Safely inject the JSON data into the template. We use replace instead of an f-string
        # to avoid accidental interpretation of single braces in the large HTML/CSS content.
        return template.replace('{injected_data}', injected_data)

def run_server():
    """Runs the medical phrases server."""
    automation_server = MedicalAutomationServer()

    # Use functools.partial to create a handler factory with the server instance
    handler_class = partial(WebRequestHandler, automation_server=automation_server)

    server_address = ('', 8080)
    httpd = HTTPServer(server_address, handler_class)
    print(f"✓ Servidor de frases médicas rodando em http://localhost:8080")
    print(f"  ↳ Usando dados de: '{automation_server.data_path}'")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor encerrado pelo usuário.")
    finally:
        httpd.server_close()

if __name__ == "__main__":
    run_server()
