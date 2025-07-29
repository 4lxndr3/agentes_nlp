# agent_core/classifier.py (versão com método de saída estruturada moderno)

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from typing import Optional

# A definição da classe de saída permanece a mesma
class SubjectTopicOutput(BaseModel):
    materia: Optional[str] = Field(description="A matéria principal do texto, ex: 'Matemática', 'História do Brasil', 'Direito Constitucional'")
    assunto: Optional[str] = Field(description="O assunto específico dentro da matéria, ex: 'Juros Compostos', 'Primeira República', 'Artigo 5 da Constituição'")
    relevante: bool = Field(description="True se o texto contém uma questão ou conteúdo de estudo, False se for uma capa, índice ou página em branco.")

class TopicClassifier:
    """
    Um agente que usa um LLM para classificar um trecho de texto por matéria e assunto.
    """
    def __init__(self, api_key: str):

        prompt = ChatPromptTemplate.from_messages([
            ("system", "Você é um especialista em classificar conteúdo de provas de concurso. Sua tarefa é analisar o texto e identificar a matéria e o assunto específico. Se o texto não for relevante (capa, índice, etc.), retorne 'relevante: false'. Extraia as informações e formate a saída de acordo com o esquema solicitado."),
            ("human", "Analise o seguinte texto extraído de uma prova:\n\n---\n\n{text_chunk}\n\n---")
        ])
        
        self.llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key, temperature=0.0)

        structured_llm = self.llm.with_structured_output(SubjectTopicOutput)
        
        self.chain = prompt | structured_llm
        
    def classify_chunk(self, text_chunk: str) -> Optional[SubjectTopicOutput]:
        """
        Classifica um único chunk de texto.
        """
        try:
            # A chamada para a chain também fica mais limpa.
            return self.chain.invoke({"text_chunk": text_chunk})
        except Exception as e:
            print(f"⚠️ Erro de classificação: {e}")
            return None