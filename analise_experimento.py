import pandas as pd
import matplotlib.pyplot as plt

# 1. Carrega o log (já com cabeçalho)
df = pd.read_csv('worker_log.csv', header=0)

# 2. Contagem de tarefas por worker_id
contagem = df['worker_id'].value_counts().sort_index()

# 3. Calcula latência total (end_proc - dequeue_time)
df['latencia'] = df['end_proc'] - df['dequeue_time']

# 4. Estatísticas de latência por worker_id
lat_stats = df.groupby('worker_id')['latencia'].agg(['mean', 'median', 'max'])

# 5. Gráfico de tarefas processadas por worker
plt.figure(figsize=(8, 5))
bars = plt.bar(
    x   = contagem.index.astype(str),
    height = contagem.values,
    color   = 'teal',
    edgecolor = 'black'
)
plt.title('Tarefas Processadas por Worker (PID)', fontsize=14, fontweight='bold')
plt.xlabel('Worker PID', fontsize=12)
plt.ylabel('Número de Tarefas', fontsize=12)
plt.grid(axis='y', linestyle=':', alpha=0.7)

# Anota valores sobre as barras
for bar in bars:
    h = bar.get_height()
    plt.text(
        bar.get_x() + bar.get_width()/2,
        h + 1,
        str(int(h)),
        ha='center',
        va='bottom',
        fontsize=11
    )

plt.tight_layout()
plt.show()

# 6. Impressão das estatísticas de latência
print('\nEstatísticas de Latência por Worker (PID):')
print(lat_stats.to_string(float_format='%.3f'))
