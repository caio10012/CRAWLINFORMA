import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# Importar a função que vamos criar para gerar o PDF
from gerar_pdf import gerar_pdf_mini_jornal

def carregar_dados(db_path='noticias.db'):
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT url, titulo, texto FROM noticias", conn)
    conn.close()
    return df

def extrair_dominio(url):
    try:
        return url.split('/')[2]
    except:
        return 'desconhecido'

def preparar_dados(df):
    df['dominio'] = df['url'].apply(extrair_dominio)
    contagem = df['dominio'].value_counts()
    comprimento_medio = df.groupby('dominio')['texto'].apply(lambda x: x.str.len().mean())
    return contagem, comprimento_medio

def filtrar_top_dominios(df, top_n=5):
    contagem = df['dominio'].value_counts()
    top_dominios = contagem.head(top_n).index.tolist()
    return df[df['dominio'].isin(top_dominios)]

def plotar_contagem(contagem):
    fig, ax = plt.subplots(figsize=(10, 6))
    contagem.sort_values().plot.barh(ax=ax)
    ax.set_title('Quantidade de Notícias por Domínio', fontsize=16, fontweight='bold')
    ax.set_xlabel('Número de Notícias', fontsize=14)
    ax.set_ylabel('Domínio', fontsize=14)
    ax.grid(axis='x', linestyle=':', alpha=0.7)
    for p in ax.patches:
        ax.annotate(f'{int(p.get_width())}', 
                    (p.get_width() + 0.5, p.get_y() + p.get_height()/2),
                    va='center', fontsize=12)
    plt.tight_layout()
    plt.show()

def imprimir_resumo(contagem, comprimento_medio):
    total = contagem.sum()
    print(f'\n{"DOMÍNIO":30} {"QTDE":>6} {"%":>8} {"TAM. MÉDIO":>12}')
    print('-'*60)
    for dom, qtd in contagem.items():
        perc = qtd/total*100
        tam = comprimento_medio[dom]
        print(f'{dom:30} {qtd:>6} {perc:8.2f}% {tam:12.0f}')

def main():
    df = carregar_dados()
    df['dominio'] = df['url'].apply(extrair_dominio)
    contagem, comprimento_medio = preparar_dados(df)
    plotar_contagem(contagem)
    imprimir_resumo(contagem, comprimento_medio)

    df_filtrado = filtrar_top_dominios(df, top_n=5)
    print(f"\nGerando PDF do mini jornal com notícias dos domínios: {df_filtrado['dominio'].unique()}")
    gerar_pdf_mini_jornal(df_filtrado)

if __name__ == '__main__':
    main()
