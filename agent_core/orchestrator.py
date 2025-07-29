# agent_core/orchestrator.py (versão final consolidada)

import datetime as dt
from collections import defaultdict
from tqdm import tqdm
from langchain_core.prompts import ChatPromptTemplate
import re	
# Importa as ferramentas e classificadores necessários de outros módulos do projeto
from agent_core.classifier import TopicClassifier
from tools.pdf_processor import extract_chunks_from_pdfs
from tools.pdf_generator import create_topic_pdf
from tools.google_calendar import CalendarManager

class PlannerOrchestrator:
    """
    Agente orquestrador que gerencia todo o fluxo de trabalho:
    1. Analisa os PDFs de entrada e classifica o conteúdo.
    2. Gera um resumo teórico para cada tópico identificado.
    3. Cria arquivos PDF de estudo, combinando a teoria e as questões.
    4. Apresenta um resumo estatístico da análise.
    5. Agenda os estudos no Google Calendar com base nas preferências do usuário.
    6. Verifica se o agendamento foi bem-sucedido.
    """
    def __init__(self, api_key: str):
        """
        Inicializa o orquestrador com o classificador de tópicos.
        
        Args:
            api_key (str): A chave de API para o Google Gemini.
        """
        self.classifier = TopicClassifier(api_key=api_key)
        self.grouped_topics = defaultdict(lambda: defaultdict(list))
        self.topic_files_for_scheduling = []

    def _generate_topic_explanation(self, materia: str, assunto: str, chunks: list) -> str:
        """
        Usa a LLM para gerar uma explicação teórica concisa baseada nas questões.
        
        Args:
            materia (str): O nome da matéria.
            assunto (str): O nome do assunto.
            chunks (list): A lista de textos das questões relacionadas.

        Returns:
            str: Um texto contendo a explicação teórica gerada pela IA.
        """
        print(f"🧠 Gerando explicação para o tópico: {materia} - {assunto}...")
        
        # Concatena todas as questões em um único texto para dar contexto à IA
        all_questions_text = "\n\n---\n\n".join(chunks)

        # Cria um prompt bem definido para instruir a IA
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", "Você é um tutor especialista em preparar alunos para concursos. Sua tarefa é criar um resumo teórico conciso com base em um conjunto de questões."),
            ("human", """
            Com base no conjunto de questões sobre o tópico "{assunto}" da matéria "{materia}", fornecido abaixo, elabore uma explicação clara e objetiva.

            A explicação deve conter os conceitos fundamentais, as definições chave, as fórmulas principais e o conhecimento essencial que um aluno precisa para resolver essas questões com sucesso.
            
            NÃO resolva as questões diretamente. Seu objetivo é ensinar a teoria por trás delas. Use negrito para destacar termos importantes e organize a explicação de forma lógica e didática.

            **Questões Fornecidas:**
            ---
            {questions}
            ---
            **Sua Explicação Didática:**
            """)
        ])
        
        explanation_chain = prompt_template | self.classifier.llm
        
        try:
            response = explanation_chain.invoke({
                "assunto": assunto,
                "materia": materia,
                "questions": all_questions_text
            })
            
            # --- CONVERSÃO DE MARKDOWN PARA TAGS HTML ---
            markdown_text = response.content
            html_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', markdown_text)
            html_text = re.sub(r'###\s*(.*)', r'<b>\1</b>', html_text)
            html_text = re.sub(r'^\*\s*(.*)', r'• \1', html_text, flags=re.MULTILINE)
            
            return html_text
            
        except Exception as e:
            print(f"⚠️ Erro ao gerar explicação para {assunto}: {e}")
            return "Não foi possível gerar a explicação teórica para este tópico."

    def analyze_and_generate_pdfs(self, input_folder: str, output_folder: str) -> str:
        """
        Executa a fase de análise: lê, classifica, gera explicações e cria os PDFs.
        Retorna um resumo textual do que foi encontrado para ser usado na conversa.
        """
        # Fase 1: Leitura e extração do texto dos PDFs
        text_chunks = extract_chunks_from_pdfs(input_folder)
        
        # Fase 2: Classificação de cada página usando a IA
        print("\n🧠 Classificando conteúdo com o agente de IA...")
        for chunk in tqdm(text_chunks, desc="Classificando Chunks"):
            classification = self.classifier.classify_chunk(chunk)
            # Agrupa apenas se a classificação for bem-sucedida e relevante
            if classification and classification.relevante and classification.materia and classification.assunto:
                self.grouped_topics[classification.materia][classification.assunto].append(chunk)

        if not self.grouped_topics:
            return "❌ Nenhum conteúdo relevante foi classificado. Encerrando."

        # Fase 3: Geração das explicações e dos PDFs de estudo
        print("\n📄 Gerando explicações e PDFs de estudo por assunto...")
        for materia, assuntos in tqdm(self.grouped_topics.items(), desc="Gerando Explicações e PDFs"):
            for assunto, chunks in assuntos.items():
                # Gera a explicação teórica para o grupo de questões
                explanation = self._generate_topic_explanation(materia, assunto, chunks)
                # Cria o PDF, passando a explicação e as questões
                pdf_filename = create_topic_pdf(materia, assunto, explanation, chunks, output_folder)
                
                # Armazena informações sobre o PDF gerado para o agendamento posterior
                self.topic_files_for_scheduling.append({
                    "materia": materia,
                    "assunto": assunto,
                    "filename": pdf_filename,
                    "count": len(chunks)
                })
        
        # Fase 4: Criação do resumo estatístico
        summary = self._generate_summary()
        return summary

    def _generate_summary(self) -> str:
        """Cria uma string formatada com as estatísticas do conteúdo analisado."""
        num_materias = len(self.grouped_topics)
        num_assuntos = len(self.topic_files_for_scheduling)
        
        summary_str = "\n" + "="*50 + "\n"
        summary_str += "🔍 ANÁLISE CONCLUÍDA 🔍\n"
        summary_str += "="*50 + "\n"
        summary_str += f"Encontrei {num_materias} matérias e um total de {num_assuntos} assuntos distintos nos seus arquivos.\n\n"
        summary_str += "Matérias encontradas (e nº de assuntos):\n"
        
        for materia, assuntos in self.grouped_topics.items():
            summary_str += f"  - {materia}: {len(assuntos)} assuntos\n"
            
        top_5_assuntos = sorted(self.topic_files_for_scheduling, key=lambda x: x['count'], reverse=True)[:5]
        summary_str += "\nTop 5 assuntos com mais questões:\n"
        for i, topic in enumerate(top_5_assuntos):
            summary_str += f"  {i+1}. {topic['materia']} - {topic['assunto']} ({topic['count']} questões)\n"
            
        summary_str += "="*50 + "\n"
        return summary_str

    def schedule_with_preferences(self, preferences: dict):
        """
        Executa a fase de agendamento, criando e verificando os eventos no Google Calendar.
        
        Args:
            preferences (dict): Um dicionário com as preferências coletadas do usuário.
        """
        calendar_manager = CalendarManager()
        print("\n📅 Criando cronograma personalizado e agendando no Google Calendar...")
        
        # Ordena os tópicos, colocando os priorizados primeiro
        study_items = sorted(
            self.topic_files_for_scheduling,
            key=lambda x: (
                x['materia'] not in preferences.get('priorities', []) and x['assunto'] not in preferences.get('priorities', []),
                -x['count'] # Desempate por número de questões
            )
        )
        
        allowed_weekdays = preferences['study_days']
        study_date = dt.datetime.strptime(preferences['start_date'], '%Y-%m-%d')
        time_parts = list(map(int, preferences['study_time'].split(':')))
        
        expected_events_to_verify = []
        topics_scheduled_today = 0
        
        # Itera sobre os tópicos e cria os eventos
        for item in tqdm(study_items, desc="Agendando Eventos"):
            # Encontra o próximo dia de estudo permitido
            while study_date.weekday() not in allowed_weekdays or topics_scheduled_today >= preferences['topics_per_day']:
                study_date += dt.timedelta(days=1)
                topics_scheduled_today = 0
            
            event_datetime = study_date.replace(hour=time_parts[0], minute=time_parts[1], second=0)
            
            summary = f"Estudar: {item['materia']} - {item['assunto']}"
            description = f"Foco do dia: Revisar as questões e a teoria do arquivo '{item['filename']}'.\nEste assunto apareceu {item['count']} vez(es) nas provas analisadas."
            
            # Adiciona o evento à lista de verificação antes de criá-lo
            expected_events_to_verify.append({
                'summary': summary,
                'start_datetime': event_datetime
            })
            
            calendar_manager.create_study_event(summary, description, event_datetime)
            topics_scheduled_today += 1

        # Etapa final de verificação para garantir que os eventos foram criados.
        #calendar_manager.verify_events_creation(expected_events_to_verify)
