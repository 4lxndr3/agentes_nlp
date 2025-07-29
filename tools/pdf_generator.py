import os
import html
import re
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

def _add_page_numbers(canvas, doc):
    canvas.saveState()
    canvas.setFont('Times-Roman', 9)
    page_number_text = f"Página {doc.page}"
    canvas.drawCentredString(4.25 * inch, 0.75 * inch, page_number_text)
    canvas.restoreState()

def create_topic_pdf(materia: str, assunto: str, explanation_text: str, content_chunks: list, output_folder: str):
    sanitized_materia = "".join(c for c in materia if c.isalnum() or c in (' ', '-')).rstrip()
    sanitized_assunto = "".join(c for c in assunto if c.isalnum() or c in (' ', '-')).rstrip()
    filename = f"{sanitized_materia}_{sanitized_assunto}.pdf".replace(" ", "_")
    filepath = os.path.join(output_folder, filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter, rightMargin=inch, leftMargin=inch, topMargin=inch, bottomMargin=inch)
    story = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Justify', alignment=TA_JUSTIFY, fontSize=11, leading=14))
    styles.add(ParagraphStyle(name='SourceHeader', fontName='Helvetica-Bold', fontSize=10, leading=12, spaceAfter=6))
    styles.add(ParagraphStyle(name='MainTitle', fontSize=18, leading=22, alignment=TA_CENTER, spaceAfter=10))
    styles.add(ParagraphStyle(name='SubTitle', fontSize=14, leading=18, alignment=TA_CENTER, spaceAfter=20))
    styles.add(ParagraphStyle(name='SectionHeader', fontName='Helvetica-Bold', fontSize=12, spaceBefore=12, spaceAfter=6))


    story.append(Paragraph(f"Matéria: {materia}", styles['MainTitle']))
    story.append(Paragraph(f"Assunto: {assunto}", styles['SubTitle']))
    
    story.append(HRFlowable(width="100%", thickness=1, color='black'))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Resumo Teórico do Assunto", styles['SectionHeader']))
    explanation_paragraph = Paragraph(explanation_text.replace('\n', '<br/>'), styles['Justify'])
    story.append(explanation_paragraph)
    story.append(Spacer(1, 0.3 * inch))


    story.append(HRFlowable(width="100%", thickness=2, color='black'))
    story.append(Spacer(1, 0.2 * inch))
    story.append(Paragraph("Questões de Provas Anteriores", styles['SectionHeader']))
    story.append(Spacer(1, 0.1 * inch))


    for i, chunk in enumerate(content_chunks):
        try:
            parts = chunk.split('\n\n---\n\n', 1)
            source_info = parts[0].replace("\n", " | ")
            content_text = parts[1]
            escaped_text = html.escape(content_text)
            
            split_pattern = r'\(\s*[A-Z]\s*\)'
            text_parts = re.split(split_pattern, escaped_text, 1)
            
            if len(text_parts) > 1:
                enunciado = text_parts[0]
                match = re.search(split_pattern, escaped_text)
                alternativas = match.group(0) + text_parts[1]
                formatted_text = f"<b>{enunciado}</b><br/><br/>{alternativas}".replace('\n', '<br/>')
            else:
                formatted_text = escaped_text.replace('\n', '<br/>')

            story.append(Paragraph(source_info, styles['SourceHeader']))
            story.append(Paragraph(formatted_text, styles['Justify']))
            
            if i < len(content_chunks) - 1:
                story.append(Spacer(1, 0.3 * inch))
                story.append(HRFlowable(width="90%", thickness=0.5, color='grey', spaceAfter=20, hAlign='CENTER'))
                story.append(Spacer(1, 0.2 * inch))
        except IndexError:
            escaped_chunk = html.escape(chunk)
            formatted_chunk = escaped_chunk.replace('\n', '<br/>')
            story.append(Paragraph(formatted_chunk, styles['Justify']))

    doc.build(story, onFirstPage=_add_page_numbers, onLaterPages=_add_page_numbers)
    return filename