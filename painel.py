import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import mannwhitneyu
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

st.set_page_config(page_title="São Paulo — Painel de derrotas", page_icon="⚽", layout="wide")

FUNDO = "#0d0d0b"
PAINEL = "#161613"
BORDA = "#2c2c27"
VERMELHO = "#e2312a"
BRANCO = "#f5f4f0"
CINZA = "#6f6f68"
FONTE = "IBM Plex Sans"

CORES_RESULTADO = {"V": BRANCO, "E": CINZA, "D": VERMELHO}
CONFIG_GRAFICO = {"displayModeBar": False}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'IBM Plex Sans', sans-serif; }}

.hero-title {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 700;
    font-size: 3.6rem;
    line-height: 1.0;
    margin-bottom: 0.15rem;
    color: {BRANCO};
}}
.hero-caption {{ color: {CINZA}; font-size: 1rem; }}

h2 {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600;
    font-size: 1.9rem;
    color: {BRANCO};
    border-top: 1px solid {BORDA};
    padding-top: 1.5rem;
    margin-top: 0.5rem;
}}
h3 {{
    font-family: 'Barlow Condensed', sans-serif;
    font-weight: 600;
    font-size: 1.7rem;
    color: {BRANCO};
    margin-bottom: 0.15rem;
}}
.chart-caption {{ color: {CINZA}; font-size: 0.88rem; margin-top: -0.1rem; margin-bottom: 0.7rem; }}

[data-testid="stMetric"] {{
    background: {PAINEL};
    border: 1px solid {BORDA};
    border-left: 4px solid {VERMELHO};
    padding: 1rem 1.2rem;
    border-radius: 3px;
}}
[data-testid="stMetricLabel"] {{ font-size: 0.85rem; color: {CINZA}; }}
[data-testid="stMetricValue"] {{ font-family: 'Barlow Condensed', sans-serif; font-weight: 700; color: {BRANCO}; }}

div[data-testid="stVerticalBlockBorderWrapper"] {{
    background: {PAINEL};
    border-color: {BORDA} !important;
    border-radius: 3px;
}}

[data-testid="stDataFrame"] div[role="gridcell"] {{ padding: 0.5rem 0.75rem !important; }}
[data-testid="stDataFrame"] div[role="columnheader"] {{ padding: 0.5rem 0.75rem !important; }}
</style>
""", unsafe_allow_html=True)


def base_layout(fig, altura=380, margem_esquerda=10):
    fig.update_layout(
        font_family=FONTE,
        font_color=BRANCO,
        plot_bgcolor=PAINEL,
        paper_bgcolor="rgba(0,0,0,0)",
        height=altura,
        margin=dict(l=margem_esquerda, r=40, t=20, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, title=None,
                    font=dict(size=13)),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, color=BRANCO, title_font=dict(size=13))
    fig.update_yaxes(showgrid=True, gridcolor=BORDA, zeroline=False, color=BRANCO, ticksuffix="   ")
    return fig


partidas = pd.read_parquet("data/processed/partidas.parquet")
estatisticas_time = pd.read_parquet("data/processed/estatisticas_time.parquet")
estatisticas_jogador = pd.read_parquet("data/processed/estatisticas_jogador.parquet")

completo_time = partidas.merge(estatisticas_time, on="match_id", how="inner")
completo_jogador = estatisticas_jogador.merge(
    partidas[["match_id", "resultado"]], on="match_id", how="inner"
)

vitorias_t = completo_time[completo_time["resultado"] == "V"]
derrotas_t = completo_time[completo_time["resultado"] == "D"]

colunas_metricas = ["posse", "chutes", "escanteios", "faltas", "cartoes_amarelos", "xg"]
NOMES_METRICA = {
    "posse": "Posse (%)", "chutes": "Finalizações", "escanteios": "Escanteios",
    "faltas": "Faltas", "cartoes_amarelos": "Cartões amarelos", "xg": "xG",
}

dados_modelo = completo_time[completo_time["resultado"].isin(["V", "D"])].dropna(subset=colunas_metricas)
X = StandardScaler().fit_transform(dados_modelo[colunas_metricas])
y = (dados_modelo["resultado"] == "V").astype(int)
modelo = LogisticRegression().fit(X, y)
acuracia = cross_val_score(LogisticRegression(), X, y, cv=5).mean()

# --- Cabeçalho ---
st.markdown('<p class="hero-title">Por que o São Paulo perde</p>', unsafe_allow_html=True)
st.markdown(
    f'<p class="hero-caption">Brasileirão 2024–2026 · {len(partidas)} partidas coletadas via Sofascore</p>',
    unsafe_allow_html=True,
)
st.write("")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Vitórias", int((partidas["resultado"] == "V").sum()))
col2.metric("Empates", int((partidas["resultado"] == "E").sum()))
col3.metric("Derrotas", int((partidas["resultado"] == "D").sum()))
col4.metric("Acurácia do modelo", f"{acuracia:.0%}")

st.write("")

# --- Conclusão em gráficos (calculados a partir dos dados) ---
posicoes_jogador = completo_jogador.groupby("jogador")["posicao"].agg(lambda s: s.mode().iloc[0])
medianas_pos = (
    completo_jogador[completo_jogador["resultado"].isin(["V", "D"])]
    .groupby(["jogador", "resultado"])["nota"].median().unstack()
)
medianas_pos = medianas_pos.join(posicoes_jogador.rename("posicao"))
NOME_POSICAO = {"D": "Zaga", "M": "Meio-campo", "F": "Ataque"}
nota_por_posicao = (
    medianas_pos[medianas_pos["posicao"] != "G"]
    .groupby("posicao")[["V", "D"]].mean()
    .rename(index=NOME_POSICAO)
)

col_a, col_b = st.columns(2)

with col_a:
    with st.container(border=True):
        st.markdown("### Diferença entre vitória e derrota, por métrica")
        st.markdown(
            '<p class="chart-caption">Variação percentual da mediana na derrota em relação à vitória.</p>',
            unsafe_allow_html=True,
        )

        variacao = pd.Series({
            NOMES_METRICA[c]: (derrotas_t[c].median() - vitorias_t[c].median()) / vitorias_t[c].median() * 100
            for c in colunas_metricas if vitorias_t[c].median() != 0
        }).sort_values()

        fig_variacao = go.Figure()
        fig_variacao.add_trace(go.Bar(
            x=variacao.values, y=variacao.index, orientation="h",
            marker_color=[VERMELHO if v > 0 else BRANCO for v in variacao.values],
            text=[f"{v:+.0f}%" for v in variacao.values],
            textposition="outside", textfont=dict(color=BRANCO), showlegend=False,
        ))
        fig_variacao.add_trace(go.Bar(x=[None], y=[None], marker_color=BRANCO, name="Maior na vitória"))
        fig_variacao.add_trace(go.Bar(x=[None], y=[None], marker_color=VERMELHO, name="Maior na derrota"))
        fig_variacao.add_vline(x=0, line_color=CINZA, line_width=1)
        fig_variacao.update_xaxes(title="variação na derrota vs. vitória")
        st.plotly_chart(base_layout(fig_variacao, altura=380, margem_esquerda=150),
                         use_container_width=True, config=CONFIG_GRAFICO)

with col_b:
    with st.container(border=True):
        st.markdown("### Nota por posição: vitória x derrota")
        st.markdown(
            '<p class="chart-caption">Média das notas medianas dos jogadores-chave de cada posição.</p>',
            unsafe_allow_html=True,
        )

        fig_posicao = go.Figure()
        fig_posicao.add_trace(go.Bar(
            x=nota_por_posicao.index, y=nota_por_posicao["V"], name="Vitória", marker_color=BRANCO,
            text=[f"{v:.2f}" for v in nota_por_posicao["V"]], textposition="outside",
        ))
        fig_posicao.add_trace(go.Bar(
            x=nota_por_posicao.index, y=nota_por_posicao["D"], name="Derrota", marker_color=VERMELHO,
            text=[f"{v:.2f}" for v in nota_por_posicao["D"]], textposition="outside",
        ))
        fig_posicao.update_layout(barmode="group")
        fig_posicao.update_yaxes(title="nota média", range=[6, 8])
        st.plotly_chart(base_layout(fig_posicao, altura=380), use_container_width=True, config=CONFIG_GRAFICO)

st.write("")

# --- Conclusão em texto (números calculados a partir dos gráficos acima) ---
diff_nota_posicao = nota_por_posicao["V"] - nota_por_posicao["D"]
posicao_maior_queda = diff_nota_posicao.idxmax()
posicao_menor_queda = diff_nota_posicao.idxmin()
metrica_maior_queda = variacao.idxmin()
metrica_sem_diferenca = variacao.abs().idxmin()

with st.container(border=True):
    st.markdown("### Conclusão")
    st.markdown(f"""
    <p style="font-size:1.02rem; line-height:1.7; color:{BRANCO};">
    O time tem <b style="color:{VERMELHO};">{variacao['Posse (%)']:+.0f}% mais posse</b> nas derrotas
    do que nas vitórias, mas essa posse não vira volume de jogo ofensivo:
    <b style="color:{VERMELHO};">finalizações caem {variacao['Finalizações']:.0f}%</b> e a
    <b style="color:{VERMELHO};">criação de chances de qualidade (xG) despenca {variacao['xG']:.0f}%</b>.
    O problema não é perder a bola, é <b>não converter posse em chute e em chance real</b>.
    Faltas ({variacao['Faltas']:+.0f}%) e cartões amarelos ({variacao['Cartões amarelos']:+.0f}%)
    praticamente não mudam, então também não é uma questão de indisciplina.<br><br>
    Essa queda de produção não fica isolada num setor: a nota cai mais na
    <b style="color:{VERMELHO};">{posicao_maior_queda}</b> ({diff_nota_posicao[posicao_maior_queda]:+.2f})
    do que no <b>{posicao_menor_queda}</b> ({diff_nota_posicao[posicao_menor_queda]:+.2f}), sinal de que o
    time como um todo perde eficiência quando joga na base da posse, não só o setor ofensivo.
    </p>
    """, unsafe_allow_html=True)

st.write("")
st.markdown("## Aprofundando nos dados")
st.write("")

# --- Estatísticas de time ---
with st.container(border=True):
    st.markdown("### Estatísticas de time por resultado")
    st.markdown(
        '<p class="chart-caption">A altura da barra é o valor típico (mediana). Escolha a métrica abaixo.</p>',
        unsafe_allow_html=True,
    )
    metrica_escolhida = st.selectbox(
        "Métrica", colunas_metricas, format_func=lambda m: NOMES_METRICA[m], label_visibility="collapsed"
    )

    resumo = completo_time.groupby("resultado")[metrica_escolhida].median().reindex(["V", "E", "D"])
    categorias = ["Vitória", "Empate", "Derrota"]
    cores_ordem = [CORES_RESULTADO[r] for r in ["V", "E", "D"]]

    fig_barra = go.Figure()
    for categoria, valor, cor in zip(categorias, resumo.values, cores_ordem):
        fig_barra.add_trace(go.Scatter(
            x=[0, valor], y=[categoria, categoria], mode="lines",
            line=dict(color=cor, width=8), showlegend=False, hoverinfo="skip",
        ))
        fig_barra.add_trace(go.Scatter(
            x=[valor], y=[categoria], mode="markers+text",
            marker=dict(color=cor, size=18, line=dict(color=FUNDO, width=1)),
            text=[f"{valor:.1f}"], textposition="middle right", textfont=dict(color=BRANCO, size=14),
            showlegend=False, hoverinfo="skip",
        ))

    fig_barra.update_xaxes(title=NOMES_METRICA[metrica_escolhida], range=[0, resumo.values.max() * 1.3])
    fig_barra.update_yaxes(automargin=True)
    st.plotly_chart(base_layout(fig_barra, altura=340, margem_esquerda=100), use_container_width=True, config=CONFIG_GRAFICO)

st.write("")
col_esq, col_dir = st.columns([1.15, 1])

# --- Significância ---
with col_esq:
    with st.container(border=True):
        st.markdown("### O que é estatisticamente confiável")
        st.markdown(
            '<p class="chart-caption">Teste de Mann-Whitney, vitória x derrota.</p>',
            unsafe_allow_html=True,
        )

        linhas_teste = []
        for coluna in colunas_metricas:
            if vitorias_t[coluna].nunique() <= 1 or derrotas_t[coluna].nunique() <= 1:
                continue
            _, p_valor = mannwhitneyu(vitorias_t[coluna], derrotas_t[coluna], method="asymptotic")
            linhas_teste.append({
                "Métrica": NOMES_METRICA[coluna],
                "Mediana V": round(vitorias_t[coluna].median(), 2),
                "Mediana D": round(derrotas_t[coluna].median(), 2),
                "p-valor": round(p_valor, 4) if pd.notna(p_valor) else None,
                "Confiável": "Sim" if pd.notna(p_valor) and p_valor < 0.05 else "Não",
            })

        tabela = pd.DataFrame(linhas_teste).sort_values("p-valor")
        st.dataframe(
            tabela, use_container_width=True, hide_index=True,
            column_config={"p-valor": st.column_config.NumberColumn(format="%.4f")},
        )

# --- Peso no modelo ---
with col_dir:
    with st.container(border=True):
        st.markdown("### Peso de cada estatística no modelo")
        st.markdown(
            '<p class="chart-caption">Regressão logística · entradas padronizadas.</p>',
            unsafe_allow_html=True,
        )

        coeficientes = pd.DataFrame({
            "métrica": [NOMES_METRICA[c] for c in colunas_metricas],
            "peso": modelo.coef_[0],
        }).sort_values("peso")

        fig_modelo = go.Figure()
        fig_modelo.add_trace(go.Bar(
            x=coeficientes["peso"], y=coeficientes["métrica"], orientation="h",
            marker_color=[BRANCO if p > 0 else VERMELHO for p in coeficientes["peso"]],
            text=[f"{p:+.2f}" for p in coeficientes["peso"]],
            textposition="outside", textfont=dict(color=BRANCO), showlegend=False,
        ))
        fig_modelo.add_trace(go.Bar(x=[None], y=[None], marker_color=BRANCO, name="Favorece vitória"))
        fig_modelo.add_trace(go.Bar(x=[None], y=[None], marker_color=VERMELHO, name="Favorece derrota"))
        fig_modelo.add_vline(x=0, line_color=CINZA, line_width=1)
        fig_modelo.update_xaxes(title="peso padronizado", range=[-0.75, 1.55])
        fig_modelo.update_layout(bargap=0.5)
        fig_modelo.update_traces(width=0.55, selector=dict(type="bar"))
        st.plotly_chart(base_layout(fig_modelo, altura=460, margem_esquerda=150), use_container_width=True, config=CONFIG_GRAFICO)

st.write("")

# --- Jogadores-chave: dumbbell chart ---
with st.container(border=True):
    st.markdown("### Nota dos jogadores-chave")
    st.markdown(
        '<p class="chart-caption">Cada linha liga a nota mediana em derrotas (vermelho) à nota em '
        'vitórias (branco). Quanto maior a linha, maior a queda de rendimento.</p>',
        unsafe_allow_html=True,
    )

    medianas_jogador = (
        completo_jogador[completo_jogador["resultado"].isin(["V", "D"])]
        .groupby(["jogador", "resultado"])["nota"].median()
        .unstack()
    )
    medianas_jogador["queda"] = medianas_jogador["V"] - medianas_jogador["D"]
    medianas_jogador = medianas_jogador.sort_values("queda", ascending=True)

    fig_dumbbell = go.Figure()

    for jogador, linha in medianas_jogador.iterrows():
        fig_dumbbell.add_trace(go.Scatter(
            x=[linha["D"], linha["V"]], y=[jogador, jogador],
            mode="lines", line=dict(color=CINZA, width=2), showlegend=False, hoverinfo="skip",
        ))

    fig_dumbbell.add_trace(go.Scatter(
        x=medianas_jogador["D"], y=medianas_jogador.index, mode="markers", name="Derrota",
        marker=dict(color=VERMELHO, size=14, line=dict(color=FUNDO, width=1)),
    ))
    fig_dumbbell.add_trace(go.Scatter(
        x=medianas_jogador["V"], y=medianas_jogador.index, mode="markers", name="Vitória",
        marker=dict(color=BRANCO, size=14, line=dict(color=FUNDO, width=1)),
    ))

    fig_dumbbell.update_xaxes(title="nota mediana", range=[6, 8])
    st.plotly_chart(base_layout(fig_dumbbell, altura=440, margem_esquerda=160), use_container_width=True, config=CONFIG_GRAFICO)