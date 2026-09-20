"""
Comparações estatísticas entre vitórias e derrotas, em nível de time e de
jogador-chave.
"""

import pandas as pd
from scipy.stats import mannwhitneyu


def comparar_time(partidas: pd.DataFrame, estatisticas_time: pd.DataFrame) -> pd.DataFrame:
    completo = partidas.merge(estatisticas_time, on="match_id", how="inner")

    colunas_metricas = ["posse", "chutes", "escanteios", "faltas", "cartoes_amarelos", "xg"]
    vitorias = completo[completo["resultado"] == "V"]
    derrotas = completo[completo["resultado"] == "D"]

    resultados_teste = []
    for coluna in colunas_metricas:
        if vitorias[coluna].nunique() <= 1 or derrotas[coluna].nunique() <= 1:
            continue

        estatistica, p_valor = mannwhitneyu(vitorias[coluna], derrotas[coluna], method="asymptotic")

        resultados_teste.append({
            "metrica": coluna,
            "mediana_vitorias": vitorias[coluna].median(),
            "mediana_derrotas": derrotas[coluna].median(),
            "p_valor": round(p_valor, 4) if pd.notna(p_valor) else None,
            "significativo": bool(p_valor < 0.05) if pd.notna(p_valor) else False,
        })

    return pd.DataFrame(resultados_teste).sort_values("p_valor")


def comparar_jogadores(partidas: pd.DataFrame, estatisticas_jogador: pd.DataFrame) -> pd.DataFrame:
    completo = estatisticas_jogador.merge(
        partidas[["match_id", "resultado"]], on="match_id", how="inner"
    )

    resultados = []
    for jogador in completo["jogador"].unique():
        dados_jogador = completo[completo["jogador"] == jogador]
        vitorias = dados_jogador[dados_jogador["resultado"] == "V"]["nota"].dropna()
        derrotas = dados_jogador[dados_jogador["resultado"] == "D"]["nota"].dropna()

        if len(vitorias) < 5 or len(derrotas) < 5:
            resultados.append({
                "jogador": jogador, "jogos_vitoria": len(vitorias), "jogos_derrota": len(derrotas),
                "mediana_vitorias": None, "mediana_derrotas": None, "p_valor": None,
                "significativo": False, "observacao": "amostra pequena demais",
            })
            continue

        estatistica, p_valor = mannwhitneyu(vitorias, derrotas, method="asymptotic")
        resultados.append({
            "jogador": jogador, "jogos_vitoria": len(vitorias), "jogos_derrota": len(derrotas),
            "mediana_vitorias": round(vitorias.median(), 2),
            "mediana_derrotas": round(derrotas.median(), 2),
            "p_valor": round(p_valor, 4), "significativo": p_valor < 0.05, "observacao": "",
        })

    return pd.DataFrame(resultados).sort_values("p_valor")


if __name__ == "__main__":
    partidas = pd.read_parquet("data/processed/partidas.parquet")
    estatisticas_time = pd.read_parquet("data/processed/estatisticas_time.parquet")
    estatisticas_jogador = pd.read_parquet("data/processed/estatisticas_jogador.parquet")

    print("=== Comparação de time (vitórias x derrotas) ===")
    print(comparar_time(partidas, estatisticas_time))

    print("\n=== Comparação de jogadores-chave (nota, vitórias x derrotas) ===")
    print(comparar_jogadores(partidas, estatisticas_jogador))