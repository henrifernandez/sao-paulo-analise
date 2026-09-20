"""
Coleta de estatísticas por partida dos jogadores-chave definidos em config.py
(minutos, nota, desarmes, duelos ganhos, passes certos).
"""

from curl_cffi import requests
import time
import pandas as pd

from config import JOGADORES_CHAVE

cabecalhos = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sofascore.com/",
}


def extrair_jogadores_chave(match_id: int) -> list[dict]:
    url = f"https://api.sofascore.com/api/v1/event/{match_id}/lineups"
    resposta = requests.get(url, headers=cabecalhos, impersonate="chrome")

    if resposta.status_code != 200:
        return []

    dados = resposta.json()
    todos_jogadores = dados["home"]["players"] + dados["away"]["players"]

    linhas = []
    for entrada in todos_jogadores:
        nome = entrada["player"]["name"]
        if nome not in JOGADORES_CHAVE:
            continue

        stats = entrada.get("statistics", {})

        linhas.append({
            "match_id": match_id,
            "jogador": nome,
            "posicao": entrada["player"]["position"],
            "titular": not entrada["substitute"],
            "minutos": stats.get("minutesPlayed"),
            "nota": stats.get("rating"),
            "desarmes": stats.get("totalTackle"),
            "duelos_ganhos": stats.get("duelWon"),
            "passes_certos": stats.get("accuratePass"),
            "passes_tentados": stats.get("totalPass"),
        })

    return linhas


def coletar_estatisticas_jogador(partidas: pd.DataFrame) -> pd.DataFrame:
    todas_as_linhas = []

    for i, linha in partidas.iterrows():
        todas_as_linhas.extend(extrair_jogadores_chave(linha["match_id"]))

        if i % 10 == 0:
            print(f"{i}/{len(partidas)} jogos processados")

        time.sleep(1.5)

    estatisticas_jogador = pd.DataFrame(todas_as_linhas)
    estatisticas_jogador["passes_certos_pct"] = (
        estatisticas_jogador["passes_certos"] / estatisticas_jogador["passes_tentados"] * 100
    )
    return estatisticas_jogador


if __name__ == "__main__":
    partidas = pd.read_parquet("data/processed/partidas.parquet")
    estatisticas_jogador = coletar_estatisticas_jogador(partidas)
    estatisticas_jogador.to_parquet("data/processed/estatisticas_jogador.parquet", index=False)
    print(f"Salvo: {len(estatisticas_jogador)} linhas de jogador-partida")
