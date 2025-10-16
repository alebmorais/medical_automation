"""
Medical Server Module
HTTP server initialization and runner for medical phrase management.
"""
from http.server import HTTPServer
from functools import partial
from api.medical_handler import MedicalRequestHandler
from db.medical_db import MedicalDatabaseManager
from config.settings import MEDICAL_PORT


def create_medical_handler(automation_server: MedicalDatabaseManager):
    """
    Create a request handler with the automation server injected.
    
    Args:
        automation_server: MedicalDatabaseManager instance.
        
    Returns:
        Configured request handler class.
    """
    return partial(MedicalRequestHandler, automation_server=automation_server)


def run_medical_server(db_path: str = None, host: str = '', port: int = None):
    """
    Run the medical phrases HTTP server.
    
    Args:
        db_path: Path to the medical phrases database. Auto-resolves if not provided.
        host: Host address to bind to. Default is '' (all interfaces).
        port: Port number to use. Uses config default if not provided.
    """
    if port is None:
        port = MEDICAL_PORT
    
    # Initialize the database manager
    automation_server = MedicalDatabaseManager(db_path=db_path)
    
    # Create the request handler with automation server injected
    handler_class = create_medical_handler(automation_server)
    
    # Create and start the HTTP server
    server_address = (host, port)
    httpd = HTTPServer(server_address, handler_class)
    
    print(f"✓ Servidor de frases médicas rodando em http://localhost:{port}")
    
    # Start serving
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⚠ Servidor interrompido pelo usuário")
        httpd.shutdown()


if __name__ == "__main__":
    # Run if executed directly
    run_medical_server()
