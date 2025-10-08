# Automação Médica

Este repositório contém experimentos e protótipos utilizados na automação do consultório da Dra. Alessandra Morais. Os artefatos principais são o servidor web (Raspberry Pi) e o cliente desktop para Windows.

## Primeiros Passos no Raspberry Pi Zero 2W (Raspberry Pi OS Lite 32-bit)

1.  **Atualize o sistema:**
    ```bash
    sudo apt update && sudo apt upgrade -y
    ```

2.  **Instale o Git e o SQLite3:**
    ```bash
    sudo apt install git sqlite3 -y
    ```

3.  **Clone este repositório:**
    ```bash
    git clone https://github.com/alebmorais/alebmorais.github.io.git
    cd alebmorais.github.io
    ```

4.  **Continue para a preparação do banco de dados e execução do servidor (seções abaixo).**

---

## Servidor Web Raspberry Pi

### Requisitos

1. **Python 3.10+** (testado no Raspberry Pi OS Bookworm)
2. Banco SQLite populado com o conteúdo do repositório (veja seção a seguir)

### Executando o servidor

Escolha o script desejado:

| Script          | Comando                 | Porta padrão |
|-----------------|-------------------------|--------------|
| `ServidorCode`  | `python3 ServidorCode`  | `8080`       |
| `ServidorCode2` | `python3 ServidorCode2` | `8080`       |

Ambas as versões expõem a interface em `http://pi.local:8080` (ou `http://<ip-do-pi>:8080`).

### Variáveis de ambiente e caminhos do banco

- `DB_PATH`: caminho absoluto para o arquivo `automation.db` utilizado pelo `ServidorCode`.
- `AUTOMATION_DB_PATH`: caminho preferencial para o banco no `ServidorCode2` (se ausente, ele volta para `DB_PATH`).

Se nenhuma variável estiver definida, o `ServidorCode` utiliza como padrão `/home/pi/automation.db`. A versão 2, por sua vez, procura automaticamente por arquivos como `automation.db` ou `database/automation.db` no diretório do script e no diretório pai.

### Preparando o banco `automation.db`

1. Copie o repositório para o Raspberry Pi (incluindo os arquivos `SQL_Filesqlite3` e `SQL_2`).
2. Gere o banco de dados a partir do SQL principal:

   ```bash
   sqlite3 automation.db < SQL_Filesqlite3
   ```

3. Opcional: importe complementos contidos em `SQL_2` executando novamente `sqlite3 automation.db < SQL_2`.
4. Mova o arquivo resultante para o caminho desejado (`/home/pi/automation.db`, `~/database/automation.db`, etc.) e ajuste `DB_PATH`/`AUTOMATION_DB_PATH` conforme necessário.

> 💡 O `ServidorCode2` tenta criar automaticamente o banco ao detectar `SQL_Filesqlite3`, `SQL_Filesqlite3.sql` ou arquivos equivalentes nos diretórios `.` ou `./database`. Ainda assim, manter o processo manual documentado garante repetibilidade em ambientes limpos.

### Checklist de verificação

1. Inicie o servidor desejado (`python3 ServidorCode2`).
2. No navegador, acesse `http://pi.local:8080` (ou o IP informado no terminal) e confirme se as categorias são carregadas na barra lateral.
3. Se o banco não carregar, confirme o caminho definido em `DB_PATH`/`AUTOMATION_DB_PATH` e verifique se `automation.db` contém a tabela `frases` com registros (`sqlite3 automation.db "SELECT COUNT(*) FROM frases;"`).

---

## Cliente Desktop Windows

O cliente Windows foi atualizado para reutilizar diretamente a interface web hospedada no Raspberry Pi. Para isso ele abre um _webview_ leve apontando para `http://pi.local:8080` sempre que o dispositivo está acessível.

### Dependências obrigatórias

1. **Python 3.10+**
2. **[pywebview](https://pywebview.flowrl.com/)**
3. **[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)** (já vem com o Windows 11, mas inclua o instalador offline no pacote para Windows 10)

Instalação sugerida via `pip`:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install pywebview requests pyautogui pynput
```

Durante o empacotamento com PyInstaller ou similares, garanta que o módulo `pywebview` esteja listado nas dependências e distribua o instalador do WebView2 (`MicrosoftEdgeWebView2RuntimeInstallerX64.exe`) junto com o executável para que o usuário possa instalá-lo antes da primeira execução.

### Comportamento offline

Se o Raspberry Pi não puder ser alcançado, o cliente mostra uma tela simples com instruções para conectar-se à mesma rede e um botão **"Tentar novamente"**. Assim que a conexão for restabelecida, a interface web será carregada automaticamente. Caso o `pywebview` não esteja instalado, a tela avisará o usuário para instalar o pacote e reabrir o aplicativo.

### Execução

```powershell
```

O arquivo `ClienteWindows` mantém uma versão alternativa com os mesmos aprimoramentos e pode ser invocado da mesma forma.

---

Para executar diretamente a interface web sem o cliente desktop, acesse `http://pi.local:8080` a partir de um navegador moderno conectado à mesma rede.

