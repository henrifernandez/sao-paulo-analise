# Análise das derrotas do São Paulo FC (Brasileirão, 2024-2026)

## Objetivo

Investigar possíveis causas das derrotas do São Paulo no Brasileirão, comparando
estatísticas de time e de jogadores-chave entre partidas vencidas e perdidas.

## Dados

- **Fonte**: API pública do Sofascore (time São Paulo, id 1981)
- **Recorte**: Brasileirão Série A, temporadas 2024, 2025 e 2026
- **Amostra**: 102 partidas (40 vitórias, 39 derrotas, 23 empates)
- **Jogadores-chave acompanhados**: Rafael, Robert Arboleda, Rafael Tolói, Alan
  Franco, Marcos Antônio, Luciano, Lucas Moura e Jonathan Calleri

## Estatísticas de time: vitórias x derrotas

| Métrica | Mediana vitórias | Mediana derrotas | p-valor | Significativo |
|---|---|---|---|---|
| xG (gols esperados) | 1.52 | 0.69 | 0.0000 | Sim |
| Chutes | 13.5 | 11.0 | 0.0107 | Sim |
| Posse de bola | 52.5% | 59.0% | 0.0366 | Sim |
| Escanteios | 5.0 | 5.0 | 0.4801 | Não |
| Faltas | 13.5 | 13.0 | 0.6653 | Não |
| Cartões amarelos | 2.0 | 2.0 | — | Não testável* |

\* Cartões amarelos tem poucos valores distintos possíveis (majoritariamente 0 a
4), o que gera empates demais na amostra para o teste de Mann-Whitney calcular
uma variância válida. Como a diferença de médias já era pequena (2.37 x 2.51),
não há indício de que essa métrica distinga vitórias de derrotas.

**Nota sobre `passes`**: a métrica foi removida da análise (tabelas, modelo e
painel) por ter correlação de 0.886 com `posse` — as duas capturam
essencialmente a mesma informação, e mantê-las juntas distorcia o peso
individual de cada uma no modelo (posse aparecia com peso negativo, passes com
peso positivo, um efeito de colinearidade, não um achado real).

**Padrão identificado — "posse estéril"**: nas derrotas, o São Paulo tem mais
posse de bola que nas vitórias, mas cria bem menos chances de gol
de qualidade (xG quase o dobro nas vitórias). Ou seja, o time segura mais a bola
quando perde, sem transformar isso em chances reais, um padrão típico de time
que gira a posse sem profundidade ou que esbarra num bloco defensivo baixo do
adversário.

## Estatísticas de jogador-chave: nota em vitórias x derrotas

| Jogador | Posição | Mediana V | Mediana D | p-valor | Significativo |
|---|---|---|---|---|---|
| Rafael Tolói | Zagueiro | 7.50 | 6.80 | 0.0127 | Sim |
| Luciano | Atacante | 7.50 | 6.90 | 0.0016 | Sim |
| Robert Arboleda | Zagueiro | 7.30 | 6.90 | 0.0038 | Sim |
| Jonathan Calleri | Atacante | 7.10 | 6.50 | 0.0091 | Sim |
| Rafael | Goleiro | 7.00 | 6.85 | 0.0652 | Limítrofe |
| Marcos Antônio | Meio-campo | 7.00 | 6.80 | 0.3524 | Não |
| Lucas Moura | Meio-campo | 7.15 | 6.80 | 0.2157 | Não |
| Alan Franco | Zagueiro | — | — | — | Amostra insuficiente (6 jogos) |

**Padrão identificado**: a queda de rendimento nas derrotas não fica isolada no
ataque. Os dois zagueiros titulares (Arboleda e Tolói) caem de nota tanto quanto
os dois principais finalizadores (Luciano e Calleri), enquanto o meio-campo mais
criativo (Lucas Moura e Marcos Antônio) mantém nível estável entre vitórias e
derrotas.

## Modelo (regressão logística) como ranking de fatores

Além dos testes estatísticos por métrica, foi treinado um modelo de regressão
logística (vitória x derrota, empates excluídos) usando as estatísticas de
time como entrada, com o objetivo de obter um ranking combinado de quais
fatores mais "pesam" na diferença entre vencer e perder, não de prever
resultados futuros com precisão.

| Métrica | Peso (padronizado) |
|---|---|
| xG | 1.23 |
| Posse | -0.37 |
| Escanteios | 0.16 |
| Chutes | 0.15 |
| Faltas | -0.10 |
| Cartões amarelos | -0.02 |

- **Acurácia (validação cruzada, 5 divisões)**: 75.3% (+/- 13.0%), contra uma
  base de referência de ~50.6% (acertar sempre a classe majoritária). Melhorou
  em relação à versão com `passes` incluída (73.9% +/- 15.3%), reforçando que
  a variável era ruído redundante, não sinal útil
- **xG e chutes são correlacionados entre si** (correlação de 0.56), o que é
  esperado (mais chutes tende a gerar mais xG). Isso explica por que o peso de
  chutes é discreto: boa parte do efeito de "finalizar mais" já é capturado
  pelo peso alto do xG
- **`passes` foi removida do modelo** por correlação de 0.886 com `posse`
  (quase a mesma informação medida duas vezes). Com as duas juntas, o modelo
  distorcia o peso individual de cada uma (posse negativa, passes positiva),
  um artefato de colinearidade, não um efeito real de "passar mais ajuda a
  vencer"

O modelo confirma, de forma combinada, os mesmos fatores já identificados
individualmente pelos testes estatísticos: xG domina, posse pesa na direção
contraintuitiva (mais posse associada a menos vitória, reforçando o padrão de
"posse estéril"), e chutes contribui de forma mais discreta por sua
sobreposição com o xG.

## Conclusão

As derrotas do São Paulo no período analisado não parecem estar associadas a
indisciplina (faltas e cartões não diferem) nem a perda de controle de jogo (o
time tem, na verdade, mais posse nas derrotas). O padrão mais
consistente é de **menor qualidade de criação ofensiva** (xG e chutes bem
abaixo) combinado com **queda de rendimento simultânea da zaga titular e dos
finalizadores**, enquanto o meio-campo de construção mantém o nível. Isso
sugere um problema mais tático que disciplinar: o time parece ficar exposto
defensivamente ao mesmo tempo que o ataque fica isolado, mesmo com a
articulação do meio de campo preservada.

## Limitações

- Amostra de 102 jogos ao longo de 3 temporadas é razoável, mas alguns
  jogadores-chave (como Alan Franco) têm poucos jogos disputados no período,
  limitando a confiabilidade do teste pra eles
- A análise não separa mandante/visitante nem adversário, dois fatores que
  provavelmente também influenciam o resultado
- Cartões amarelos não pôde ser testado estatisticamente pela baixa variância
  dos dados

## Próximos passos possíveis

- Separar a análise por mandante x visitante
- Analisar se a queda é mais forte contra adversários específicos (rivais
  diretos x times de menor orçamento)
- Incluir dados de xG concedido (xGA) para checar se a queda defensiva também
  aparece nesse indicador, além da nota dos zagueiros
- Ampliar a lista de jogadores-chave incluindo quem assumiu a vaga do Alan
  Franco no período em que ele não jogou