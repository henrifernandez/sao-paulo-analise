# Análise das derrotas do São Paulo FC

Projeto de ciência de dados que investiga por que o São Paulo perde no Brasileirão. Compara estatísticas de time e de jogadores-chave entre vitórias e derrotas em 102 partidas das temporadas 2024 a 2026, com testes estatísticos, um modelo de regressão logística e um painel interativo.

## O que a análise encontrou

- O **xG** (gols esperados) é o fator que mais separa vitórias de derrotas. A mediana é 1,52 nas vitórias contra 0,69 nas derrotas.
- Nas derrotas o time tem **mais posse de bola** (59,0% contra 52,5%), mas cria menos chances de qualidade. O relatório chama esse padrão de "posse estéril".
- Faltas, escanteios e cartões não distinguem vitórias de derrotas, então indisciplina não explica o problema.
- A nota dos dois zagueiros titulares e dos dois principais finalizadores cai nas derrotas, enquanto a do meio-campo se mantém estável.
- A regressão logística, usada como ranking de fatores e não para prever jogos, acerta 75,3% na validação cruzada, contra cerca de 50,6% de uma base ingênua.

O relatório completo, com tabelas, p-valores, limitações e próximos passos, está em [`RELATORIO.md`](RELATORIO.md).

## Como foi feito

- **Coleta** em Python com `curl_cffi`, a partir da API pública do Sofascore, em três etapas (partidas, estatísticas de time e estatísticas dos jogadores-chave).
- **Análise** com pandas e teste de Mann-Whitney (SciPy) para comparar vitórias e derrotas sem assumir distribuição normal.
- **Modelo** de regressão logística com scikit-learn, com variáveis padronizadas. A variável `passes` foi removida por correlação de 0,886 com `posse`, o que distorcia os pesos.
- **Painel** em Streamlit com gráficos Plotly.

## Estrutura

```
coleta_partidas.py            partidas do Brasileirão 2024 a 2026
coleta_estatisticas_time.py   posse, chutes, xG, faltas e cartões de cada partida
coleta_jogadores.py           nota e minutos dos jogadores-chave (lista em config.py)
analise.py                    testes estatísticos de time e de jogador
treinar_modelo.py             regressão logística e ranking de fatores
painel.py                     painel interativo
data/processed/               dados já coletados, em Parquet
RELATORIO.md                  relatório com método, resultados e limitações
```

## Como rodar

Use Python 3.10 ou mais recente.

```bash
pip install -r requirements.txt

# O painel e as análises já funcionam com os dados em data/processed/
streamlit run painel.py
python analise.py
python treinar_modelo.py
```

Para coletar os dados de novo, rode nesta ordem (cada etapa usa o resultado da anterior):

```bash
python coleta_partidas.py
python coleta_estatisticas_time.py
python coleta_jogadores.py
```

## Limitações

A amostra de 102 jogos é razoável, mas alguns jogadores têm poucas partidas. A análise não separa mandante de visitante nem o adversário. Os dados vêm da API do Sofascore, então a coleta pode deixar de funcionar se o serviço mudar, e o uso dos dados deve respeitar os termos do Sofascore. Os detalhes estão no relatório.
