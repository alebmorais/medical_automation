#!/usr/bin/env python3
"""
Medical Automation Server - Main Entry Point
Combined server for medical phrases and snippet management.
"""
import sys
import argparse
from threading import Thread
from config.settings import SNIPPET_PORT, MEDICAL_PORT
from servers.snippet_server import run_snippet_server
from servers.medical_server import run_medical_server


def run_all_servers(db_path: str = None, snippet_host: str = '127.0.0.1', medical_host: str = ''):
    """
    Run both servers simultaneously.
    
    Medical server runs in a background thread, snippet server in main thread.
    
    Args:
        db_path: Path to the medical database. Auto-resolves if not provided.
        snippet_host: Host for snippet server (default: 127.0.0.1 for localhost only).
        medical_host: Host for medical server (default: '' for all interfaces).
    """
    print("=" * 60)
    print("Iniciando servidores de automação médica...")
    print("=" * 60)
    
    # Start medical server in background thread
    medical_thread = Thread(
        target=run_medical_server,
        args=(db_path, medical_host, MEDICAL_PORT),
        daemon=True,
        name="MedicalServerThread"
    )
    medical_thread.start()
    
    # Give medical server time to start
    import time
    time.sleep(0.5)
    
    # Run snippet server in main thread (blocking)
    # This keeps the main process alive
    try:
        run_snippet_server(host=snippet_host, port=SNIPPET_PORT, debug=False)
    except KeyboardInterrupt:
        print("\n⚠ Servidores interrompidos pelo usuário")
        sys.exit(0)


def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Medical Automation Server - Gerenciador de frases médicas e snippets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  %(prog)s                          # Executar ambos os servidores
  %(prog)s --mode medical           # Executar apenas servidor de frases médicas
  %(prog)s --mode snippet           # Executar apenas servidor de snippets
  %(prog)s --db-path ./custom.db    # Usar banco de dados customizado
  %(prog)s --snippet-port 5001      # Usar porta customizada para snippets
  %(prog)s --medical-port 8081      # Usar porta customizada para frases médicas
        """
    )
    
    parser.add_argument(
        '--mode',
        choices=['all', 'medical', 'snippet'],
        default='all',
        help='Modo de execução: all (ambos), medical (frases médicas), snippet (snippets)'
    )
    
    parser.add_argument(
        '--db-path',
        type=str,
        default=None,
        help='Caminho do banco de dados de frases médicas (auto-resolve se não especificado)'
    )
    
    parser.add_argument(
        '--snippet-port',
        type=int,
        default=SNIPPET_PORT,
        help=f'Porta para o servidor de snippets (padrão: {SNIPPET_PORT})'
    )
    
    parser.add_argument(
        '--medical-port',
        type=int,
        default=MEDICAL_PORT,
        help=f'Porta para o servidor de frases médicas (padrão: {MEDICAL_PORT})'
    )
    
    parser.add_argument(
        '--snippet-host',
        type=str,
        default='127.0.0.1',
        help='Host para o servidor de snippets (padrão: 127.0.0.1)'
    )
    
    parser.add_argument(
        '--medical-host',
        type=str,
        default='',
        help='Host para o servidor de frases médicas (padrão: "" para todas as interfaces)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Ativar modo debug (apenas para desenvolvimento)'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Medical Automation Server v2.0.0 (Refactored)'
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == 'medical':
            print(f"Iniciando servidor de frases médicas na porta {args.medical_port}...")
            run_medical_server(
                db_path=args.db_path,
                host=args.medical_host,
                port=args.medical_port
            )
        
        elif args.mode == 'snippet':
            print(f"Iniciando servidor de snippets na porta {args.snippet_port}...")
            run_snippet_server(
                host=args.snippet_host,
                port=args.snippet_port,
                debug=args.debug
            )
        
        else:  # mode == 'all'
            run_all_servers(
                db_path=args.db_path,
                snippet_host=args.snippet_host,
                medical_host=args.medical_host
            )
    
    except KeyboardInterrupt:
        print("\n⚠ Servidor interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro ao iniciar servidor: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
