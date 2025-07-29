# agent_core/conversational_planner.py (versão com correção do início da conversa)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import json

class ConversationalPlanner:
    def __init__(self, api_key: str):
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.7)
        self.history = []

    def start_conversation(self, topics_summary: str, schedule_summary: str):
        """ Inicia a conversa com uma saudação e um resumo inteligente. """
        

        # 1. Define o papel do agente 
        system_prompt = """
        Você é um assistente de estudos inteligente e amigável. Sua tarefa é conversar com o usuário para criar um cronograma de estudos personalizado. 
        Seja proativo, use os dados fornecidos para fazer sugestões inteligentes e guie o usuário até um plano final.
        """
        
        # 2. Cria a primeira "pergunta" do usuário, que contém os dados e a instrução para começar.
        initial_user_prompt = f"""
        Olá! Por favor, inicie a conversa. Aqui estão os dados que você precisa para começar:

        **Resumo dos Tópicos das Provas que analisei:**
        {topics_summary}

        **Análise da sua Agenda:**
        {schedule_summary}

        Com base nisso, inicie a conversa com uma saudação amigável, um resumo rápido do que você descobriu e uma pergunta aberta para começarmos a planejar.
        """
        
        # 3. O histórico agora começa com o papel do sistema E a primeira mensagem do "usuário".
        self.history = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=initial_user_prompt)
        ]
        
        # 4. A primeira invocação agora tem um conteúdo claro para a IA responder.
        initial_response = self.llm.invoke(self.history)
        self.history.append(initial_response)
        
        print("\n--- 🤖 Assistente de Estudos ---")
        print(initial_response.content)

    def chat(self, user_input: str):
        """ Continua a conversa com a entrada do usuário. """
        self.history.append(HumanMessage(content=user_input))
        
        response = self.llm.invoke(self.history)
        self.history.append(response)
        
        print(f"\n--- 🤖 Assistente de Estudos ---\n{response.content}")

    def is_plan_finalized(self) -> dict | None:
        """
        Verifica se a conversa chegou a um plano final. Se sim, extrai as preferências.
        """
        prompt = """
        Analise o histórico da conversa. O usuário concordou em finalizar e agendar o plano?
        Se sim, extraia as seguintes informações em um formato JSON:
        - topics_per_day (int)
        - study_time (string, formato "HH:MM")
        - study_days (lista de inteiros, segunda=0, domingo=6)
        - priorities (lista de strings com nomes de matérias/assuntos, pode ser vazia)
        - start_date (string, formato "YYYY-MM-DD")
        
        Se o plano ainda não estiver finalizado, retorne um JSON com a chave "finalized" como false.
        Responda APENAS com o JSON. Não adicione nenhum outro texto ou formatação.
        """
        
        finalization_check_history = self.history + [HumanMessage(content=prompt)]
        
        try:
            response = self.llm.invoke(finalization_check_history)
            cleaned_response = response.content.strip().replace('```json', '').replace('```', '')
            data = json.loads(cleaned_response)
            
            if data.get("finalized") is False:
                return None
            
            if all(k in data for k in ['topics_per_day', 'study_time', 'study_days', 'start_date']):
                # Garante que 'priorities' exista, mesmo que seja uma lista vazia
                data.setdefault('priorities', [])
                return data
            return None
        except (json.JSONDecodeError, TypeError, AttributeError):
            return None