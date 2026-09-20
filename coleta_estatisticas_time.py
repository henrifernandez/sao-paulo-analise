"""
Coleta de estatísticas de dentro do jogo (posse, chutes, xG, faltas, cartões)
para cada partida já salva em data/processed/partidas.parquet.
"""

from curl_cffi import requests
import time
import pandas as pd

cabecalhos = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sofascore.com/",
}


def extrair_estatisticas_time(match_id: int, mandante: bool) -> dict | None:
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/statistics"
    resposta = requests.get(url, headers=cabecalhos, impersonate="chrome")

    if resposta.status_code != 200:
        return None

    dados = resposta.json()

    periodo_completo = next(
        (p for p in dados.get("statistics", []) if p["period"] == "ALL"), None
    )
    if periodo_completo is None:
        return None

    visao_geral = next(
        (g for g in periodo_completo["groups"] if g["groupName"] == "Match overview"),
        None,
    )
    if visao_geral is None:
        return None

    itens = {item["key"]: item for item in visao_geral["statisticsItems"]}

    def valor(chave: str):
        item = itens.get(chave)
        if item is None:
            return None
        return item["homeValue"] if mandante else item["awayValue"]

    return {
        "match_id": match_id,
        "posse": valor("ballPossession"),
        "chutes": valor("totalShotsOnGoal"),
        "escanteios": valor("cornerKicks"),
        "faltas": valor("fouls"),
        "cartoes_amarelos": valor("yellowCards"),
        "cartoes_vermelhos": valor("redCards"),
        "xg": valor("expectedGoals"),
        "passes": valor("passes"),
    }


def coletar_estatisticas_time(partidas: pd.DataFrame) -> pd.DataFrame:
    estatisticas = []

    for i, linha in partidas.iterrows():
        resultado = extrair_estatisticas_time(linha["match_id"], linha["mandante"])
        if resultado is not None:
            estatisticas.append(resultado)

        if i % 10 == 0:
            print(f"{i}/{len(partidas)} jogos processados")

        time.sleep(1.5)

    return pd.DataFrame(estatisticas)


if __name__ == "__main__":
    partidas = pd.read_parquet("data/processed/partidas.parquet")
    estatisticas_time = coletar_estatisticas_time(partidas)
    estatisticas_time.to_parquet("data/processed/estatisticas_time.parquet", index=False)
    print(f"Salvo: {len(estatisticas_time)} jogos com estatísticas")
