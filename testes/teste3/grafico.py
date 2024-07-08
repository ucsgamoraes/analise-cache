import os
import json
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator, ScalarFormatter
import scienceplots

def ler_dados_json(json_file_path, chave_x, chave_y):
    with open(json_file_path, "r", encoding="utf-8") as f:
        dados = json.load(f)
        x = [i for i in dados[chave_x]]
        y = dados[chave_y]
    return x, y

min_power_x = 1
max_power_x = 7

file_path = os.path.dirname(__file__)
grafico1 = file_path + "/dados/grafico.json"
chave_y = "taxa_hit_global_values"
chave_x = "associatividade"

x, y = ler_dados_json(grafico1, chave_x, chave_y)
plt.style.context('science')
plt.style.use(['science', 'ieee'])
plt.rcParams.update({'font.size': 16})
plt.plot(x, y, linewidth=2)
plt.title("Impacto do Associatividade")
plt.xlabel("Associatividade")
plt.ylabel("Taxa de acerto (\%)")

ticks = [2**i for i in range(min_power_x, max_power_x)]
labels = [f'{2**i}' if 2**i < 1024 else f'{2**i // 1024}k' if 2**i < 1024**2 else '1M' for i in range(min_power_x, max_power_x)]
plt.xscale('log')
plt.xticks(ticks, labels)
y_major_locator = MultipleLocator(5)
ax = plt.gca()
ax.yaxis.set_major_locator(y_major_locator)
ax.yaxis.set_major_formatter(ScalarFormatter())

plt.grid(True)
figure = plt.gcf() # get current figure
figure.set_size_inches(8, 6)
plt.savefig(file_path + "/teste3.svg", format="svg", dpi=300)