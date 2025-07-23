import redis

r = redis.Redis(host='localhost', port=6379, db=0)

urls = [
    "https://g1.globo.com/",
    "https://www.bbc.com/portuguese",
    "https://www.cnnbrasil.com.br/"
]

for url in urls:
    r.lpush("fila_urls", url)
    print(f"URL enviada para a fila: {url}")
