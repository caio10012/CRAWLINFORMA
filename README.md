# 🗞️ Resumo Semanal de Notícias - Gerador de PDF Automatizado

Este projeto tem como objetivo coletar, resumir e gerar automaticamente um documento em PDF com as principais manchetes da semana. Utilizando técnicas de web scraping, limpeza de dados e manipulação de arquivos, o sistema cria um jornal simplificado e visualmente organizado com notícias reais.

## 📌 Funcionalidades

- 🔍 **Coleta automatizada** de manchetes de sites de notícias confiáveis.
- 🧠 **Resumidor automático** para simplificar as manchetes.
- 🗂️ Organização das notícias por categorias como Política, Economia, Esportes, etc.
- 🧾 **Geração de PDF** com layout de jornal semanal.
- ⏱️ Execução rápida com **paralelismo de tarefas** usando múltiplos workers.

## 📸 Exemplo de Saída

> **POLÍTICA**  
> *Governo Milei negocia acordo para que argentinos entrem nos EUA sem visto*  
> *28/07/2025*  
> Argentina iniciou processo para integrar o programa Visa Waiver dos EUA. Aproximação com o governo Trump pode beneficiar o país, enquanto Brasil sofre ameaça de taxação.

## 🛠️ Tecnologias Utilizadas

- **Python 3.11+**
- `requests`, `BeautifulSoup` – Scraping de sites de notícias
- `reportlab` ou `FPDF` – Geração do PDF
- `concurrent.futures` – Execução paralela de tarefas
- `datetime`, `os`, `re` – Utilitários para manipulação de arquivos e datas