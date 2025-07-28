#!/usr/bin/env python3
import os
import time
import re
import redis
import requests
from bs4 import BeautifulSoup
import database
from datetime import datetime
import dateparser
import json

# Configuração de limite
MAX_NOTICIAS = 10

def is_noticia(url):
    """Verifica se a URL é de uma notícia real com padrão rigoroso"""
    padrao_noticia = re.compile(
        r'https?://[^/]+\.globo\.com/[^/]+/noticia/\d{4}/\d{2}/\d{2}/'
    )
    
    # Lista negra de seções não-noticiosas
    secoes_proibidas = [
        'sobre', 'equipe', 'redacao', 'institucional', 'contato',
        'termos-de-uso', 'vc-no-g1', 'redacao-globoreporter',
        'equipe-bom-dia-brasil', 'conheca-a-historia',
        'nossa-equipe', 'siga-a-globonews'
    ]
    
    if not padrao_noticia.search(url):
        return False
        
    if any(sec in url.lower() for sec in secoes_proibidas):
        return False
        
    return True

def extrair_links_secao(soup, base_url="https://g1.globo.com"):
    """Extrai links de notícias de uma página de seção"""
    links = []
    for card in soup.select('a.feed-post-link'):
        href = card.get('href')
        if href:
            if not href.startswith('http'):
                href = base_url + href
            if is_noticia(href):
                links.append(href)
    return links

def extrair_data_publicacao(soup, url):
    """Extrai e converte a data de publicação com múltiplas estratégias"""
    # Estratégia 1: Tag time com itemprop
    data_tag = soup.select_one('time[itemprop="datePublished"]')
    if data_tag and data_tag.get('datetime'):
        try:
            return datetime.strptime(data_tag['datetime'], '%Y-%m-%dT%H:%M:%S.%fZ')
        except:
            pass
    
    # Estratégia 2: Conteúdo de publicação
    pub_tag = soup.select_one('.content-publication-data__updated')
    if pub_tag:
        data_text = pub_tag.get_text().strip()
        parsed_date = dateparser.parse(data_text, languages=['pt'])
        if parsed_date:
            return parsed_date
    
    # Estratégia 3: JSON-LD no cabeçalho
    script = soup.select_one('script[type="application/ld+json"]')
    if script:
        try:
            data = json.loads(script.string)
            date_str = data.get('datePublished', '')
            if date_str:
                # Tenta remover informações de fuso horário
                date_str = date_str.split('+')[0]
                return datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')
        except:
            pass
    
    # Estratégia 4: Extrair do URL (último recurso)
    padrao_data = re.search(r'/(\d{4})/(\d{2})/(\d{2})/', url)
    if padrao_data:
        try:
            ano, mes, dia = padrao_data.groups()
            return datetime(int(ano), int(mes), int(dia))
        except:
            pass
    
    return None

def extrair_conteudo(soup, url):
    """Extrai título, resumo, texto e data de publicação da notícia"""
    # Título principal
    titulo_tag = soup.select_one('h1.content-head__title')
    titulo = titulo_tag.get_text().strip() if titulo_tag else ""
    
    # Resumo/Subtítulo
    resumo_tag = soup.select_one('h2.content-head__subtitle')
    resumo = resumo_tag.get_text().strip() if resumo_tag else ""
    
    # Data de publicação
    data_publicacao = extrair_data_publicacao(soup, url)
    
    # Corpo da notícia
    corpo = []
    for p in soup.select('article p.content-text__container'):
        texto = p.get_text().strip()
        if texto:
            corpo.append(texto)
    
    texto_completo = "\n\n".join(corpo)
    
    # Verifica se o conteúdo tem pelo menos 100 palavras
    if len(texto_completo.split()) < 100:
        return "", "", "", None
    
    return titulo, resumo, texto_completo, data_publicacao

def process_url(r, url, contador):
    if contador["total"] >= MAX_NOTICIAS:
        print(f"Limite de {MAX_NOTICIAS} notícias atingido!")
        return False

    print(f"\nProcessando: {url}")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9'
        }
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except Exception as e:
        print(f"Erro ao baixar {url}: {e}")
        return True

    soup = BeautifulSoup(resp.text, "html.parser")
    
    if not is_noticia(url):
        print(f"Processando página de seção: {url}")
        links = extrair_links_secao(soup)
        for link in links:
            if not r.sismember("processed_urls", link) and contador["total"] < MAX_NOTICIAS:
                r.rpush("task_queue", link)
                print(f"  + Notícia encontrada: {link[:70]}...")
        
        r.sadd("processed_urls", url)
        return True
    
    print(f"Processando notícia: {url}")
    
    if soup.select_one('.paywall'):
        print(f"Notícia com paywall: {url}")
        r.sadd("processed_urls", url)
        return True
    
    titulo, resumo, texto, data_publicacao = extrair_conteudo(soup, url)
    
    if not texto:
        print(f"Conteúdo não encontrado ou insuficiente em: {url}")
        r.sadd("processed_urls", url)
        return True
    
    conteudo_completo = f"{titulo}\n\n{resumo}\n\n{texto}"
    
    # Converter data para string ISO se existir
    data_str = data_publicacao.isoformat() if data_publicacao else None
    
    database.salvar_noticia(url, titulo, conteudo_completo, data_str)
    
    contador["total"] += 1
    print(f"Notícia salva: {titulo[:60]}... ({contador['total']}/{MAX_NOTICIAS})")

    r.sadd("processed_urls", url)

    if contador["total"] < MAX_NOTICIAS:
        for a in soup.select('a[href^="https://g1.globo.com/"]'):
            link = a.get('href').split('?')[0]
            if link and not r.sismember("processed_urls", link) and is_noticia(link):
                r.rpush("task_queue", link)
                print(f"  + Nova notícia relacionada: {link[:70]}...")

    return True

def main():
    database.criar_tabela()
    
    redis_host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    
    contador = {"total": 0}
    
    print(f"Worker ativo. Aguardando tarefas (limite: {MAX_NOTICIAS} notícias)...")
    
    while True:
        try:
            if contador["total"] >= MAX_NOTICIAS:
                print(f"Limite de {MAX_NOTICIAS} notícias atingido. Encerrando...")
                break
                
            item = r.brpop("task_queue", timeout=30)
            if not item:
                print("Timeout - Sem novas tarefas")
                if contador["total"] > 0:
                    print("Nenhuma tarefa nova. Encerrando...")
                    break
                time.sleep(10)
                continue
                
            _, url = item
            if not r.sismember("processed_urls", url):
                if not process_url(r, url, contador):
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