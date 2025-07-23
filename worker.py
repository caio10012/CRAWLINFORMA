import redis
import requests
from bs4 import BeautifulSoup
import json
import os

r = redis.Redis(host='localhost', port=6379, db=0)

while True:
    _, url = r.brpop("fila_urls")
    url = url.decode("utf-8")
    print(f"[WORKER] Pegando URL: {url}")

    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        title = soup.title.string.strip() if soup.title else "Sem título"

        noticia = {"url": url, "titulo": title}

        # Salvar no JSON
        if not os.path.exists("storage/noticias.json"):
            with open("storage/noticias.json", "w") as f:
                json.dump([noticia], f, indent=4)
        else:
            with open("storage/noticias.json", "r") as f:
                data = json.load(f)
            data.append(noticia)
            with open("storage/noticias.json", "w") as f:
                json.dump(data, f, indent=4)

        print(f"[WORKER] Notícia salva: {title}")
    except Exception as e:
        print(f"[WORKER] Erro: {e}")
