import sqlite3
from datetime import datetime

def criar_tabela():
    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS noticias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            titulo TEXT,
            texto TEXT,
            data_publicacao TEXT,  -- Nova coluna para a data de publicação original
            data_coleta DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

def salvar_noticia(url, titulo, texto, data_publicacao):
    # Verifica se o texto tem pelo menos 100 palavras
    palavras = texto.split()
    if len(palavras) < 100:
        print(f"[DB] Ignorando notícia com conteúdo insuficiente: {titulo[:50]}...")
        return

    conn = sqlite3.connect('noticias.db')
    cursor = conn.cursor()
    try:
        cursor.execute(
            """INSERT OR IGNORE INTO noticias 
            (url, titulo, texto, data_publicacao, data_coleta) 
            VALUES (?, ?, ?, ?, ?)""",
            (url, titulo, texto, data_publicacao, datetime.now())
        )
        conn.commit()
        print(f"[DB] Notícia salva: {titulo[:50]}...")
    except sqlite3.Error as e:
        print(f"[DB] Erro ao salvar: {e}")
    finally:
        conn.close()