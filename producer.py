#!/usr/bin/env python3
import os
import redis

# URLs de seções com listas de notícias
SEEDS = [
    "https://g1.globo.com/ultimas-noticias/",
    "https://g1.globo.com/politica/",
    "https://g1.globo.com/economia/",
    "https://g1.globo.com/mundo/",
    "https://g1.globo.com/tecnologia/",
    "https://g1.globo.com/ciencia-e-saude/",
    "https://g1.globo.com/educacao/"
]

def main():
    redis_host = os.getenv("REDIS_HOST", "localhost")
    r = redis.Redis(host=redis_host, port=6379, decode_responses=True)
    
    # Limpa filas anteriores
    r.delete("task_queue")
    r.delete("processed_urls")
    
    for url in SEEDS:
        r.rpush("task_queue", url)
        print(f"Seção adicionada: {url}")
    
    print(f"Producer finalizado. {len(SEEDS)} seções enfileiradas.")

if __name__ == "__main__":
    main()