#!/usr/bin/env python3
import os
import time
import re
import redis
import requests
from bs4 import BeautifulSoup
import database

# Configuração de limite
MAX_NOTICIAS = 20  # Limite máximo de notícias a serem coletadas

def is_noticia(url):
    """Verifica se a URL é de uma notícia real"""
    padrao_noticia = re.compile(r'\.globo\.com/[^/]+/noticia/')
    return bool(padrao_noticia.search(url))

def extrair_links_secao(soup, base_url="https://g1.globo.com"):
    """Extrai links de notícias de uma página de seção"""
    links = []
    for card in soup.select('a.feed-post-link'):
        href = card.get('href')
        if href and is_noticia(href):
            # Garante URL absoluta
            if not href.startswith('http'):
                href = base_url + href
            links.append(href)
    return links

def extrair_conteudo(soup):
    """Extrai título, resumo e texto da notícia"""
    # Título principal
    titulo_tag = soup.select_one('h1.content-head__title')
    titulo = titulo_tag.get_text().strip() if titulo_tag else ""
    
    # Resumo/Subtítulo
    resumo_tag = soup.select_one('h2.content-head__subtitle')
    resumo = resumo_tag.get_text().strip() if resumo_tag else ""
    
    # Corpo da notícia
    corpo = []
    for p in soup.select('article p.content-text__container'):
        texto = p.get_text().strip()
        if texto:
            corpo.append(texto)
    
    texto_completo = "\n\n".join(corpo)
    
    return titulo, resumo, texto_completo

def process_url(r, url, contador):
    # Verifica se atingiu o limite
    if contador["total"] >= MAX_NOTICIAS:
        print(f"Limite de {MAX_NOTICIAS} notícias atingido!")
        return False  # Indica que deve parar

    print(f"\nProcessando: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return True

    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Se for página de seção, extrai links de notícias
    if not is_noticia(url):
        print(f"Processando página de seção: {url}")
        links = extrair_links_secao(soup)
        for link in links:
            if not r.sismember("processed_urls", link) and contador["total"] < MAX_NOTICIAS:
                r.rpush("task_queue", link)
                print(f"  + Notícia encontrada: {link[:70]}...")
        
        # Marca seção como processada
        r.sadd("processed_urls", url)
        return True
    
    # Se for notícia real, processa conteúdo
    print(f"Processando notícia: {url}")
    
    # Verifica se é paywall
    if soup.select_one('.paywall'):
        print(f"Notícia com paywall: {url}")
        r.sadd("processed_urls", url)
        return True
    
    titulo, resumo, texto = extrair_conteudo(soup)
    
    if not texto:
        print(f"Conteúdo não encontrado em: {url}")
        r.sadd("processed_urls", url)
        return True
    
    # Combina título, resumo e texto
    conteudo_completo = f"{titulo}\n\n{resumo}\n\n{texto}"
    database.salvar_noticia(url, titulo, conteudo_completo)
    print(f"Notícia salva: {titulo[:60]}...")
    
    # Atualiza contador
    contador["total"] += 1
    print(f"Total de notícias coletadas: {contador['total']}/{MAX_NOTICIAS}")

    # Marca como processada
    r.sadd("processed_urls", url)

    # Enfileira novos links válidos (apenas de notícias) se ainda houver espaço
    if contador["total"] < MAX_NOTICIAS:
        for a in soup.select('a[href^="https://g1.globo.com/"]'):
            link = a.get('href').split('?')[0]  # Remove parâmetros
            if link and not r.sismember("processed_urls", link) and is_noticia(link):
                r.rpush("task_queue", link)
                print(f"  + Nova notícia relacionada: {link[:70]}...")

    return True

def main():
    database.criar_tabela()
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    
    # Contador de notícias
    contador = {"total": 0}
    
    print(f"Worker ativo. Aguardando tarefas (limite: {MAX_NOTICIAS} notícias)...")
    
    while True:
        try:
            # Verifica se atingiu o limite antes de buscar nova tarefa
            if contador["total"] >= MAX_NOTICIAS:
                print(f"Limite de {MAX_NOTICIAS} notícias atingido. Encerrando...")
                break
                
            item = r.brpop("task_queue", timeout=30)
            if not item:
                print("Timeout - Sem novas tarefas")
                # Se não há tarefas e já coletamos notícias, podemos parar
                if contador["total"] > 0:
                    print("Nenhuma tarefa nova. Encerrando...")
                    break
                time.sleep(10)
                continue
                
            _, url = item
            if not r.sismember("processed_urls", url):
                if not process_url(r, url, contador):  # Se retornar False, atingiu limite
                    break
            else:
                print(f"Pulando (processado): {url}")
        except KeyboardInterrupt:
            print("\nWorker interrompido")
            break
        except Exception as e:
            print(f"Erro geral: {e}")
            time.sleep(5)
    
    print(f"Worker finalizado. Total de notícias coletadas: {contador['total']}")

if __name__ == "__main__":
    main()