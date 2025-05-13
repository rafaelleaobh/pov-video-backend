# Lista de Tarefas - Implantação em Nuvem POV Video Generator

- [x] 001: Pesquisar opções de plataformas gratuitas para backend (Flask) e frontend (React).
- [x] 002: Selecionar a melhor combinação de plataformas (backend e frontend) e documentar os limites, vantagens e a justificativa da escolha.
- [x] 003: Preparar o projeto backend (Flask) para deploy na plataforma escolhida (ex: criar `render.yaml` ou `Procfile`, ajustar `requirements.txt`, configurar Gunicorn).
- [x] 004: Preparar o projeto frontend (React) para deploy na plataforma escolhida (ex: configurar build, variáveis de ambiente para API backend).
- [x] 005: Corrigir imports do backend (ajuste de path do módulo integrations) para garantir compatibilidade com o ambiente de produção na nuvem.
- [x] 006: Ajustar o backend para ler as credenciais do Google a partir de um "Secret File" (via variável de ambiente GOOGLE_APPLICATION_CREDENTIALS).
- [ ] 007: Orientar o usuário sobre como fazer o upload do arquivo JSON de credenciais do Google como "Secret File" no Render e configurar a variável de ambiente `GOOGLE_APPLICATION_CREDENTIALS`.
- [ ] 008: Executar o deploy do backend no Render após configuração do Secret File.
- [ ] 009: Validar o funcionamento da integração com Google (Sheets e Gmail) no backend.
- [ ] 010: Executar o deploy do frontend no Vercel.
- [ ] 011: Validar o funcionamento completo da aplicação online (frontend e backend integrados, funcionalidades principais).
- [ ] 012: Fornecer o link público da aplicação e instruções de uso simplificadas ao usuário.
- [ ] 013: Reportar progresso e próximos passos ao usuário (se houver pendências) ou finalizar a tarefa.
