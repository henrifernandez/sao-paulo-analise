import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

partidas = pd.read_parquet("data/processed/partidas.parquet")
estatisticas_time = pd.read_parquet("data/processed/estatisticas_time.parquet")
completo = partidas.merge(estatisticas_time, on="match_id", how="inner")

colunas_entrada = ["posse", "chutes", "escanteios", "faltas", "cartoes_amarelos", "xg"]
dados = completo[completo["resultado"].isin(["V", "D"])].dropna(subset=colunas_entrada)

X = dados[colunas_entrada]
y = (dados["resultado"] == "V").astype(int)

escalador = StandardScaler()
X_escalado = escalador.fit_transform(X)

modelo = LogisticRegression()
modelo.fit(X_escalado, y)

coeficientes = pd.DataFrame({
    "metrica": colunas_entrada,
    "peso": modelo.coef_[0],
})
coeficientes["peso_absoluto"] = coeficientes["peso"].abs()
coeficientes = coeficientes.sort_values("peso_absoluto", ascending=False)

print(coeficientes)

escores = cross_val_score(LogisticRegression(), X_escalado, y, cv=5)
print(f"\nAcurácia média (validação cruzada, 5 divisões): {escores.mean():.2%} (+/- {escores.std():.2%})")

print("\nCorrelação com xG:")
print(dados[colunas_entrada].corr()["xg"].sort_values(ascending=False))