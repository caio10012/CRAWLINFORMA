from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT  # Adicionei TA_RIGHT aqui
from reportlab.lib import colors
import sqlite3
from datetime import datetime, timedelta

def gerar_jornal():
    # Conecta ao banco
    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()
    
    # Busca notícias dos últimos 7 dias
    uma_semana_atras = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    cursor.execute("""
        SELECT titulo, texto, data_coleta 
        FROM noticias 
        WHERE data_coleta >= ?
        ORDER BY data_coleta DESC
    """, (uma_semana_atras,))
    
    noticias = cursor.fetchall()
    conn.close()

    if not noticias:
        print("Nenhuma notícia recente encontrada!")
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
        alignment=TA_RIGHT,  # Corrigido com TA_RIGHT importado
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
        # Corrige o formato da data
        try:
            # Tenta converter de string para datetime
            if isinstance(data, str):
                try:
                    data_obj = datetime.strptime(data, '%Y-%m-%d %H:%M:%S.%f')
                except ValueError:
                    data_obj = datetime.strptime(data, '%Y-%m-%d %H:%M:%S')
                data_formatada = data_obj.strftime('%d/%m %H:%M')
            else:
                data_formatada = data.strftime('%d/%m %H:%M')
        except Exception:
            data_formatada = "Data desconhecida"
        
        if "politica" in titulo.lower():
            secoes["Política"].append((titulo, texto, data_formatada))
        elif "economia" in titulo.lower():
            secoes["Economia"].append((titulo, texto, data_formatada))
        elif "mundo" in titulo.lower():
            secoes["Mundo"].append((titulo, texto, data_formatada))
        elif "tecnologia" in titulo.lower():
            secoes["Tecnologia"].append((titulo, texto, data_formatada))
        elif "ciência" in titulo.lower() or "saúde" in titulo.lower() or "saude" in titulo.lower():
            secoes["Ciência e Saúde"].append((titulo, texto, data_formatada))
        elif "educação" in titulo.lower() or "educacao" in titulo.lower():
            secoes["Educação"].append((titulo, texto, data_formatada))
        else:
            secoes["Outras"].append((titulo, texto, data_formatada))
    
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