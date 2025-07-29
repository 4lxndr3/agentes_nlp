

# 🤖 Agente de Estudos Personalizado com IA

Este projeto é uma solução completa de agente autônomo que transforma uma coleção de provas antigas em formato PDF em um plano de estudos inteligente, interativo e personalizado, agendado diretamente no seu Google Calendar.

O sistema utiliza Modelos de Linguagem Grandes (LLM) do Google (Gemini) para analisar, classificar, resumir e conversar com o usuário, criando uma experiência de planejamento de estudos verdadeiramente assistida por IA.

## ✨ Principais Funcionalidades

  * **Análise e Classificação Automática:** O agente lê múltiplos PDFs, identifica as páginas relevantes e classifica cada questão por matéria e assunto específico.
  * **Geração de Resumos Teóricos com IA:** Para cada tópico identificado, o agente gera uma explicação teórica concisa, explicando os conceitos fundamentais necessários para resolver as questões daquele tópico.
  * **Criação de Material de Estudo Focado:** Gera novos PDFs para cada assunto, contendo o resumo teórico seguido por todas as questões relacionadas àquele tema, com formatação otimizada para estudo.
  * **Análise de Agenda:** O agente se conecta ao seu Google Calendar para analisar seus padrões de horários e identificar os períodos mais livres para o estudo.
  * **Agendamento Conversacional Inteligente:** Em vez de um formulário rígido, você interage com um agente via chat. Ele sugere os melhores horários com base na análise da sua agenda e conversa com você para definir suas preferências (ritmo de estudo, prioridades, etc.).
  * **Verificação de Agendamento:** Após agendar, o sistema verifica se os eventos foram de fato criados no seu calendário, informando o sucesso da operação e listando eventuais falhas.
  * **Utilitário de Limpeza:** Inclui um script separado para apagar com segurança todos os eventos criados pelo agente, facilitando testes e reorganizações.

## 🏗️ Arquitetura do Sistema

O projeto é modular e segue boas práticas de engenharia de software, dividido em:

1.  **Orquestrador Principal (`orchestrator.py`):** O cérebro do sistema, que gerencia o fluxo de análise e agendamento.
2.  **Agentes de IA:**
      * `TopicClassifier`: Especialista em classificar o conteúdo dos PDFs.
      * `ConversationalPlanner`: Especialista em conversar com o usuário e definir as preferências do cronograma.
3.  **Ferramentas (`tools/`):** Módulos especializados em tarefas como ler PDFs, gerar novos PDFs e interagir com as APIs do Google.

## ✅ Pré-requisitos

  * Python 3.10 ou superior.
  * Uma conta Google.
  * Acesso à internet para as APIs do Google.

## 🚀 Configuração do Ambiente (Passo a Passo)

Siga estes passos com atenção para configurar seu ambiente de execução.

### Passo 1: Preparar o Projeto e Dependências

1.  Clone ou salve o projeto em uma pasta no seu computador.
2.  Abra um terminal nessa pasta.
3.  **Recomendado:** Crie e ative um ambiente virtual para isolar as dependências:
    ```bash
    python3 -m venv .env
    source .env/bin/activate
    # No Windows, use: .env\Scripts\activate
    ```
4.  Instale todas as bibliotecas necessárias com um único comando:
    ```bash
    pip install -r requirements.txt
    ```

### Passo 2: Configurar a API do Google Gemini (IA)

1.  Acesse o [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Clique em "Create API key" para gerar sua chave.
3.  Dentro da pasta do projeto, encontre a subpasta `config/`. Crie um arquivo chamado `.env` dentro dela.
4.  Adicione sua chave de API a este arquivo, da seguinte forma:
    ```
    GOOGLE_API_KEY="SUA_CHAVE_API_AQUI"
    ```

### Passo 3: Configurar a API do Google Calendar
obs: eu acho que com o meu arquivo de credentials funciona
1.  Acesse o [Google Cloud Console](https://console.cloud.google.com/).
2.  Crie um novo projeto (ex: "Agente de Estudos").
3.  No menu de navegação, vá para **"APIs e serviços" \> "APIs e serviços ativados"**.
4.  Clique em **"+ ATIVAR APIS E SERVIÇOS"**, procure por **"Google Calendar API"** e ative-a.
5.  Volte para **"APIs e serviços"** e vá para **"Tela de consentimento OAuth"**:
      * Escolha **"Externo"** e clique em "Criar".
      * Preencha o nome do aplicativo (ex: "Study Planner Agent"), seu e-mail de suporte e e-mail de contato. Salve e continue.
      * Na tela "Escopos", não precisa adicionar nada. Salve e continue.
      * Na tela "Usuários de teste", clique em **"+ ADD USERS"** e adicione seu próprio endereço de e-mail. Salve e continue.
6.  Volte para **"APIs e serviços"** e vá para **"Credenciais"**:
      * Clique em **"+ CRIAR CREDENCIAIS"** e selecione **"ID do cliente OAuth"**.
      * No campo "Tipo de aplicativo", selecione **"App para computador"**.
      * Clique em **"CRIAR"**.
      * Faça o download do arquivo JSON. **Renomeie-o para `credentials.json` e mova-o para a pasta `config/` do projeto.**

## 🏃‍♀️ Como Executar o Projeto

1.  **Adicione suas Provas:** Coloque os arquivos PDF das provas que você deseja analisar dentro da pasta `input_proofs/`.
2.  **Execute o Script Principal:** No seu terminal (com o ambiente virtual ativado), na pasta raiz do projeto, execute:
    ```bash
    python3 main.py
    ```
3.  **Siga as Instruções:**
      * **Primeira Execução:** Uma aba do seu navegador será aberta para você autorizar o acesso à sua agenda. Faça login e conceda a permissão.
      * **Análise:** O agente começará a analisar e processar seus arquivos. Aguarde a conclusão.
      * **Chat:** O assistente de estudos iniciará a conversa. Interaja com ele em linguagem natural para definir seu plano.
      * **Agendamento e Verificação:** Ao final da conversa, o agente criará os eventos e verificará se tudo foi salvo corretamente.

## 🛠️ Utilitário: Limpeza de Eventos

Para facilitar testes, você pode apagar todos os eventos criados pelo agente.

1.  Execute o script de limpeza no terminal:
    ```bash
    python3 delete_events.py
    ```
2.  Informe o período (data de início e fim) em que os eventos foram criados.
3.  Confirme a exclusão digitando `s`.

## 📁 Estrutura do Projeto

```
/study_planner_agent/
|
|-- 📂 agent_core/
|   |-- classifier.py         # Agente que classifica o conteúdo
|   |-- conversational_planner.py # Agente que conversa com o usuário
|   |-- orchestrator.py       # Agente principal que gerencia o fluxo
|
|-- 📂 config/
|   |-- .env                    # Guarda a chave da API do Gemini
|   |-- credentials.json        # Suas credenciais do Google Calendar
|   |-- token.json              # Gerado após a autorização para salvar seu login
|
|-- 📂 input_proofs/
|   |-- (Coloque suas provas em PDF aqui)
|
|-- 📂 output_topics/
|   |-- (Os PDFs de estudo gerados aparecerão aqui)
|
|-- 📂 tools/
|   |-- google_calendar.py    # Ferramenta para interagir com o Google Calendar
|   |-- pdf_generator.py      # Ferramenta para criar os PDFs
|   |-- pdf_processor.py      # Ferramenta para ler os PDFs
|
|-- main.py                     # Script principal para executar o sistema
|-- delete_events.py            # Utilitário para limpar a agenda
|-- requirements.txt            # Lista de dependências do projeto
|-- README.md                   # Este arquivo
```# trabalho-agentes
# agentes_nlp
