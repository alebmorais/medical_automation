# Sistema de Automação Médica

Este guia completo transforma um Raspberry Pi em um servidor dedicado para o sistema de automação médica. As instruções são voltadas para iniciantes, desde a preparação do cartão SD até o acesso final.

## Parte 1: Configuração do Servidor no Raspberry Pi

**Hardware Necessário:**
*   Raspberry Pi Zero 2 W (ou outro modelo)
*   Cartão MicroSD (16 GB ou mais, de boa qualidade)
*   Fonte de alimentação USB compatível

---

### Passo 1: Preparando o Cartão SD (Antes de Ligar o Pi)

Vamos configurar o sistema operacional, o Wi-Fi e o acesso remoto antes mesmo de colocar o cartão no Raspberry Pi. Isso é conhecido como modo *headless*.

1.  **Baixe o Raspberry Pi Imager:**
    *   Acesse o site oficial do Raspberry Pi e baixe a ferramenta "Imager" para o seu computador (Windows, Mac ou Linux):
        [https://www.raspberrypi.com/software/](https://www.raspberrypi.com/software/)

2.  **Grave o Sistema Operacional:**
    *   Abra o Raspberry Pi Imager e insira o cartão SD no seu computador.
    *   **CHOOSE DEVICE**: Selecione "Raspberry Pi Zero 2 W".
    *   **CHOOSE OS**: Clique em "Raspberry Pi OS (other)" e selecione **"Raspberry Pi OS Lite (32-bit)"**. A versão Lite não tem interface gráfica e é ideal para servidores.
    *   **CHOOSE STORAGE**: Selecione o seu cartão MicroSD.
    *   Clique em **NEXT**.

3.  **Pré-configure o Sistema:**
    *   Na janela "Customise settings", clique em **"EDIT SETTINGS"**.
    *   **Aba "General"**:
        *   Marque **"Set hostname"** e defina um nome. Sugestão: `pi-medico.local`.
        *   Defina um **nome de usuário** e **senha**. Anote-os, pois você precisará deles.
    *   **Aba "Services"**:
        *   Marque **"Enable SSH"** e selecione "Use password authentication". Isso permite o acesso remoto.
    *   **Aba "Wireless LAN"**:
        *   Marque **"Configure wireless LAN"**.
        *   **SSID**: Digite o nome da sua rede Wi-Fi.
        *   **Password**: Digite a senha da sua rede Wi-Fi.
        *   **Wireless LAN country**: Selecione o seu país (ex: `BR` para Brasil).
    *   Clique em **SAVE** e depois em **YES** para iniciar a gravação. O processo pode levar alguns minutos.

4.  **Ejetar o Cartão:** Após a conclusão, ejete o cartão SD com segurança e insira-o no seu Raspberry Pi.

---

### Passo 2: Primeiro Acesso e Configuração Inicial

1.  **Ligue o Raspberry Pi:** Conecte a fonte de alimentação. Aguarde 1-2 minutos para ele iniciar e se conectar ao Wi-Fi.

2.  **Acesse o Pi via SSH:**
    *   Abra o terminal do seu computador (no Windows, pode ser o PowerShell ou CMD).
    *   Digite o comando abaixo, usando o nome de usuário e o hostname que você configurou:
        ```bash
        ssh seu_usuario@pi-medico.local
        ```
        *Se `pi-medico.local` não funcionar, você precisará encontrar o endereço IP do Pi no seu roteador e usar `ssh seu_usuario@<endereco-ip>`.*
    *   Digite a senha que você criou.

3.  **Atualize o Sistema:**
    *   Comandos para garantir que todos os pacotes estão na versão mais recente:
        ```bash
        sudo apt update && sudo apt upgrade -y
        ```

---

### Passo 3: Instalação do Projeto

1.  **Instale as Dependências:**
    *   O projeto precisa de `git` para clonar o repositório e `sqlite3` para o banco de dados.
        ```bash
        sudo apt install git sqlite3 python3 -y
        ```

2.  **Clone o Repositório:**
    *   Baixe os arquivos do projeto para o seu Pi:
        ```bash
        git clone https://github.com/alebmorais/medical_automation.git
        ```

3.  **Entre no Diretório do Projeto:**
    ```bash
    cd medical_automation
    ```

4.  **Teste o Servidor (Opcional):**
    *   Para garantir que tudo está funcionando, você pode iniciar o servidor manualmente:
        ```bash
        python3 ServidorCode2
        ```
    *   Ele deve exibir uma mensagem de que o banco de dados foi criado e o servidor está rodando.
    *   Pressione `Ctrl + C` para parar o servidor.

---

### Passo 4: Configurar o Servidor para Iniciar Automaticamente

Para que o sistema funcione como um aparelho dedicado, ele deve iniciar sozinho sempre que o Pi for ligado.

1.  **Crie um Arquivo de Serviço `systemd`:**
    *   Use o editor de texto `nano` para criar o arquivo de configuração:
        ```bash
        sudo nano /etc/systemd/system/medical-automation.service
        ```

2.  **Cole o Conteúdo Abaixo:**
    *   Copie e cole o texto a seguir no editor `nano`. **Importante:** Substitua `seu_usuario` pelo nome de usuário que você criou para o Pi.

        ```ini
        [Unit]
        Description=Medical Automation Server
        After=network.target

        [Service]
        User=seu_usuario
        WorkingDirectory=/home/seu_usuario/medical_automation
        ExecStart=/usr/bin/python3 /home/seu_usuario/medical_automation/ServidorCode2
        Restart=always

        [Install]
        WantedBy=multi-user.target
        ```

3.  **Salve e Feche o Arquivo:**
    *   Pressione `Ctrl + X`.
    *   Pressione `Y` para confirmar que deseja salvar.
    *   Pressione `Enter` para confirmar o nome do arquivo.

4.  **Ative e Inicie o Serviço:**
    *   **Recarregue o systemd:** `sudo systemctl daemon-reload`
    *   **Ative o serviço para iniciar no boot:** `sudo systemctl enable medical-automation.service`
    *   **Inicie o serviço agora:** `sudo systemctl start medical-automation.service`

5.  **Verifique o Status (Opcional):**
    *   Para ver se o servidor está rodando corretamente, use:
        ```bash
        sudo systemctl status medical-automation.service
        ```
    *   Pressione `Q` para sair.

Seu servidor agora está configurado e rodando! Você pode desconectar do SSH. Ele continuará funcionando e iniciará automaticamente sempre que for ligado.

---

### Passo 5: Acessando a Aplicação

*   Abra um navegador em qualquer computador, tablet ou celular na mesma rede Wi-Fi.
*   Acesse o endereço: `http://pi-medico.local:8080` (ou `http://<endereco-ip-do-pi>:8080`).

## Parte 2: Cliente Desktop para Windows

O cliente Windows funciona como um "navegador dedicado" para a interface web, com funcionalidades extras.

### Requisitos

1.  **Python 3.10+** instalado no Windows.
2.  **Dependências Python:** `pywebview` (cria a janela), `requests` (comunicação), `pyautogui` e `pynput` (para digitação automática e atalhos globais).
3.  **[Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/en-us/microsoft-edge/webview2/)**: Geralmente já incluído no Windows 11. Para Windows 10, pode ser necessário instalar manualmente.

### Instalação das Dependências

Com o Python instalado, abra o **PowerShell** ou **CMD** no Windows e execute:

```bash
pip install pywebview requests pyautogui pynput
```

### Execução

Para iniciar o cliente, execute o script `ClienteWindows`:

```bash
python ClienteWindows
```

O aplicativo tentará se conectar a `http://pi-medico.local:8080`. Se o servidor no Raspberry Pi estiver no ar, a interface será exibida.


