# Teste A/B — Campanhas de Marketing Digital

Análise de teste A/B sobre um dataset público de campanhas do Facebook Ads: **30 dias de
`Control Campaign` (Maximum Bidding) contra 30 dias de `Test Campaign` (Average Bidding)**.

A pergunta não é "qual grupo converteu mais", e sim **"devo trocar a campanha?"** — o que exige
julgar custo por compra e, antes de decidir, checar se a diferença é real ou ruído.

---

## 1. Dataset

| Coluna | Descrição |
|---|---|
| `Campaign Name` | `Control Campaign` ou `Test Campaign` |
| `Date` | dia da campanha (`dd.mm.aaaa`) |
| `Spend [USD]` | investimento diário |
| `# of Impressions` | impressões |
| `Reach` | alcance |
| `# of Website Clicks` | cliques no site |
| `# of Searches` | buscas |
| `# of View Content` | visualizações de conteúdo |
| `# of Add to Cart` | adições ao carrinho |
| `# of Purchase` | compras |

> ⚠️ **O separador é `;`, não `,`.** Ler com o padrão do pandas coloca a linha inteira numa coluna
> só. Foi o que obrigou a versão anterior deste projeto a consertar os DataFrames *depois* da leitura.
> Todos os notebooks agora leem com `sep=';'`.

> ℹ️ **O dataset não tem receita.** Só há gasto e contagens de funil. Isso significa que **ROI
> (`(receita − gasto) / gasto`) e ROAS são incalculáveis aqui** — não é uma falha da análise, é
> ausência de dado. As métricas deriváveis são custo por compra e as taxas de funil.

## 2. Resultado

| Métrica | Controle | Teste | Δ |
|---|---:|---:|---:|
| Gasto total (30 d) | $68.653 | $76.892 | **+12,0%** |
| Compras (30 d) | 15.161 | 14.869 | **−1,9%** |
| **CPA** | **$4,53** | **$5,17** | **+14,2%** |
| Taxa de compra (cliques → compra) | 9,83% | 8,49% | −1,3 p.p. |

**Teste de significância (unidade experimental = dia, n = 30 por braço):**

| Teste | p | Decisão a 5% |
|---|---:|---|
| t-test de Welch (taxa diária) | **0,123** | não rejeita H₀ |
| Mann-Whitney U (não-paramétrico) | 0,263 | não rejeita H₀ |

**Veredito: manter a campanha de controle, por ora — e o resultado é inconclusivo.**

O teste gasta 12% a mais, converte um pouco pior e tem CPA 14% mais alto, mas com 30 dias por braço
a diferença **não atinge significância estatística**. Não há ganho que justifique a troca, e como o
teste custa mais, esperar por mais dados é a opção de menor risco. Adotá-lo teria custado
**$9.561 a mais** nos mesmos 30 dias.

### A armadilha do p-value

Aplicar z-test de duas proporções sobre as contagens agregadas dá **p ≈ 0** (z = −13,3) e sugere um
resultado "altamente significativo". Esse número está errado: ele trata os 175.107 cliques do grupo
de teste como 175.107 observações independentes, mas cliques do mesmo dia são correlacionados — mesmo
tempo, mesma verba, mesmo público. Isso é *pseudoreplicação*: infla o n artificialmente e zera o
p-value. A unidade experimental real é o **dia**, e são apenas 30 por braço.

O `notebooks/comparacao_metricas.ipynb` mostra os dois lado a lado para deixar a diferença explícita.

## 3. Estrutura

```text
teste-ab-projeto/
├── data/
│   ├── control_group.csv       # 30 dias, Maximum Bidding
│   └── test_group.csv          # 30 dias, Average Bidding
├── notebooks/
│   ├── data_load.ipynb         # carga (Kaggle opcional) + leitura com sep=';'
│   ├── eda_CG.ipynb            # EDA do grupo de controle
│   ├── eda_TG.ipynb            # EDA do grupo de teste
│   └── comparacao_metricas.ipynb  # métricas, gráficos, significância e conclusão
├── scripts/
│   ├── build_notebooks.py      # gera os 4 notebooks (fonte da verdade)
│   └── execute_notebooks.py    # executa e salva com as saídas
├── requirements.txt
└── README.md
```

## 4. Como executar

Rode a partir da **raiz do repositório** (os notebooks usam caminho relativo `../data/`):

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows | source .venv/bin/activate (Linux/Mac)
pip install -r requirements.txt

# opcional: regenera os notebooks a partir do script
python scripts/build_notebooks.py

# executa e salva as saídas
python scripts/execute_notebooks.py
```

Depois é só abrir os `.ipynb` no Jupyter, na ordem: `data_load` → `eda_CG` → `eda_TG` →
`comparacao_metricas`.

## 5. Correções aplicadas

A versão anterior dos notebooks não rodava fora da máquina de origem. O que estava quebrado:

| Problema | Correção |
|---|---|
| Caminho absoluto `/home/art/test_AB_projeto/...` | Caminho relativo a partir da raiz do projeto |
| CSV lido com `,` e consertado depois por `fix_dataframe()` | Leitura direta com `sep=';'`; o `fix_dataframe()` sumiu |
| `df['ROI']` e `df['CPA']` — **colunas que não existem no dataset** (`KeyError`) | CPA calculado como `gasto / compras`; ROI removido por ser incalculável sem receita |
| Conclusão com percentuais **digitados à mão** (`+18.8`, `−1.9`, `−12.9` como "dado da sua análise") | Todos os deltas calculados a partir dos dados |
| `df_TG.describe` sem parênteses, e o notebook nunca executado | Corrigido e executado |
| Kernelspec `venv` (nome da máquina de origem) | `python3`, padrão em qualquer instalação |
| `data_load` dependia do cache do Kaggle em `/home/art/.cache/...` | Download opcional; os CSVs versionados bastam |

Os números reais divergem dos que estavam fixados no código: o CPA do teste é **+14,2%**, não +18,8%.

## 6. Limitações

- **30 dias por braço é pouco poder.** Para detectar uma diferença de cerca de 1,3 p.p. na taxa de
  compra seriam necessários bem mais dias. O resultado correto aqui é "inconclusivo", não "o teste
  é pior".
- **Sem receita**, então ROAS/ROI ficam fora do alcance deste dataset.
- **Comparação não é aleatorizada:** os dois braços são campanhas diferentes e não têm, por desenho,
  tráfego sorteado no mesmo período. Não há garantia de que os grupos sejam comparáveis — uma
  sazonalidade ou um público diferente explica parte da diferença observada.
- Dataset público de exemplo, não dados de uma campanha real.

## 7. Próximos passos

- Incluir receita por conversão para liberar **ROAS**, que é a métrica que fecha a conta de verdade.
- Estender a janela além de 30 dias e rodar um teste de potência (*power analysis*) para definir
  quantos dias são necessários antes de decidir.
- Segmentar por dispositivo/público, se o dado for além das 9 colunas.
- Recalcular automaticamente quando o `execute_notebooks.py` rodar, para o relatório nunca ficar
  defasado em relação aos dados.

## 8. Licença e dados

Código sob licença **MIT**. O dataset `ilkeryildiz/example-dataset-for-ab-test` é de distribuição
pública no Kaggle e está versionado em `data/` por ser pequeno (~4 KB).
