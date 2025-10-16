"""
Medical Automation HTTP Request Handler
Handles HTTP requests for the medical phrases interface.
"""
import json
import urllib.parse
import traceback
from http.server import BaseHTTPRequestHandler
from db.medical_db import MedicalDatabaseManager


class MedicalRequestHandler(BaseHTTPRequestHandler):
    """HTTP request handler for medical automation server."""
    
    def __init__(self, *args, automation_server=None, **kwargs):
        """
        Initialize the request handler.
        
        Args:
            automation_server: MedicalDatabaseManager instance.
            *args: Positional arguments for BaseHTTPRequestHandler.
            **kwargs: Keyword arguments for BaseHTTPRequestHandler.
        """
        self.automation_server = automation_server
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        """Suppress unnecessary logs."""
        pass
    
    def do_GET(self):
        """
        Process GET requests.
        
        Routes:
            /api/categorias - Get all main categories
            /api/subcategorias/<category> - Get subcategories
            /api/frases?categoria=<cat>&subcategoria=<subcat> - Get phrases
            / - Serve HTML interface
        """
        try:
            parsed_url = urllib.parse.urlparse(self.path)
            path = parsed_url.path
            
            # API routes
            if path.startswith('/api/'):
                self._handle_api_request(path, parsed_url)
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
    
    def _handle_api_request(self, path, parsed_url):
        """
        Handle API routes.
        
        Args:
            path: Request path.
            parsed_url: Parsed URL object.
        """
        path_parts = path.strip('/').split('/')
        
        # GET /api/categorias
        if len(path_parts) == 2 and path_parts[1] == 'categorias':
            categorias = self.automation_server.get_categorias_principais()
            self.send_json_response(categorias)
            return
        
        # GET /api/subcategorias/<categoria>
        if len(path_parts) >= 3 and path_parts[1] == 'subcategorias':
            categoria = urllib.parse.unquote('/'.join(path_parts[2:]))
            if not categoria:
                self.send_error(400, "Categoria não especificada")
                return
            subcategorias = self.automation_server.get_subcategorias(categoria)
            self.send_json_response(subcategorias)
            return
        
        # GET /api/frases?categoria=<cat>&subcategoria=<subcat>
        if len(path_parts) >= 2 and path_parts[1] == 'frases':
            query_params = urllib.parse.parse_qs(parsed_url.query)
            categoria = query_params.get('categoria', [None])[0]
            subcategoria = query_params.get('subcategoria', [None])[0]
            frases = self.automation_server.get_frases(categoria, subcategoria)
            self.send_json_response(frases)
            return
        
        self.send_error(404, "Rota de API não encontrada")
    
    def send_json_response(self, data):
        """
        Send a JSON response.
        
        Args:
            data: Data to serialize as JSON.
        """
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
        """Send the HTML interface."""
        try:
            # Read HTML template from file
            from pathlib import Path
            template_path = Path(__file__).parent.parent / 'templates' / 'medical_interface.html'
            
            if template_path.exists():
                with open(template_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            else:
                # Fallback to inline template if file doesn't exist yet
                html_content = self._get_inline_html_template()
            
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Cache-Control', 'no-cache')
            self.end_headers()
            self.wfile.write(html_content.encode('utf-8'))
        except Exception as e:
            print(f"Erro ao enviar HTML: {e}")
            traceback.print_exc()
            self.send_error(500, "Erro ao carregar interface")
    
    def _get_inline_html_template(self):
        """
        Fallback inline HTML template.
        This will be replaced by the external template file.
        
        Returns:
            str: HTML content
        """
        return '''<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Servidor de Automação Médica</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 40px;
            background: #f5f5f5;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .status {
            padding: 15px;
            background: #e7f3ff;
            border-left: 4px solid #007bff;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Servidor de Automação Médica</h1>
        <div class="status">
            <strong>Status:</strong> Servidor ativo
        </div>
        <p>A interface completa será carregada do arquivo de template.</p>
        <p>Endpoints da API disponíveis:</p>
        <ul>
            <li><code>GET /api/categorias</code> - Listar categorias principais</li>
            <li><code>GET /api/subcategorias/&lt;categoria&gt;</code> - Listar subcategorias</li>
            <li><code>GET /api/frases?categoria=&lt;cat&gt;&amp;subcategoria=&lt;subcat&gt;</code> - Listar frases</li>
        </ul>
    </div>
</body>
</html>'''
