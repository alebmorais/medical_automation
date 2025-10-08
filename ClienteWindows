#!/usr/bin/env python3
# Cliente Desktop para Windows - Automação Médica
# Interface nativa com fundo azul escuro, navegação por voz, atalhos e cliques
# Detecta automaticamente se está no Windows e só ativa neste sistema

import json
import os
import platform
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, ttk
from urllib import request as urllib_request
import traceback

# Função utilitária para lidar com pausas sem depender de input() em ambientes
# onde stdin pode não estar disponível (ex: execução por atalho ou como
# aplicativo empacotado).
def pause_for_user(prompt, delay_seconds=3):
    """Exibe uma mensagem de pausa sem exigir entrada quando stdin não existe."""
    try:
        if sys.stdin and sys.stdin.isatty():
            input(prompt)
            return
    except (EOFError, RuntimeError):
        pass

    # Ambiente não interativo: apenas informar e aguardar brevemente para que
    # o usuário leia a mensagem.
    message = prompt.strip() or "Pressione Enter para continuar..."
    print(message)
    time.sleep(max(delay_seconds, 0))

# Tentar importar bibliotecas opcionais

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    requests = None



try:
    import pyautogui
    AUTOGUI_AVAILABLE = True
except ImportError:
    AUTOGUI_AVAILABLE = False

try:
    import pynput
    from pynput import keyboard
    PYNPUT_AVAILABLE = True
except ImportError:
    PYNPUT_AVAILABLE = False

try:
    import webview

    WEBVIEW_AVAILABLE = True
except ImportError:
    WEBVIEW_AVAILABLE = False
    webview = None


class WindowsDesktopClient:
    def __init__(self):
        """Inicializar o cliente desktop e configurar dependências."""
        # Verificar se está no Windows
        if platform.system() != "Windows":
            print("Sistema não é Windows. Cliente desktop não será iniciado.")
            return

        # Configurações
        self.pi_url = "http://pi.local:8080"
        
        self.current_phrase = None

        # Dados
        self.categories = []
        self.subcategories = []
        self.phrases = []
        self.selected_category = None
        self.selected_subcategory = None

        # Interface
        self.root = None
        
        
        self.webview_window = None
        self.ui_mode = None
        self.pending_webview = False
        self.force_legacy_ui = False
        self.legacy_initialized = False

        # Inicializar
        
        self.setup_gui()
        if self.ui_mode == "legacy":
            self.initialize_legacy_mode()

    def initialize_legacy_mode(self):
        """Ensure that legacy mode helpers are configured only once."""
        if self.legacy_initialized:
            return
        self.setup_keyboard_shortcuts()
        self.load_categories()
        self.legacy_initialized = True

    

    def setup_gui(self):
        """Criar interface do cliente."""
        # Paleta comum para fallback/legado
        self.colors = {
            "bg_primary": "#1a237e",  # Azul escuro principal
            "bg_secondary": "#283593",  # Azul médio
            "bg_accent": "#3f51b5",  # Azul claro
            "text_primary": "#ffffff",  # Branco
            "text_secondary": "#e8eaf6",  # Branco levemente azulado
            "button_active": "#4caf50",  # Verde
            "button_hover": "#66bb6a",  # Verde claro
            "border": "#5c6bc0",  # Azul para bordas
        }

        pi_reachable = self.is_pi_reachable()

        if WEBVIEW_AVAILABLE and pi_reachable and not self.force_legacy_ui:
            self.ui_mode = "webview"
            self.webview_window = webview.create_window(
                "Automação Médica",
                self.pi_url,
                width=1000,
                height=700,
                resizable=True,
            )
            return

        # Necessário criar janela Tk para fallback ou interface legada
        self.root = tk.Tk()
        self.root.title("Automação Médica")
        self.root.geometry("1000x700")
        self.root.configure(bg=self.colors["bg_primary"])
        self.root.attributes("-topmost", True)

        if not pi_reachable:
            self.ui_mode = "fallback"
            self.build_offline_screen()
            return

        # Quando pywebview não está disponível, mantemos a UI Tk existente
        if not WEBVIEW_AVAILABLE:
            print(
                "pywebview não foi encontrado. Utilizando interface Tkinter tradicional."
            )

        self.ui_mode = "legacy"

        # Configurar estilo ttk apenas no modo legado
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Dark.TFrame", background=self.colors["bg_primary"])
        style.configure(
            "Dark.TLabel",
            background=self.colors["bg_primary"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 10),
        )
        style.configure(
            "Title.TLabel",
            background=self.colors["bg_primary"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Dark.TButton",
            background=self.colors["bg_accent"],
            foreground=self.colors["text_primary"],
            font=("Segoe UI", 10, "bold"),
        )

        self.create_header()
        
        self.create_navigation_area()
        self.create_preview_area()
        self.create_status_bar()

        self.root.focus_set()
        self.root.bind("<Escape>", lambda e: self.toggle_minimize())
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())

    def build_offline_screen(self):
        """Exibir tela simples informando ausência de conexão."""
        container = tk.Frame(self.root, bg=self.colors["bg_primary"])
        container.pack(expand=True, fill=tk.BOTH, padx=40, pady=40)

        title = tk.Label(
            container,
            text="Não foi possível acessar o Raspberry Pi.",
            bg=self.colors["bg_primary"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 18, "bold"),
            wraplength=600,
            justify="center",
        )
        title.pack(pady=(0, 20))

        instructions = (
            "Verifique se o Raspberry Pi está ligado e conectado à rede. "
            "Conecte o computador ao mesmo Wi-Fi ou cabo e tente novamente."
        )
        self.fallback_status_var = tk.StringVar(value=instructions)
        status_label = tk.Label(
            container,
            textvariable=self.fallback_status_var,
            bg=self.colors["bg_primary"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 11),
            wraplength=600,
            justify="center",
        )
        status_label.pack(pady=(0, 20))

        button_frame = tk.Frame(container, bg=self.colors["bg_primary"])
        button_frame.pack()

        retry_button = tk.Button(
            button_frame,
            text="Tentar novamente",
            command=self.retry_connection,
            bg=self.colors["button_active"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
        )
        retry_button.pack(side=tk.LEFT, padx=10)

        close_button = tk.Button(
            button_frame,
            text="Fechar",
            command=self.root.destroy,
            bg=self.colors["bg_accent"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 11, "bold"),
            padx=16,
            pady=8,
        )
        close_button.pack(side=tk.LEFT, padx=10)

        if not WEBVIEW_AVAILABLE:
            note = tk.Label(
                container,
                text=(
                    "Observação: instale o pacote 'pywebview' para carregar a interface "
                    "web moderna diretamente no aplicativo."
                ),
                bg=self.colors["bg_primary"],
                fg=self.colors["text_secondary"],
                font=("Segoe UI", 10),
                wraplength=600,
                justify="center",
            )
            note.pack(pady=(20, 0))

    def retry_connection(self):
        """Tentar reconectar ao Pi e abrir a webview se possível."""
        if not self.is_pi_reachable():
            self.fallback_status_var.set(
                "Ainda não foi possível conectar. Confira os cabos/rede e tente novamente."
            )
            return

        if WEBVIEW_AVAILABLE:
            self.fallback_status_var.set(
                "Conexão restabelecida! Abrindo a interface web..."
            )
            self.root.after(200, self._open_webview_after_fallback)
        else:
            self.fallback_status_var.set(
                "Conectado ao Pi! Instale o pacote 'pywebview' e reabra o aplicativo "
                "para usar a interface moderna."
            )

    def _open_webview_after_fallback(self):
        """Encerrar a janela Tk e preparar a webview."""
        if not WEBVIEW_AVAILABLE:
            return
        self.pending_webview = True
        self.force_legacy_ui = False
        if self.root:
            self.root.destroy()
            self.root = None
        self.webview_window = webview.create_window(
            "Automação Médica",
            self.pi_url,
            width=1000,
            height=700,
            resizable=True,
        )

    def is_pi_reachable(self, timeout=3):
        """Verificar se a URL do Pi responde."""
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(self.pi_url, timeout=timeout)
                return response.status_code < 500
            with urllib_request.urlopen(self.pi_url, timeout=timeout) as response:
                return 200 <= getattr(response, "status", 200) < 500
            return False
        except Exception as e:
            print(f"Falha ao verificar a disponibilidade do Pi: {e}")
            traceback.print_exc()
            return False

    def create_header(self):
        """Criar cabeçalho"""
        header_frame = tk.Frame(self.root, bg=self.colors["bg_secondary"], height=80)
        header_frame.pack(fill=tk.X, padx=2, pady=2)
        header_frame.pack_propagate(False)

        # Título
        title_label = tk.Label(
            header_frame,
            text="🏥 Automação Médica",
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 20, "bold"),
        )
        title_label.pack(expand=True)

        # Subtítulo
        subtitle_label = tk.Label(
            header_frame,
            text="Neurologia",
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_secondary"],
            font=("Segoe UI", 12),
        )
        subtitle_label.pack()

    

    def create_navigation_area(self):
        """Criar área de navegação com 3 colunas"""
        nav_frame = tk.Frame(self.root, bg=self.colors["bg_primary"])
        nav_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Configurar grid
        nav_frame.grid_columnconfigure(0, weight=1)
        nav_frame.grid_columnconfigure(1, weight=1)
        nav_frame.grid_columnconfigure(2, weight=1)
        nav_frame.grid_rowconfigure(0, weight=1)

        # Coluna 1: Categorias
        self.create_list_column(nav_frame, "📋 Categorias", 0, "categories")

        # Coluna 2: Subcategorias
        self.create_list_column(nav_frame, "📑 Subcategorias", 1, "subcategories")

        # Coluna 3: Frases
        self.create_list_column(nav_frame, "💬 Frases", 2, "phrases")

    def create_list_column(self, parent, title, column, list_type):
        """Criar uma coluna de lista"""
        # Frame da coluna
        col_frame = tk.Frame(
            parent, bg=self.colors["bg_secondary"], relief="raised", bd=2
        )
        col_frame.grid(row=0, column=column, sticky="nsew", padx=2, pady=2)

        # Título
        title_label = tk.Label(
            col_frame,
            text=title,
            bg=self.colors["bg_accent"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 12, "bold"),
            pady=10,
        )
        title_label.pack(fill=tk.X)

        # Listbox
        listbox_frame = tk.Frame(col_frame, bg=self.colors["bg_secondary"])
        listbox_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        listbox = tk.Listbox(
            listbox_frame,
            bg=self.colors["bg_primary"],
            fg=self.colors["text_primary"],
            selectbackground=self.colors["bg_accent"],
            selectforeground=self.colors["text_primary"],
            font=("Segoe UI", 10),
            relief="flat",
            bd=0,
        )

        scrollbar = tk.Scrollbar(listbox_frame, orient="vertical")
        listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.configure(command=listbox.yview)

        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configurar eventos
        if list_type == "categories":
            self.categories_listbox = listbox
            listbox.bind("<<ListboxSelect>>", self.on_category_select)
        elif list_type == "subcategories":
            self.subcategories_listbox = listbox
            listbox.bind("<<ListboxSelect>>", self.on_subcategory_select)
        elif list_type == "phrases":
            self.phrases_listbox = listbox
            listbox.bind("<<ListboxSelect>>", self.on_phrase_select)

    def create_preview_area(self):
        """Criar área de preview da frase"""
        preview_frame = tk.Frame(
            self.root, bg=self.colors["bg_secondary"], relief="raised", bd=2
        )
        preview_frame.pack(fill=tk.X, padx=10, pady=5)

        # Título
        preview_title = tk.Label(
            preview_frame,
            text="👁️ Preview da Frase Selecionada",
            bg=self.colors["bg_secondary"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 12, "bold"),
            pady=5,
        )
        preview_title.pack()

        # Área de texto
        text_frame = tk.Frame(preview_frame, bg=self.colors["bg_secondary"])
        text_frame.pack(fill=tk.X, padx=10, pady=5)

        self.preview_text = tk.Text(
            text_frame,
            height=6,
            wrap=tk.WORD,
            bg=self.colors["bg_primary"],
            fg=self.colors["text_primary"],
            font=("Consolas", 10),
            relief="flat",
            bd=0,
            state="disabled",
        )

        preview_scrollbar = tk.Scrollbar(text_frame, orient="vertical")
        self.preview_text.configure(yscrollcommand=preview_scrollbar.set)
        preview_scrollbar.configure(command=self.preview_text.yview)

        self.preview_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        preview_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Botões de ação
        buttons_frame = tk.Frame(preview_frame, bg=self.colors["bg_secondary"])
        buttons_frame.pack(pady=10)

        # Botão de digitar
        self.type_button = tk.Button(
            buttons_frame,
            text="⌨️ Digitar Automaticamente (F5)",
            bg=self.colors["button_active"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 11, "bold"),
            command=self.auto_type_phrase,
            relief="raised",
            bd=2,
            padx=20,
            pady=8,
        )
        self.type_button.pack(side=tk.LEFT, padx=5)

        # Botão de copiar
        self.copy_button = tk.Button(
            buttons_frame,
            text="📋 Copiar para Clipboard",
            bg=self.colors["bg_accent"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 11, "bold"),
            command=self.copy_phrase,
            relief="raised",
            bd=2,
            padx=20,
            pady=8,
        )
        self.copy_button.pack(side=tk.LEFT, padx=5)

    def create_status_bar(self):
        """Criar barra de status"""
        self.status_bar = tk.Label(
            self.root,
            text="Pronto - Conecte-se ao Pi Zero",
            bg=self.colors["bg_accent"],
            fg=self.colors["text_primary"],
            font=("Segoe UI", 9),
            relief="sunken",
            bd=1,
            anchor="w",
            padx=10,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def setup_keyboard_shortcuts(self):
        """Configurar atalhos de teclado"""
        if not PYNPUT_AVAILABLE:
            return

        def on_press(key):      
            try:
              if hasattr(key, "vk") and key.vk:
                    # Teclas F1-F12
                    if key.vk >= 112 and key.vk <= 123:
                        fn_num = key.vk - 111
                        self.handle_function_key(fn_num)
            except AttributeError:
                pass
         
# Listener global
        try:
            self.keyboard_listener = keyboard.Listener(on_press=on_press)
            self.keyboard_listener.start()
        except Exception as e:
            print(f"Erro ao configurar atalhos globais: {e}")

    def handle_function_key(self, fn_number):
        """Processar teclas de função"""
        shortcuts = {
            1: lambda: self.quick_type(
                "Bom dia, tudo bem? Qual seria a solicitação, por gentileza?"
            ),
            2: lambda: self.quick_type(
                "Boa tarde, tudo bem? Qual seria a solicitação, por gentileza?"
            ),
            3: lambda: self.quick_type(
                "Boa noite, tudo bem? Qual seria a solicitação, por gentileza?"
            ),
            4: lambda: self.quick_type(
                "Olá, tudo bem? Um momento, por favor. Estou finalizando a discussão de outro caso."
            ),
            5: self.auto_type_phrase,
            
            11: self.toggle_fullscreen,
        }

        if fn_number in shortcuts:
            threading.Thread(target=shortcuts[fn_number], daemon=True).start()

    def load_categories(self):
        """Carregar categorias do Pi"""
        if not REQUESTS_AVAILABLE:
            self.update_status("Biblioteca requests não disponível.")
            return

        try:
            response = requests.get(f"{self.pi_url}/api/categorias", timeout=3)
            if response.status_code == 200:
                self.categories = response.json()
                self.update_categories_listbox()
                self.update_status("Conectado ao Pi Zero - Categorias carregadas")
            else:
                self.update_status("Erro ao conectar com Pi Zero")
        except Exception as e:
            self.update_status(f"Não foi possível conectar ao Pi: {e}")

    def update_categories_listbox(self):
        """Atualizar listbox de categorias"""
        self.categories_listbox.delete(0, tk.END)
        for category in self.categories:
            self.categories_listbox.insert(tk.END, category)

    def on_category_select(self, event):
        """Evento de seleção de categoria"""
        selection = self.categories_listbox.curselection()
        if selection:
            self.selected_category = self.categories[selection[0]]
            self.load_subcategories()

    def load_subcategories(self):
        """Carregar subcategorias"""
        if not REQUESTS_AVAILABLE:
            self.update_status("Biblioteca requests não disponível.")
            return

        try:
            url = f"{self.pi_url}/api/subcategorias/{self.selected_category}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                self.subcategories = response.json()
                self.update_subcategories_listbox()
                # Limpar frases
                self.phrases_listbox.delete(0, tk.END)
                self.clear_preview()
        except Exception as e:
            self.update_status(f"Erro ao carregar subcategorias: {e}")

    def update_subcategories_listbox(self):
        """Atualizar listbox de subcategorias"""
        self.subcategories_listbox.delete(0, tk.END)
        for subcategory in self.subcategories:
            self.subcategories_listbox.insert(tk.END, subcategory)

    def on_subcategory_select(self, event):
        """Evento de seleção de subcategoria"""
        selection = self.subcategories_listbox.curselection()
        if selection and self.selected_category:
            self.selected_subcategory = self.subcategories[selection[0]]
            self.load_phrases()

    def load_phrases(self):
        """Carregar frases"""
        if not REQUESTS_AVAILABLE:
            self.update_status("Biblioteca requests não disponível.")
            return

        try:
            url = f"{self.pi_url}/api/frases/{self.selected_category}/{self.selected_subcategory}"
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                self.phrases = response.json()
                self.update_phrases_listbox()
                self.clear_preview()
        except Exception as e:
            self.update_status(f"Erro ao carregar frases: {e}")

    def update_phrases_listbox(self):
        """Atualizar listbox de frases"""
        self.phrases_listbox.delete(0, tk.END)
        for phrase in self.phrases:
            display_text = f"{phrase['ordem']}. {phrase['nome']}"
            self.phrases_listbox.insert(tk.END, display_text)

    def on_phrase_select(self, event):
        """Evento de seleção de frase"""
        selection = self.phrases_listbox.curselection()
        if selection:
            self.current_phrase = self.phrases[selection[0]]
            self.update_preview()

    def update_preview(self):
        """Atualizar preview da frase"""
        if self.current_phrase:
            content = self.current_phrase["conteudo"]
            # Normalizar quebras de linha
            content = content.replace("\\n", "\n")

            self.preview_text.config(state="normal")
            self.preview_text.delete(1.0, tk.END)
            self.preview_text.insert(1.0, content)
            self.preview_text.config(state="disabled")

            self.update_status(f"Frase selecionada: {self.current_phrase['nome']}")

    def clear_preview(self):
        """Limpar preview"""
        self.preview_text.config(state="normal")
        self.preview_text.delete(1.0, tk.END)
        self.preview_text.config(state="disabled")
        self.current_phrase = None

    def auto_type_phrase(self):
        """Digitar frase automaticamente"""
        if not self.current_phrase:
            messagebox.showwarning("Aviso", "Selecione uma frase primeiro!")
            return

        if not AUTOGUI_AVAILABLE:
            messagebox.showerror("Erro", "PyAutoGUI não disponível")
            return

        self.update_status("Digitação automática em 2 segundos...")

        def type_text():
            time.sleep(2)
            text = self.current_phrase["conteudo"].replace("\\n", "\n")
            pyautogui.write(text)
            self.root.after(
                100, lambda: self.update_status("Frase digitada automaticamente!")
            )

        threading.Thread(target=type_text, daemon=True).start()

    def quick_type(self, text):
        """Digitar texto rápido"""
        if not AUTOGUI_AVAILABLE:
            return

        def type_text():
            time.sleep(1)
            pyautogui.write(text)
            self.root.after(
                100, lambda: self.update_status(f"Digitado: {text[:30]}...")
            )

        threading.Thread(target=type_text, daemon=True).start()

    def copy_phrase(self):
        """Copiar frase para clipboard"""
        if not self.current_phrase:
            messagebox.showwarning("Aviso", "Selecione uma frase primeiro!")
            return

        text = self.current_phrase["conteudo"].replace("\\n", "\n")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.update_status("Frase copiada para clipboard!")

    

    

    def toggle_minimize(self):
        """Alternar minimização"""
        if not self.root:
            return
        if self.root.state() == "normal":
            self.root.iconify()
        else:
            self.root.deiconify()
            self.root.lift()

    def toggle_fullscreen(self):
        """Alternar tela cheia"""
        if not self.root:
            return
        current = self.root.attributes("-fullscreen")
        self.root.attributes("-fullscreen", not current)

    def update_status(self, message):
        """Atualizar barra de status"""
        if hasattr(self, "status_bar") and self.status_bar:
            self.status_bar.config(text=message)
        else:
            print(message)

    def run(self):
        """Executar aplicação"""
        if platform.system() != "Windows":
            return

        if self.ui_mode == "webview":
            webview_started = self.start_webview_runtime()
            if webview_started:
                return

        try:
            if self.root:
                self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

        if self.pending_webview:
            self.ui_mode = "webview"
            self.start_webview_runtime()

    def cleanup(self):
        """Limpeza ao fechar"""
        
        if hasattr(self, "keyboard_listener"):
            self.keyboard_listener.stop()

    def start_webview_runtime(self):
        """Iniciar o loop da webview se disponível."""
        if not WEBVIEW_AVAILABLE or not self.webview_window:
            return False
        try:
            webview.start()
            return True
        except Exception as exc:
            error_message = f"Erro ao iniciar a interface web: {exc}"
            print(error_message)
            traceback.print_exc()
            pause_for_user(
                "Não foi possível abrir a interface web. Pressione Enter para continuar no modo legado.",
                delay_seconds=2,
            )
            self.pending_webview = False
            self.webview_window = None
            self.force_legacy_ui = True

            if not self.root:
                self.setup_gui()
                if self.ui_mode == "legacy":
                    self.initialize_legacy_mode()

            if self.root:
                try:
                    self.root.after(
                        0,
                        lambda: self.update_status(
                            "Interface web indisponível. Utilizando modo legado."
                        ),
                    )
                except Exception as e:
                    print(f"Falha ao agendar atualização de status: {e}")
                    self.update_status("Interface web indisponível. Utilizando modo legado.")

            return False
def main():
    """Função principal."""
    # Verificar sistema operacional
    if platform.system() != "Windows":
        print("Este cliente só funciona no Windows.")
        print("Para outros sistemas, use a interface web: http://pi.local:8080")
        sys.exit(0)

    print("Iniciando cliente desktop para Windows...")

    # Verificar dependências
    missing_deps = []
    if not REQUESTS_AVAILABLE:
        missing_deps.append("requests")
    
    if not AUTOGUI_AVAILABLE:
        missing_deps.append("pyautogui")
    if not PYNPUT_AVAILABLE:
        missing_deps.append("pynput")

    if missing_deps:
        print("Dependências opcionais não encontradas:")
        for dep in missing_deps:
            print(f"  - {dep}")
        print("Para instalar: pip install " + " ".join(missing_deps))
        print("O cliente funcionará com funcionalidades limitadas.")
        pause_for_user("Pressione Enter para continuar...")

    # Iniciar cliente
    try:
        client = WindowsDesktopClient()
        client.run()
    except Exception as e:
        print(f"Erro inesperado ao executar o cliente: {e}")
        traceback.print_exc()
        pause_for_user("Ocorreu um erro inesperado. Pressione Enter para sair.")
if __name__ == "__main__":
    main()
