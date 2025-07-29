import os
from typing import List
from pypdf import PdfReader
from tqdm import tqdm

def extract_chunks_from_pdfs(folder_path: str) -> List[str]:
    """
    Lê todos os arquivos PDF de uma pasta, extrai o texto e o divide em chunks.

    Args:
        folder_path: O caminho para a pasta contendo os arquivos PDF.

    Returns:
        Uma lista de strings, onde cada string é um chunk de texto (página).
    """
    print(f"🔎 Lendo e processando PDFs da pasta: {folder_path}...")
    text_chunks = []
    pdf_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.pdf')]

    for filename in tqdm(pdf_files, desc="Processando PDFs"):
        file_path = os.path.join(folder_path, filename)
        try:
            reader = PdfReader(file_path)
            for page_num, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    # Adiciona contexto de origem a cada chunk
                    source_context = f"Fonte: {filename}, Página: {page_num + 1}\n\n---\n\n{text}"
                    text_chunks.append(source_context)
        except Exception as e:
            print(f"⚠️ Erro ao ler o arquivo {filename}: {e}")
            
    print(f"✅ Extração concluída. Total de {len(text_chunks)} páginas (chunks) processadas.")
    return text_chunks