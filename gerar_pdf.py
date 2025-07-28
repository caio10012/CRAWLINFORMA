from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
import sqlite3
from datetime import datetime, timedelta

def formatar_data(data_str):
    """Tenta converter várias formatos de data para objeto datetime"""
    formatos = [
        '%Y-%m-%dT%H:%M:%S.%fZ',  # Formato ISO
        '%Y-%m-%dT%H:%M:%SZ',      # Formato ISO sem milissegundos
        '%d/%m/%Y %Hh%M',           # Formato brasileiro
        '%Y-%m-%d %H:%M:%S',        # Formato SQL
        '%d/%m/%Y'                  # Apenas data
    ]
    
    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt)
        except ValueError:
            continue
    
    # Se nenhum formato funcionar, retorna data atual como fallback
    return datetime.now()

def gerar_jornal():
    # Conecta ao banco
    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()
    
    # Busca notícias dos últimos 3 dias (em relação à data de publicação)
    tres_dias_atras = (datetime.now() - timedelta(days=3))
    
    # Seleciona as notícias com data_publicacao nos últimos 3 dias
    cursor.execute("""
        SELECT titulo, texto, data_publicacao 
        FROM noticias 
        ORDER BY data_publicacao DESC
    """)
    
    noticias = []
    for titulo, texto, data_publicacao in cursor.fetchall():
        # Filtra notícias com menos de 100 palavras
        if len(texto.split()) < 100:
            continue
            
        # Tenta converter a data para objeto datetime
        try:
            data_obj = formatar_data(data_publicacao)
            
            # Filtra notícias muito antigas
            if data_obj < tres_dias_atras:
                continue
                
            data_formatada = data_obj.strftime('%d/%m %H:%M')
        except Exception as e:
            print(f"Erro ao formatar data '{data_publicacao}': {e}")
            data_formatada = data_publicacao
        
        noticias.append((titulo, texto, data_formatada))
    
    conn.close()

    if not noticias:
        print("Nenhuma notícia recente encontrada!")
        return

    # Ordena notícias pela data mais recente
    noticias.sort(key=lambda x: x[2], reverse=True)

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
        
        if "politica" in titulo_lower or "governo" in titulo_lower:
            secoes["Política"].append((titulo, texto, data))
        elif "economia" in titulo_lower or "econômica" in titulo_lower or "financeiro" in titulo_lower:
            secoes["Economia"].append((titulo, texto, data))
        elif "mundo" in titulo_lower or "internacional" in titulo_lower:
            secoes["Mundo"].append((titulo, texto, data))
        elif "tecnologia" in titulo_lower or "digital" in titulo_lower:
            secoes["Tecnologia"].append((titulo, texto, data))
        elif "ciência" in titulo_lower or "saúde" in titulo_lower or "saude" in titulo_lower or "médic" in titulo_lower:
            secoes["Ciência e Saúde"].append((titulo, texto, data))
        elif "educação" in titulo_lower or "educacao" in titulo_lower or "escola" in titulo_lower:
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
                
                # Limita o texto para 500 caracteres + leia mais
                texto_resumido = texto[:500] + ("..." if len(texto) > 500 else "")
                story.append(Paragraph(texto_resumido, styles['CorpoNoticia']))
                story.append(Spacer(1, 15))
            
            story.append(PageBreak())
    
    # Gera o PDF
    doc.build(story)
    print(f"Jornal semanal gerado com {len(noticias)} notícias!")

if __name__ == "__main__":
    gerar_jornal()