import csv
import statistics
import sys
from collections import defaultdict


def leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def resumen(prefijos):
    print("| Ejecución | Endpoint | Peticiones | Fallos | Fallos % | Mediana (ms) | P95 (ms) | Req/s | Tamaño medio (B) |")
    print("|---|---|---|---|---|---|---|---|---|")
    for p in prefijos:
        for r in leer(p + "_stats.csv"):
            n, fl = int(r["Request Count"]), int(r["Failure Count"])
            nombre = "Aggregated" if r["Name"] == "Aggregated" else r["Name"]
            pct = (100 * fl / n) if n else 0
            print(f"| {p.split(chr(92))[-1].split('/')[-1]} | {nombre} | {n} | {fl} | {pct:.2f} | "
                  f"{float(r['Median Response Time']):.0f} | {float(r['95%']):.0f} | "
                  f"{float(r['Requests/s']):.2f} | {float(r['Average Content Size']):.0f} |")


def rampa(prefijo):
    filas = [r for r in leer(prefijo + "_stats_history.csv") if r["Name"] == "Aggregated" and r["User Count"] not in ("", "0")]
    por_usuarios = defaultdict(list)
    for r in filas:
        por_usuarios[int(r["User Count"])].append(r)
    print("| Usuarios | Req/s (media) | P50 (ms, mediana) | P95 (ms, mediana) | Fallos/s (media) |")
    print("|---|---|---|---|---|")
    for u in sorted(por_usuarios):
        g = por_usuarios[u][len(por_usuarios[u]) // 3:]  # se descarta el tercio inicial (calentamiento del escalón)
        def num(k):
            return [float(x[k]) for x in g if x[k] not in ("", "N/A")]
        print(f"| {u} | {statistics.mean(num('Requests/s')):.2f} | {statistics.median(num('50%')):.0f} | "
              f"{statistics.median(num('95%')):.0f} | {statistics.mean(num('Failures/s')):.2f} |")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--rampa":
        rampa(args[1])
    elif args:
        resumen(args)
    else:
        print(__doc__)
