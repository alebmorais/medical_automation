# Automação Médica

Este repositório contém os artefatos para um sistema de automação de frases médicas, composto por um servidor web (ideal para Raspberry Pi) e um cliente desktop para Windows.

O sistema permite acessar rapidamente um banco de dados de frases e protocolos médicos através de uma interface web amigável.

## Configuração e Instalação (Raspberry Pi)

Estas instruções são otimizadas para um Raspberry Pi com Raspberry Pi OS (ou qualquer sistema baseado em Debian).

### 1. Preparação do Sistema

Abra o terminal e execute os seguintes comandos para atualizar o sistema e instalar as dependências essenciais:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install git sqlite3 python3 -y
```

### 2. Clonar o Repositório

Clone este projeto para o seu dispositivo:

```bash
git clone https://github.com/alebmorais/phrases_automation.git
cd phrases_automation
```
*Observação: O nome do repositório pode variar. Ajuste o comando `git clone` se necessário.*

### 3. Executando o Servidor

O projeto inclui um servidor inteligente (`ServidorCode2`) que configura o banco de dados automaticamente.

Para iniciar, basta executar:

```bash
python3 ServidorCode2
```

Ao ser executado pela primeira vez, o servidor irá:
1.  Procurar por um arquivo de banco de dados (`automation.db`).
2.  Se não o encontrar, ele buscará um arquivo SQL de referência (como `SQL2.sql` ou `SQL_File.sql`) no diretório e o usará para **criar e popular o banco de dados automaticamente**.
3.  Após a configuração, o servidor iniciará na porta `8080`.

### 4. Acessando a Interface

Após iniciar o servidor, você pode acessar a aplicação de duas formas:
*   **Localmente no Pi:** Abra um navegador e acesse `http://localhost:8080`.
*   **De outro dispositivo na mesma rede:** Use o endereço `http://<ip-do-seu-pi>:8080` (ex: `http://192.168.1.10`).

---

## Cliente Desktop (Windows)

O cliente para Windows funciona como um "navegador dedicado" para a interface web hospedada no Raspberry Pi.

### Requisitos

1.  **Python 3.10+** instalado no Windows.
2.  **Dependências Python:** `pywebview` (recomendado), `requests`. Para funcionalidades completas (digitação automática e atalhos globais), instale também `pyautogui` e `pynput`.
3.  **[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)**: Geralmente já incluído no Windows 11. Para Windows 10, pode ser necessário instalar manualmente.

### Instalação das Dependências

Com o Python instalado, execute no PowerShell ou CMD:

```bash
pip install pywebview requests pyautogui pynput
```

### Execução

Para iniciar o cliente, execute o script `ClienteWindows`:

```bash
python ClienteWindows
```

O aplicativo tentará se conectar a `http://pi.local:8080`. Se o servidor no Raspberry Pi estiver no ar e na mesma rede, a interface será exibida. Caso contrário, uma mensagem de erro aparecerá com um botão para tentar novamente.

---

## Solução de Problemas

*   **O servidor não inicia ou o banco de dados não é criado:**
    *   Verifique se um arquivo SQL de referência (como `SQL2.sql` ou `SQL_File.sql`) está presente no diretório do projeto. O servidor prioriza `SQL2.sql`.
    *   Certifique-se de que você tem permissão para criar arquivos no diretório onde o servidor está sendo executado.
*   **Criação manual do banco de dados:** Se a criação automática falhar, você pode criar o banco manualmente com o seguinte comando (use o arquivo SQL mais recente):
    ```bash
    sqlite3 automation.db < SQL2.sql
    ```
    Mova o arquivo `automation.db` gerado para o mesmo diretório do `ServidorCode2` e tente executá-lo novamente.
*   **Cliente Windows não conecta:**
    *   Verifique se o Raspberry Pi e o computador Windows estão na mesma rede Wi-Fi.
    *   Tente acessar `http://<ip-do-seu-pi>:8080` diretamente no navegador do Windows para confirmar a conectividade.
    *   Certifique-se de que o WebView2 Runtime está instalado.


