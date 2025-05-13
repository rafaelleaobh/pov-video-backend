# Guia Visual Simplificado: Deploy do POV Video Backend

Olá! Este guia vai te ajudar a colocar o backend do seu projeto POV Video Generator no ar, usando o arquivo ZIP que preparei e a plataforma Render, de uma forma mais visual e com o mínimo de interação técnica possível.

**Pré-requisitos:**

1.  **Conta no GitHub Criada:** Conforme conversamos, você precisará de uma conta no GitHub.
2.  **Arquivo ZIP do Backend:** O arquivo `pov_video_backend_corrected_final.zip` que preparei para você.
3.  **Arquivo de Credenciais do Google:** O seu arquivo `gen-lang-client-xxxxxxxxxxxx-xxxxxxxxxxxxxxxx.json` (o nome pode variar um pouco).
4.  **Suas Chaves de API:**
    *   OpenAI API Key
    *   HuggingFace API Key
    *   RunwayML API Key
    *   ID da sua Planilha Google Sheets
    *   Email para notificações do Gmail

**Passo 1: Preparar o Repositório no GitHub**

1.  **Crie um Novo Repositório no GitHub:**
    *   Acesse o [GitHub](https://github.com/) e faça login.
    *   No canto superior direito, clique no ícone de "+" e selecione "New repository".
    *   **Repository name:** Dê um nome simples, por exemplo, `meu-pov-backend`.
    *   Deixe como **Public**.
    *   Clique em **"Create repository"**.
    *   *Visual:* (Imagine aqui uma captura de tela do GitHub mostrando o formulário de criação de repositório).

2.  **Faça Upload dos Arquivos do Backend para o GitHub:**
    *   Baixe e descompacte o arquivo `pov_video_backend_corrected_final.zip` no seu computador. Você terá uma pasta chamada `pov_video_generator`.
    *   Na página do seu novo repositório no GitHub, clique em "**Add file**" e depois em "**Upload files**".
    *   *Visual:* (Imagine uma captura de tela do GitHub mostrando o botão "Add file" > "Upload files").
    *   Arraste **todo o conteúdo** da pasta `pov_video_generator` (ou seja, a pasta `src`, o arquivo `requirements.txt`, o arquivo `render.yaml`, etc.) para a área de upload do GitHub.
        *   **Importante:** Não suba a pasta `pov_video_generator` em si, mas sim o que está *dentro* dela, diretamente na raiz do seu repositório.
    *   Após o upload, adicione uma mensagem de commit (ex: "Initial backend code") e clique em "**Commit changes**".
    *   *Visual:* (Imagine uma captura de tela do GitHub mostrando os arquivos sendo arrastados e o botão "Commit changes").

**Passo 2: Configurar o Serviço no Render**

1.  **Crie um Novo Web Service no Render:**
    *   Acesse o [Render](https://dashboard.render.com/) e faça login.
    *   Clique em "**+ New**" (ou "+ Add new") e selecione "**Web Service**".
    *   *Visual:* (Imagine uma captura de tela do Render mostrando o botão "+ New" > "Web Service").
    *   Conecte sua conta do GitHub ao Render se ainda não o fez.
    *   Selecione o repositório que você acabou de criar (ex: `meu-pov-backend`).

2.  **Configure os Detalhes do Serviço:**
    *   **Name:** Dê um nome único para seu serviço (ex: `meu-pov-backend-app`). O Render usará isso para a URL.
    *   **Region:** Escolha a região mais próxima de você (ex: Oregon (US West)).
    *   **Branch:** `main` (ou a branch principal do seu repositório).
    *   **Root Directory:** Deixe **em branco** (já que subimos o conteúdo da pasta `pov_video_generator` diretamente para a raiz do repositório).
    *   **Environment:** Selecione `Python`.
    *   **Build Command:** O Render deve detectar automaticamente a partir do `render.yaml` (`pip install -r requirements.txt`). Se não, preencha.
    *   **Start Command:** O Render deve detectar automaticamente (`gunicorn src.main:app`). Se não, preencha.
    *   **Plan:** Escolha o plano **Free**.
    *   *Visual:* (Imagine uma captura de tela do Render mostrando esses campos de configuração).
    *   Clique em "**Create Web Service**". O Render começará o primeiro deploy (que pode falhar inicialmente por falta das variáveis de ambiente, e tudo bem).

**Passo 3: Configurar Variáveis de Ambiente e Secret File no Render**

Depois que o serviço for criado (mesmo que o primeiro deploy falhe), vá para a página do seu serviço no Render.

1.  **Acesse a Aba "Environment":**
    *   No menu lateral do seu serviço, clique em "**Environment**".
    *   *Visual:* (Imagine uma captura de tela do Render mostrando a aba "Environment").

2.  **Adicione o "Secret File" para as Credenciais do Google:**
    *   Role para baixo até a seção "**Secret Files**".
    *   Clique em "**Add Secret File**".
    *   **Filename / Mount Path:** Digite `google_credentials.json`.
    *   **Content:** Abra o seu arquivo de credenciais do Google (`gen-lang-client-....json`) no seu computador, copie **todo o conteúdo** dele e cole neste campo "Content".
    *   *Visual:* (Imagine uma captura de tela do Render mostrando a adição do Secret File).
    *   Clique em "**Save Changes**". O Render informará o caminho onde o arquivo será montado (ex: `/etc/secrets/google_credentials.json`). Anote este caminho!

3.  **Adicione as Variáveis de Ambiente:**
    *   Ainda na aba "Environment", vá para a seção "**Environment Variables**".
    *   Clique em "**Add Environment Variable**" para cada uma das seguintes variáveis:
        *   **Key:** `GOOGLE_APPLICATION_CREDENTIALS`
            *   **Value:** O caminho completo que o Render te deu para o Secret File (ex: `/etc/secrets/google_credentials.json`).
        *   **Key:** `OPENAI_API_KEY`
            *   **Value:** Sua chave da API da OpenAI.
        *   **Key:** `HUGGINGFACE_API_KEY`
            *   **Value:** Sua chave da API da HuggingFace.
        *   **Key:** `RUNWAYML_API_KEY`
            *   **Value:** Sua chave da API da RunwayML.
        *   **Key:** `GOOGLE_SPREADSHEET_ID`
            *   **Value:** O ID da sua planilha do Google Sheets.
        *   **Key:** `GMAIL_RECIPIENT`
            *   **Value:** O email para onde as notificações do Gmail serão enviadas.
    *   *Visual:* (Imagine uma captura de tela do Render mostrando a adição de uma variável de ambiente).
    *   Após adicionar todas, clique em "**Save Changes**".

**Passo 4: Deploy e Verificação**

1.  **Aguarde o Novo Deploy:**
    *   Salvar as variáveis de ambiente e o Secret File geralmente aciona um novo deploy automaticamente no Render.
    *   Acompanhe o status na aba "Events" ou na visão geral do serviço.
    *   Espere até que o status seja "**Live**" ou "Deploy successful".
    *   *Visual:* (Imagine uma captura de tela do Render mostrando um deploy bem-sucedido).

2.  **Verifique a URL:**
    *   A URL pública do seu backend (ex: `https://meu-pov-backend-app.onrender.com`) estará visível na página do seu serviço.

**Pronto!** Se tudo correu bem, seu backend estará no ar e funcionando.

Por favor, siga estes passos com calma. Se algo não estiver claro ou você encontrar alguma dificuldade, me avise em qual passo você está e o que está acontecendo!

