"""
Coleta de partidas do São Paulo no Brasileirão (2024-2026) via API do Sofascore.
"""

from curl_cffi import requests
import time
import pandas as pd
from datetime import datetime

ID_SAO_PAULO = 1981

cabecalhos = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://www.sofascore.com/",
}


def extrair_jogo(evento: dict) -> dict | None:
    if evento["tournament"]["uniqueTournament"]["slug"] != "brasileirao-serie-a":
        return None
    if evento["status"]["type"] != "finished":
        return None

    mandante = evento["homeTeam"]["id"] == ID_SAO_PAULO
    gols_pro = evento["homeScore"]["current"] if mandante else evento["awayScore"]["current"]
    gols_contra = evento["awayScore"]["current"] if mandante else evento["homeScore"]["current"]

    if gols_pro > gols_contra:
        resultado = "V"
    elif gols_pro < gols_contra:
        resultado = "D"
    else:
        resultado = "E"

    return {
        "match_id": evento["id"],
        "data": datetime.fromtimestamp(evento["startTimestamp"]),
        "temporada": evento["season"]["year"],
        "adversario": evento["awayTeam"]["name"] if mandante else evento["homeTeam"]["name"],
        "mandante": mandante,
        "gols_pro": gols_pro,
        "gols_contra": gols_contra,
        "resultado": resultado,
    }


def coletar_partidas() -> pd.DataFrame:
    todos_os_jogos = []
    pagina = 0

    while True:
        url = f"https://api.sofascore.com/api/v1/team/{ID_SAO_PAULO}/events/last/{pagina}"
        resposta = requests.get(url, headers=cabecalhos, impersonate="chrome")
        dados = resposta.json()

        jogos_da_pagina = [extrair_jogo(evento) for evento in dados["events"]]
        jogos_da_pagina = [jogo for jogo in jogos_da_pagina if jogo is not None]
        todos_os_jogos.extend(jogos_da_pagina)

        print(f"Página {pagina}: {len(jogos_da_pagina)} jogos do Brasileirão")

        temporadas_da_pagina = {evento["season"]["year"] for evento in dados["events"]}
        if "2023" in temporadas_da_pagina or not dados["hasNextPage"]:
            break

        pagina += 1
        time.sleep(2)

    partidas = pd.DataFrame(todos_os_jogos)
    partidas = partidas[partidas["temporada"].isin(["2024", "2025", "2026"])]
    partidas = partidas.sort_values("data").reset_index(drop=True)
    return partidas


if __name__ == "__main__":
    import os

    partidas = coletar_partidas()
    print(partidas.shape)
    print(partidas["temporada"].value_counts())

    os.makedirs("data/processed", exist_ok=True)
    partidas.to_parquet("data/processed/partidas.parquet", index=False)
    print("Salvo em data/processed/partidas.parquet")
