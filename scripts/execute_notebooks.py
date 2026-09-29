"""Executa os 4 notebooks a partir da pasta notebooks/ e salva com as saidas."""

import sys
from pathlib import Path

import nbformat
from nbclient import NotebookClient

NB_DIR = Path("notebooks")
NAMES = ["data_load", "eda_CG", "eda_TG", "comparacao_metricas"]

falhas = 0

for nome in NAMES:
    caminho = NB_DIR / f"{nome}.ipynb"
    nb = nbformat.read(caminho, as_version=4)
    nb.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    client = NotebookClient(
        nb,
        timeout=300,
        kernel_name="python3",
        resources={"metadata": {"path": str(NB_DIR.resolve())}},
        allow_errors=False,
    )
    try:
        client.execute()
    except Exception as exc:
        falhas += 1
        print(f"[FALHOU] {nome}: {type(exc).__name__}")
        # salva assim mesmo, para inspecionar onde parou
        nbformat.write(nb, caminho)
        mensagem = str(exc)
        for linha in mensagem.splitlines()[:14]:
            print("    " + linha)
        continue

    nbformat.write(nb, caminho)
    tamanho = caminho.stat().st_size
    print(f"[ok] {nome:<22} {tamanho / 1024:7.1f} KB")

sys.exit(1 if falhas else 0)
