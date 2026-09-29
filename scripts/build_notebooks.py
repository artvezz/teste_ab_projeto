"""Reconstroi os notebooks do teste A/B corrigidos.

Corrige:
- caminhos absolutos /home/art/... -> caminhos relativos ao repo
- leitura do CSV sem sep=';' (o arquivo usa ';'), eliminando o fix_dataframe()
- df['ROI'] e df['CPA'] -> KeyError: as colunas nao existem no dataset
- percentuais digitados a mao na conclusao -> agora calculados
- kernelspec 'venv' (especifico da maquina de origem) -> 'python3'
"""

import json
from pathlib import Path

import nbformat as nbf

NB_DIR = Path("notebooks")


def code(src: str):
    return nbf.v4.new_code_cell(src.strip("\n"))


def md(src: str):
    return nbf.v4.new_markdown_cell(src.strip("\n"))


METADATA = {
    "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
    "language_info": {
        "name": "python",
        "version": "3.12.0",
        "file_extension": ".py",
        "mimetype": "text/x-python",
        "codemirror_mode": {"name": "ipython", "version": 3},
        "pygments_lexer": "ipython3",
        "nbconvert_exporter": "python",
    },
}

LOADERS = {
    "eda_CG": ("control_group.csv", "df_CG", "Control Campaign", "GRUPO DE CONTROLE"),
    "eda_TG": ("test_group.csv", "df_TG", "Test Campaign", "GRUPO DE TESTE"),
}

EDA_CELLS = """
import pandas as pd

pd.set_option("display.width", 200)
"""

EDA_LOAD = '''
# O CSV usa ';' como separador. O caminho e relativo a raiz do repo, entao
# o notebook roda em qualquer maquina depois de abrir a pasta do projeto.
df = pd.read_csv("../data/{fname}", sep=";")
df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", dayfirst=True)
df = df.sort_values("Date").reset_index(drop=True)
print("{label} - {{}} dias".format(len(df)))
'''

EDA_VIEWS = [
    "df.head()",
    "df.info()",
    "df.describe()",
]

# ---------------------------------------------------------------- data_load
data_load = nbf.v4.new_notebook(
    cells=[
        md(
            "# Carga dos dados\n\n"
            "Os dois CSVs já estão versionados em `data/`, então o notebook roda **offline**.\n"
            "O bloco do Kaggle é opcional: só é usado se você quiser re-baixar o dataset original."
        ),
        code(
            """
import os
import shutil

import pandas as pd

pd.set_option("display.width", 200)
"""
        ),
        md(
            "## 1. (Opcional) baixar o dataset do Kaggle\n\n"
            "Precisa de `~/.kaggle/kaggle.json`. Se você não tem, pule para o passo 2 —\n"
            "os arquivos em `data/` já são os do dataset."
        ),
        code(
            """
DATASET = "ilkeryildiz/example-dataset-for-ab-test"
ARQUIVOS = ["control_group.csv", "test_group.csv"]

caminho_destino = os.path.join("..", "data")
os.makedirs(caminho_destino, exist_ok=True)

try:
    import kagglehub

    path = kagglehub.dataset_download(DATASET)
    print("Dataset baixado em:", path)
    for nome in ARQUIVOS:
        shutil.copy(os.path.join(path, nome), os.path.join(caminho_destino, nome))
        print(f"  copiado: {nome}")
except Exception as exc:  # kagglehub ausente, sem credencial ou sem rede
    print("Download ignorado:", type(exc).__name__, exc)
    print("Seguindo com os arquivos que ja estao em data/.")
"""
        ),
        md(
            "## 2. Carregar os dois grupos\n\n"
            "Detalhe que quebrava a análise: **o CSV usa `;` como separador**, não `,`.\n"
            "Ler com o padrão do pandas colocava a linha inteira numa coluna só, e aí\n"
            "era preciso um `fix_dataframe()` para consertar depois."
        ),
        code(
            """
SEP = ";"  # o dataset usa ponto e virgula

df_control = pd.read_csv(os.path.join(caminho_destino, "control_group.csv"), sep=SEP)
df_test = pd.read_csv(os.path.join(caminho_destino, "test_group.csv"), sep=SEP)

for nome, df in (("control", df_control), ("test", df_test)):
    df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", dayfirst=True)
    df["group"] = nome

df_ab = pd.concat([df_control, df_test], ignore_index=True).sort_values(
    ["group", "Date"]
).reset_index(drop=True)

print("Colunas:", list(df_ab.columns))
print()
df_ab.head()
"""
        ),
        code(
            """
df_ab.info()
"""
        ),
        code(
            """
df_ab.groupby("group")[["Spend [USD]", "# of Impressions", "# of Purchase"]].agg(["sum", "mean"]).round(1)
"""
        ),
    ],
    metadata=METADATA,
    nbformat=4,
    nbformat_minor=5,
)

# ------------------------------------------------------------- eda_CG / TG
for fname, var, campaign, label in LOADERS.values():
    cells = [
        md(
            f"# EDA — {label}\n\n"
            f"Dataset: `ilkeryildiz/example-dataset-for-ab-test` · campanha `{campaign}`.\n\n"
            "Este notebook roda a partir da raiz do projeto. O CSV é separado por `;` e a\n"
            "coluna de data vem em `dd.mm.aaaa`."
        ),
        code(EDA_CELLS),
        code(EDA_LOAD.format(fname=fname, label=label)),
    ]
    cells += [code(v) for v in EDA_VIEWS]
    cells.append(
        md(
            "## Séries diárias\n\n"
            "Spend e impressões ao longo dos 30 dias, para ver se há sazonalidade que\n"
            "possa confundir a comparação entre os grupos."
        )
    )
    cells.append(
        code(
            f"""
df.set_index("Date")[["Spend [USD]", "# of Impressions", "# of Website Clicks", "# of Purchase"]].plot(
    subplots=True, figsize=(14, 9), sharex=True, title="{label}"
)
plt.tight_layout()
plt.show()
"""
        )
    )
    cells.insert(
        2,
        code(
            "import matplotlib.pyplot as plt\n"
            "import seaborn as sns\n\n"
            "plt.style.use('dark_background')\n"
            "sns.set_palette('husl')\n"
        ),
    )

    nb = nbf.v4.new_notebook(
        cells=cells, metadata=METADATA, nbformat=4, nbformat_minor=5
    )
    (NB_DIR / f"{var.replace('df_', 'eda_')}.ipynb").write_text(
        nbf.writes(nb), encoding="utf-8"
    )
    print("escrito:", f"{var.replace('df_', 'eda_')}.ipynb")

# -------------------------------------------------------- comparacao_metricas
comparacao = nbf.v4.new_notebook(
    cells=[
        md(
            "# Comparação entre os grupos — Control vs Test\n\n"
            "Controle: **Maximum Bidding** · Teste: **Average Bidding**.\n\n"
            "Duas correções em relação à versão anterior deste notebook:\n\n"
            "1. **ROI foi removido.** O dataset não tem receita — só contagens e gasto —\n"
            "   então ROI (`(receita - gasto) / gasto`) é **incalculável** aqui. No lugar,\n"
            "   as métricas deriváveis de verdade: CPA, CTR, CPC, CPM, taxa de carrinho\n"
            "   e taxa de compra.\n"
            "2. **A conclusão é calculada, não digitada.** A versão anterior fixava os\n"
            "   percentuais (`+18.8`, `-1.9`, `-12.9`) como constantes no código e depois\n"
            "   imprimia uma recomendação a partir deles.\n\n"
            "Além disso, o teste de significância decide se a diferença é ruído ou real."
        ),
        code(
            """
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

pd.set_option("display.width", 220)

plt.style.use("dark_background")
sns.set_palette("husl")
plt.rcParams["figure.figsize"] = (14, 8)
plt.rcParams["font.size"] = 12

warnings.filterwarnings("ignore", category=FutureWarning)
"""
        ),
        md("## 1. Carga"),
        code(
            """
SEP = ";"


def carregar(caminho, rotulo):
    df = pd.read_csv(caminho, sep=SEP)
    df["Date"] = pd.to_datetime(df["Date"], format="%d.%m.%Y", dayfirst=True)
    return df.sort_values("Date").reset_index(drop=True), rotulo


df_CG_fixed, rotulo_CG = carregar("../data/control_group.csv", "Controle")
df_TG_fixed, rotulo_TG = carregar("../data/test_group.csv", "Teste")

print(f"{rotulo_CG}: {len(df_CG_fixed)} dias | {rotulo_TG}: {len(df_TG_fixed)} dias")
df_CG_fixed.head()
"""
        ),
        md("## 2. Métricas derivadas\n\nO dataset traz gasto e contagens de funil, mas não traz receita. Por isso o ROI não é calculável — as métricas abaixo são as que os dados sustentam de fato."),
        code(
            """
TOTAIS = {
    "cliques": "# of Website Clicks",
    "impressoes": "# of Impressions",
    "carrinhos": "# of Add to Cart",
    "compras": "# of Purchase",
}


def derivar(df):
    \"\"\"Métricas de custo e de funil. CPA = gasto / compras.\"\"\"
    out = df.copy()
    out["CPA"] = out["Spend [USD]"] / out[TOTAIS["compras"]].replace(0, np.nan)
    out["CTR"] = out[TOTAIS["cliques"]] / out[TOTAIS["impressoes"]].replace(0, np.nan)
    out["CPC"] = out["Spend [USD]"] / out[TOTAIS["cliques"]].replace(0, np.nan)
    out["CPM"] = out["Spend [USD]"] / out[TOTAIS["impressoes"]].replace(0, np.nan) * 1000
    out["Taxa carrinho"] = out[TOTAIS["carrinhos"]] / out[TOTAIS["cliques"]].replace(0, np.nan)
    out["Taxa compra"] = out[TOTAIS["compras"]] / out[TOTAIS["cliques"]].replace(0, np.nan)
    return out


CG = derivar(df_CG_fixed)
TG = derivar(df_TG_fixed)

resumo = pd.DataFrame(
    {
        "Controle": CG.mean(numeric_only=True),
        "Teste": TG.mean(numeric_only=True),
    }
)
resumo["Δ %"] = (resumo["Teste"] - resumo["Controle"]) / resumo["Controle"] * 100
resumo.round(3)
"""
        ),
        md("## 3. Gasto e volume absolutos"),
        code(
            """
totais = pd.DataFrame(
    {
        "Gasto (USD)": [CG["Spend [USD]"].sum(), TG["Spend [USD]"].sum()],
        "Impressões": [CG["# of Impressions"].sum(), TG["# of Impressions"].sum()],
        "Cliques": [CG["# of Website Clicks"].sum(), TG["# of Website Clicks"].sum()],
        "Compras": [CG["# of Purchase"].sum(), TG["# of Purchase"].sum()],
    },
    index=["Controle", "Teste"],
)
totais["Δ %"] = (totais.loc["Teste"] - totais.loc["Controle"]) / totais.loc["Controle"] * 100
totais.round(2)
"""
        ),
        md("### 3.1. Comparação das contagens bruteiras (média diária)"),
        code(
            """
metrics = [
    "Spend [USD]",
    "# of Impressions",
    "Reach",
    "# of Website Clicks",
    "# of Searches",
    "# of View Content",
    "# of Add to Cart",
    "# of Purchase",
]

fig, axes = plt.subplots(2, 4, figsize=(20, 12))
axes = axes.ravel()

for i, metric in enumerate(metrics):
    media_control = CG[metric].mean()
    media_test = TG[metric].mean()

    bars = axes[i].bar(["Controle", "Teste"], [media_control, media_test],
                       color=["#1f77b4", "#ff7f0e"], alpha=0.8)
    axes[i].axhline(y=media_control, color="white", linestyle="--", alpha=0.7)

    for bar, value in zip(bars, [media_control, media_test]):
        altura = bar.get_height()
        rotulo = f"${value:,.0f}" if metric == "Spend [USD]" else f"{value:,.0f}"
        axes[i].text(bar.get_x() + bar.get_width() / 2, altura * 1.01,
                     rotulo, ha="center", va="bottom", fontweight="bold")

    pct = (media_test - media_control) / media_control * 100 if media_control else 0
    axes[i].set_title(f"{metric}\\nΔ: {pct:+.1f}%",
                      color="green" if pct > 0 else "red", fontweight="bold")
    axes[i].set_ylabel("Média diária")
    axes[i].grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
"""
        ),
        md("### 3.2. Investimento total"),
        code(
            """
def barras_totais(titulo, valores, sufixo=""):
    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.bar(["Controle", "Teste"], valores, color=["#1f77b4", "#ff7f0e"], alpha=0.8)
    for bar, value in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                f"{value:,.0f}{sufixo}", ha="center", va="bottom", fontweight="bold")
    delta = (valores[1] - valores[0]) / valores[0] * 100
    ax.set_title(f"{titulo}\\nΔ: {delta:+.1f}%",
                 color="green" if delta > 0 else "red", fontweight="bold", fontsize=16)
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()


barras_totais("INVESTIMENTO TOTAL", [CG["Spend [USD]"].sum(), TG["Spend [USD]"].sum()], " USD")
"""
        ),
        code(
            """
barras_totais("TOTAL DE COMPRAS", [CG["# of Purchase"].sum(), TG["# of Purchase"].sum()])
"""
        ),
        md("### 3.3. CPA — custo por compra (o que substituiu o ROI inexistente)"),
        code(
            """
cpa_control = CG["Spend [USD]"].sum() / CG["# of Purchase"].sum()
cpa_test = TG["Spend [USD]"].sum() / TG["# of Purchase"].sum()

fig, ax = plt.subplots(figsize=(10, 6))
bars = ax.bar(["Controle", "Teste"], [cpa_control, cpa_test],
              color=["#1f77b4", "#ff7f0e"], alpha=0.8)
for bar, value in zip(bars, [cpa_control, cpa_test]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
            f"${value:.2f}", ha="center", va="bottom", fontweight="bold", fontsize=12)

delta_cpa = (cpa_test - cpa_control) / cpa_control * 100
# CPA menor e melhor, entao o sinal da cor e invertido em relacao as demais metricas
ax.set_title(f"CPA (custo por compra)\\nΔ: {delta_cpa:+.1f}%",
             color="red" if delta_cpa > 0 else "green", fontweight="bold", fontsize=16)
ax.set_ylabel("USD por compra", fontweight="bold")
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()

print(f"CPA Controle: ${cpa_control:.2f}")
print(f"CPA Teste:    ${cpa_test:.2f}")
"""
        ),
        md("### 3.4. Taxas de funil"),
        code(
            """
taxas = ["CTR", "Taxa carrinho", "Taxa compra"]
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

for ax, taxa in zip(axes, taxas):
    valores = [CG[taxa].mean(), TG[taxa].mean()]
    bars = ax.bar(["Controle", "Teste"], valores, color=["#1f77b4", "#ff7f0e"], alpha=0.8)
    for bar, value in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() * 1.01,
                f"{value:.2%}", ha="center", va="bottom", fontweight="bold")
    delta = (valores[1] - valores[0]) / valores[0] * 100
    ax.set_title(f"{taxa}\\nΔ: {delta:+.1f}%",
                 color="green" if delta > 0 else "red", fontweight="bold", fontsize=14)
    ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()
"""
        ),
        md(
            "## 4. A diferença é real ou é ruído?\n\n"
            "Aqui está a pegadinha clássica deste dataset, e ela muda a conclusão.\n\n"
            "O número óbvio é o z-test sobre as contagens agregadas: 175 mil cliques no\n"
            "teste contra 154 mil no controle. Mas **cliques dentro do mesmo dia não são\n"
            "independentes** — o dia traz a mesma condição de tempo, a mesma verba e a mesma\n"
            "público-alvo. Somar 175 mil cliques como se fossem 175 mil observações\n"
            "independentes é *pseudoreplicação*: infla o n e zera o p-value.\n\n"
            "A unidade experimental real é o **dia**, então são 30 observações por braço.\n"
            "O teste principal é o **t-test de Welch** sobre a taxa de compra diária, com o\n"
            "Mann-Whitney como checagem não-paramétrica. O z-test aparece só para mostrar\n"
            "por que ele engana."
        ),
        code(
            """
ALFA = 0.05

compras_c, cliques_c = CG["# of Purchase"].sum(), CG["# of Website Clicks"].sum()
compras_t, cliques_t = TG["# of Purchase"].sum(), TG["# of Website Clicks"].sum()

# --- taxa diaria: a unidade experimental correta (1 ponto por dia) ---
diaria_cg = CG["Taxa compra"].dropna()
diaria_tg = TG["Taxa compra"].dropna()


def z_test_ingenuo(sucesso_a, total_a, sucesso_b, total_b):
    \"\"\"z-test de duas proporcoes. ASSUME independência entre cliques — violada aqui.\"\"\"
    p1, p2 = sucesso_a / total_a, sucesso_b / total_b
    p_pool = (sucesso_a + sucesso_b) / (total_a + total_b)
    erro = np.sqrt(p_pool * (1 - p_pool) * (1 / total_a + 1 / total_b))
    z = (p2 - p1) / erro
    return p1, p2, z, 2 * (1 - stats.norm.cdf(abs(z)))


p_cg, p_tg, z_ingenuo, p_z_ingenuo = z_test_ingenuo(
    compras_c, cliques_c, compras_t, cliques_t
)
t_stat, p_t = stats.ttest_ind(diaria_tg, diaria_cg, equal_var=False)
u_stat, p_u = stats.mannwhitneyu(diaria_tg, diaria_cg, alternative="two-sided")

print("=== TESTE PRINCIPAL: taxa de compra DIARIA (n = 30 por braco) ===")
print(f"  Controle: {diaria_cg.mean():.4%} (desvio {diaria_cg.std():.4%})")
print(f"  Teste:    {diaria_tg.mean():.4%} (desvio {diaria_tg.std():.4%})")
print(f"  t-test de Welch  : t = {t_stat:.3f} | p = {p_t:.4f} -> "
      f"{'REJEITA H0' if p_t < ALFA else 'NAO REJEITA H0'}")
print(f"  Mann-Whitney U   : U = {u_stat:.1f} | p = {p_u:.4f} -> "
      f"{'REJEITA H0' if p_u < ALFA else 'NAO REJEITA H0'}")
print()
print("=== TESTE INGENUO: proporcoes sobre as contagens agregadas ===")
print(f"  Controle: {p_cg:.4%} ({compras_c:,.0f} / {cliques_c:,.0f})")
print(f"  Teste:    {p_tg:.4%} ({compras_t:,.0f} / {cliques_t:,.0f})")
print(f"  z = {z_ingenuo:.3f} | p = {p_z_ingenuo:.2e}")
print("  ^ Parece significativo, mas so porque trata 175 mil cliques como independentes.")
print("    Cliques do mesmo dia sao correlacionados; esse p-value nao e confiavel.")

significante = p_t < ALFA
print()
print("VEREDITO DE SIGNIFICANCIA (usa o teste diario):",
      "diferenca significativa." if significante
      else f"diferenca NAO significativa (p = {p_t:.3f} >= {ALFA}).")
"""
        ),
        md(
            "## 5. Conclusão (calculada a partir dos números acima)\n\n"
            "A regra de decisão lê o teste diário, não o z-test ingênuo."
        ),
        code(
            """
print("=" * 68)
print("CONCLUSAO - ANALISE FINANCEIRA DO TESTE A/B")
print("=" * 68)

dados = {
    "Gasto total": (CG["Spend [USD]"].sum(), TG["Spend [USD]"].sum()),
    "Compras": (CG["# of Purchase"].sum(), TG["# of Purchase"].sum()),
    "CPA (USD)": (cpa_control, cpa_test),
}
for nome, (c, t_) in dados.items():
    delta = (t_ - c) / c * 100
    print(f"  {nome:<14} Controle {c:>12,.2f} | Teste {t_:>12,.2f} | delta {delta:+6.1f}%")

print()
print(f"  Taxa de compra diaria: Controle {diaria_cg.mean():.4%} -> Teste {diaria_tg.mean():.4%}")
print(f"  t-test de Welch  p = {p_t:.4f}  ->  "
      f"{'significativo' if significante else 'NAO significativo'} a {ALFA:.0%}")
print(f"  Mann-Whitney U   p = {p_u:.4f}")
print(f"  (z-test ingenuo daria p = {p_z_ingenuo:.2e}, mas ele e pseudoreplicacao)")

# --- regra de decisao, escrita sobre os numeros calculados acima ---
teste_melhor = cpa_test < cpa_control
print()
print("=" * 68)
if significante and teste_melhor:
    print("VEREDITO: adotar o TESTE.")
    print("  CPA menor com conversao significativamente melhor.")
elif significante and not teste_melhor:
    print("VEREDITO: manter a campanha de CONTROLE.")
    print("  Conversao significativamente pior e CPA maior.")
elif not significante and teste_melhor:
    print("VEREDITO: inconclusivo, sem base para trocar.")
    print("  O teste tem CPA menor, mas com 30 dias por braco a diferenca de conversao")
    print(f"  nao atinge significancia (p = {p_t:.3f}). Rodar mais dias antes de decidir.")
else:
    print("VEREDITO: manter a campanha de CONTROLE, por ora.")
    print("  O teste tem CPA pior e a diferenca nao e estatisticamente significativa")
    print(f"  (p = {p_t:.3f}): nao ha ganho que justifique trocar. E, como o teste gasta mais,")
    print("  o custo de esperar por mais dados e menor que o custo de adota-lo errado.")

print()
print("Impacto do periodo, se o teste fosse adotado:")
custo_extra = cpa_test - cpa_control
print(f"  Custo extra por compra:  ${custo_extra:,.2f}")
print(f"  Custo extra em {len(TG)} dias:  ${custo_extra * TG['# of Purchase'].sum():,.2f}")
print("=" * 68)
"""
        ),
    ],
    metadata=METADATA,
    nbformat=4,
    nbformat_minor=5,
)

(NB_DIR / "data_load.ipynb").write_text(nbf.writes(data_load), encoding="utf-8")
(NB_DIR / "comparacao_metricas.ipynb").write_text(nbf.writes(comparacao), encoding="utf-8")
print("escrito: data_load.ipynb")
print("escrito: comparacao_metricas.ipynb")
