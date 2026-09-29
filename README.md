# Teste A/B — Campanhas de Marketing

> ⚠️ **Status: trabalho em andamento (WIP).** A análise comparativa **não está concluída**.
> Este repositório está published como registro do progresso, não como resultado finalizado.
> Veja ["O que falta"](#o-que-falta) antes de levar este projeto para uma entrevista.

Análise de teste A/B sobre um dataset público de campanhas de marketing digital
(30 dias de `Control Campaign` vs 30 dias de `Test Campaign`).

---

## 1. Dataset

Fonte: dados de campanhas do Facebook Ads, partitioned em grupo de controle e grupo de teste.
Os CSVs usam `;` como separador e trazem uma linha por dia, com 9 campos:

| Coluna | Descrição |
|---|---|
| `Campaign Name` | `Control Campaign` ou `Test Campaign` |
| `Date` | dia da campanha (formato `dd.mm.yyyy`) |
| `Spend [USD]` | investimento diário |
| `# of Impressions` | impressões |
| `Reach` | alcance |
| `# of Website Clicks` | cliques no site |
| `# of Searches` | buscas |
| `# of View Content` | visualizações de conteúdo |
| `# of Add to Cart` | adições ao carrinho |
| `# of Purchase` | compras |

`data/control_group.csv` e `data/test_group.csv` estão versionados porque são pequenos
(~2 KB cada) e necessários para reproduzir a análise.

## 2. Estrutura

```
teste_ab_projeto/
├── data/
│   ├── control_group.csv       # 30 dias, grupo de controle
│   └── test_group.csv          # 30 dias, grupo de teste
└── notebooks/
    ├── data_load.ipynb         # carga e inspeção inicial
    ├── eda_CG.ipynb            # EDA do grupo de controle
    ├── eda_TG.ipynb            # EDA do grupo de teste (incompleto)
    └── comparacao_metricas.ipynb  # correções de parsing + beginnings da comparação
```

## 3. Como executar

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows | source .venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

Os notebooks também importam `kagglehub`, que foi usado para baixar o dataset do Kaggle.
Os CSVs já estão versionados, então a análise não depende de baixar nada.

## 4. O que falta

Estado real deste trabalho no momento:

1. **Caminhos absolutos hardcoded.** As células de carga usam
   `/home/art/test_AB_projeto/data/...`, que só existe na máquina original.
   Para executar, ajuste para um caminho relativo (`../data/control_group.csv`)
   ou suba a pasta `data/` para o `PYTHONPATH`.
2. **Parsing do CSV ainda é feito em código.** Como o separador é `;` e o CSV veio
   com tudo em uma coluna, os notebooks carregam com `pd.read_csv(...)` e depois
   quebram a string com `str.split(';')` dentro de `fix_dataframe()`. O passo
   natural é passar `sep=';'` e `decimal`/coerções de tipo direto na leitura.
3. **`eda_TG.ipynb` não foi executado** (zero células com saída).
4. **A comparação entre grupos não foi fechada.** Não há teste de significância
   nem cálculo de diferença entre `Test` e `Control` — que é o objetivo do projeto.

Sem os itens 1 e 2, os notebooks não rodam fora da máquina original. Sem os itens
3 e 4, não há resultado.

## 5. Próximos passos

- Ler os CSVs com `sep=';'` e eliminar `fix_dataframe()`.
- Rodar a EDA dos dois grupos de forma simétrica.
- Calcular as métricas de comparação (CTR, taxa de adição ao carrinho,
  taxa de conversão) por grupo e a diferença relativa.
- Aplicar um teste de significância (e.g. two-proportion z-test ou t-test nas
  taxas diárias) para dizer se a diferença do `Test Campaign` é real ou ruído.
- Consolidar em um relatório curto com a recomendação de campanha.

## 6. Nota

Este repositório faz parte de um conjunto de projetos de estudo e demonstração.
O dataset é de origem pública; nenhum dado sensível está versionado aqui.
