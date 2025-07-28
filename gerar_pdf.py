from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
import sqlite3
from datetime import datetime

def formatar_data(data_str):
    """Tenta converter vários formatos de data para objeto datetime"""
    if not data_str:
        return None
        
    formatos = [
        '%Y-%m-%dT%H:%M:%S',       # Formato ISO sem milissegundos
        '%Y-%m-%dT%H:%M:%S.%f',    # Formato ISO com milissegundos
        '%Y-%m-%d %H:%M:%S',        # Formato SQL
        '%Y-%m-%d',                 # Apenas data
        '%d/%m/%Y %Hh%M'            # Formato brasileiro
    ]
    
    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue
    
    return None

def gerar_jornal():
    # Conecta ao banco
    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()
    
    # Busca todas as notícias
    cursor.execute("""
        SELECT titulo, texto, data_publicacao 
        FROM noticias 
        ORDER BY data_publicacao DESC
    """)
    
    noticias = []
    for titulo, texto, data_publicacao in cursor.fetchall():
        # Formata a data
        data_obj = None
        
        if data_publicacao:
            if isinstance(data_publicacao, str):
                data_obj = formatar_data(data_publicacao)
            elif isinstance(data_publicacao, datetime):
                data_obj = data_publicacao
        
        # Formata para exibição
        if data_obj:
            data_formatada = data_obj.strftime('%d/%m/%Y')
        else:
            data_formatada = "Data desconhecida"
        
        # Filtra notícias com conteúdo suficiente
        if len(texto.split()) >= 100:
            noticias.append((titulo, texto, data_formatada))
    
    conn.close()

    if not noticias:
        print("Nenhuma notícia encontrada no banco de dados!")
        return

    # Configura PDF
    doc = SimpleDocTemplate("jornal_semanal.pdf", pagesize=A4)
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    styles.add(ParagraphStyle(
        name='Cabecalho',
        fontSize=24,
        alignment=TA_CENTER,
        textColor=colors.darkred,
        spaceAfter=20,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='Secao',
        fontSize=16,
        textColor=colors.darkblue,
        spaceAfter=10,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='TituloNoticia',
        fontSize=14,
        textColor=colors.black,
        spaceAfter=6,
        fontName='Helvetica-Bold'
    ))
    
    styles.add(ParagraphStyle(
        name='CorpoNoticia',
        fontSize=11,
        leading=14,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName='Helvetica'
    ))
    
    styles.add(ParagraphStyle(
        name='Data',
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_RIGHT,
        spaceAfter=5
    ))

    # Cabeçalho do jornal
    data_edicao = datetime.now().strftime("%d/%m/%Y")
    story.append(Paragraph("JORNAL SEMANAL G1", styles['Cabecalho']))
    story.append(Paragraph(f"Edição de {data_edicao}", styles['Data']))
    story.append(Spacer(1, 30))
    
    # Organiza por seções
    secoes = {
        "Política": [],
        "Economia": [],
        "Mundo": [],
        "Tecnologia": [],
        "Ciência e Saúde": [],
        "Educação": [],
        "Outras": []
    }
    
    # Classifica as notícias
    for titulo, texto, data in noticias:
        titulo_lower = titulo.lower()
        
        if "politica" in titulo_lower or "governo" in titulo_lower or "presidente" in titulo_lower:
            secoes["Política"].append((titulo, texto, data))
        elif "economia" in titulo_lower or "financeiro" in titulo_lower or "mercado" in titulo_lower or "dólar" in titulo_lower:
            secoes["Economia"].append((titulo, texto, data))
        elif "mundo" in titulo_lower or "internacional" in titulo_lower or "país" in titulo_lower or "guerra" in titulo_lower:
            secoes["Mundo"].append((titulo, texto, data))
        elif "tecnologia" in titulo_lower or "digital" in titulo_lower or "app" in titulo_lower or "celular" in titulo_lower:
            secoes["Tecnologia"].append((titulo, texto, data))
        elif "ciência" in titulo_lower or "saúde" in titulo_lower or "medic" in titulo_lower or "hospital" in titulo_lower:
            secoes["Ciência e Saúde"].append((titulo, texto, data))
        elif "educação" in titulo_lower or "educacao" in titulo_lower or "escola" in titulo_lower or "universidade" in titulo_lower:
            secoes["Educação"].append((titulo, texto, data))
        else:
            secoes["Outras"].append((titulo, texto, data))
    
    # Adiciona conteúdo ao PDF
    for secao, conteudo in secoes.items():
        if conteudo:
            story.append(Paragraph(secao.upper(), styles['Secao']))
            story.append(Spacer(1, 10))
            
            for titulo, texto, data in conteudo:
                story.append(Paragraph(titulo, styles['TituloNoticia']))
                story.append(Paragraph(f"<font size=9 color=grey>{data}</font>", styles['Normal']))
                story.append(Spacer(1, 5))
                
                texto_resumido = texto[:500] + ("..." if len(texto) > 500 else "")
                story.append(Paragraph(texto_resumido, styles['CorpoNoticia']))
                story.append(Spacer(1, 15))
            
            story.append(PageBreak())
    
    doc.build(story)
    print(f"Jornal gerado com {len(noticias)} notícias!")

if __name__ == "__main__":
    gerar_jornal()