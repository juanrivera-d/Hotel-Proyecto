import pandas as pd
import matplotlib.pyplot as plt

def cargar(archivo):
    df = pd.read_csv(archivo)
    df = df[df['Name'] == 'Aggregated'].copy()
    df['t'] = df['Timestamp'] - df['Timestamp'].iloc[0]
    df['p95'] = pd.to_numeric(df['95%'], errors='coerce')
    df['rps'] = pd.to_numeric(df['Requests/s'], errors='coerce')
    return df

h1 = cargar('E1b_3replicas_stats_history.csv')
h2 = cargar('E2_analitica_pesada_stats_history.csv')
h3 = cargar('E3_5escritores_stats_history.csv')

fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(12.5, 3.4), dpi=220)

# Panel 1: Latencia P95 en escala logarítmica
ax1.plot(h1['t'], h1['p95'], label='E1b: Ligera (20 u, 3 rép.)', color='#1f77b4', linewidth=1.6)
ax1.plot(h2['t'], h2['p95'], label='E2: Analítica (5 u, 7.78 MB)', color='#d62728', linewidth=1.6)
ax1.set_yscale('log')
ax1.set_title('Latencia P95 móvil: E1b vs E2 (ms, log)')
ax1.set_xlabel('Tiempo transcurrido (s)')
ax1.set_ylabel('ms (escala log)')
ax1.legend(fontsize=7.5, loc='center right')
ax1.grid(True, which='both', alpha=0.25)

# Panel 2: Throughput comparativo
ax2.plot(h1['t'], h1['rps'], label='E1b: Ligera (20 usuarios)', color='#1f77b4', linewidth=1.6)
ax2.plot(h2['t'], h2['rps'], label='E2: Analítica (5 usuarios)', color='#d62728', linewidth=1.6)
ax2.set_title('Throughput: E1b vs E2 (Req/s)')
ax2.set_xlabel('Tiempo transcurrido (s)')
ax2.set_ylabel('Req/s')
ax2.legend(fontsize=7.5, loc='center right')
ax2.grid(True, alpha=0.3)

# Panel 3: Evolución temporal P95 de escrituras E3
ax3.plot(h3['t'], h3['p95'], label='P95 móvil (P95 global: 180 ms)', color='#2ca02c', linewidth=1.6)
ax3.axhline(180, color='#555555', linestyle='--', linewidth=1, label='P95 agregado (180 ms)')
ax3.set_title('E3: Latencia P95 móvil Escrituras (ms)')
ax3.set_xlabel('Tiempo transcurrido (s)')
ax3.set_ylabel('ms')
ax3.legend(fontsize=7.5, loc='upper right')
ax3.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig('fig5_locust_final.png')
print('Listo: fig5_locust_final.png generado')
