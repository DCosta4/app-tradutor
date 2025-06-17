import streamlit as st
import pandas as pd
import random
import os

# Carrega frases do Excel
@st.cache_data
def carregar_frases():
    df = pd.read_excel("frases.xlsx")
    df["PT"] = df["PT"].astype(str)
    df["EN"] = df["EN"].astype(str)
    return df

# Carrega ou cria histórico de desempenho
def carregar_desempenho(df):
    colunas_padrao = ["PT", "EN", "Acertos", "Erros", "Percentual"]

    if os.path.exists("desempenho.csv"):
        desempenho = pd.read_csv("desempenho.csv", sep=";", encoding="utf-8-sig")

        # Garante que todas as frases do Excel estejam no desempenho.csv
        desempenho_pt = set(desempenho["PT"])
        novas_frases = df[~df["PT"].isin(desempenho_pt)]

        if not novas_frases.empty:
            novas_linhas = pd.DataFrame({
                "PT": novas_frases["PT"],
                "EN": novas_frases["EN"],
                "Acertos": 0,
                "Erros": 0,
                "Percentual": 0.0
            })
            desempenho = pd.concat([desempenho, novas_linhas], ignore_index=True)

        # Garante que o desempenho tenha apenas as frases que ainda estão no Excel
        desempenho = desempenho[desempenho["PT"].isin(df["PT"])].reset_index(drop=True)

    else:
        desempenho = pd.DataFrame({
            "PT": df["PT"],
            "EN": df["EN"],
            "Acertos": [0]*len(df),
            "Erros": [0]*len(df),
            "Percentual": [0.0]*len(df)
        })

    # Garante que todas as colunas existam e estejam na ordem correta
    for coluna in colunas_padrao:
        if coluna not in desempenho.columns:
            desempenho[coluna] = 0 if coluna in ["Acertos", "Erros"] else 0.0

    desempenho = desempenho[colunas_padrao]
    return desempenho

# Salva desempenho
def salvar_desempenho(desempenho):
    desempenho["Total"] = desempenho["Acertos"] + desempenho["Erros"]
    desempenho["Percentual"] = desempenho["Acertos"] / desempenho["Total"]
    desempenho["Percentual"] = desempenho["Percentual"].fillna(0)
    desempenho.drop(columns=["Total"], inplace=True)
    desempenho.to_csv("desempenho.csv", sep=";", index=False, encoding="utf-8-sig")

# Seleciona uma nova frase baseada em erros (repetição espaçada simples)
def escolher_nova_frase(df, desempenho):
    acertos = desempenho["Acertos"] + 1
    erros = desempenho["Erros"] + 1
    pesos = erros / acertos
    pesos = pesos / pesos.sum()  # normaliza os pesos
    idx = random.choices(df.index, weights=pesos)[0]
    return idx

# Página principal
st.title("📘 Treinador de Tradução ")

df = carregar_frases()
desempenho = carregar_desempenho(df)

# Estado inicial
if "idx" not in st.session_state:
    st.session_state.idx = escolher_nova_frase(df, desempenho)
if "feedback" not in st.session_state:
    st.session_state.feedback = ""
if "ultima_frase" not in st.session_state:
    st.session_state.ultima_frase = ""

# Frase atual
idx = st.session_state.idx
frase_pt = df.loc[idx, "PT"]
frase_en = df.loc[idx, "EN"]

st.markdown(f"### Frase em Português:\n{frase_pt}")
resposta = st.text_input("Digite a tradução em inglês:")

# Botão verificar
if st.button("Verificar"):
    resposta_limpa = resposta.strip().lower()
    gabarito_limpo = frase_en.strip().lower()

    if resposta_limpa == gabarito_limpo:
        st.success("✅ Correto!")
        desempenho.loc[idx, "Acertos"] += 1
    else:
        st.error("❌ Incorreto.")
        st.markdown(f"**Resposta correta:** {frase_en}")
        desempenho.loc[idx, "Erros"] += 1

    salvar_desempenho(desempenho)
    st.session_state.feedback = "verificado"
    st.session_state.ultima_frase = frase_pt

# Botão próxima frase
if st.button("Próxima frase"):
    st.session_state.idx = escolher_nova_frase(df, desempenho)
    st.session_state.feedback = ""
    st.rerun()

# Mostrar histórico da última frase verificada
if st.session_state.feedback == "verificado":
    st.markdown(f"**Frase anterior:** {st.session_state.ultima_frase}")

with st.expander("📊 Ver desempenho completo"):
    desempenho_ordenado = desempenho.copy()
    desempenho_ordenado["Percentual"] = (desempenho_ordenado["Acertos"] / (desempenho_ordenado["Acertos"] + desempenho_ordenado["Erros"])).fillna(0)
    desempenho_ordenado["Percentual"] = (desempenho_ordenado["Percentual"] * 100).round(1).astype(str) + "%"
    st.dataframe(desempenho_ordenado[["PT", "EN", "Acertos", "Erros", "Percentual"]])


