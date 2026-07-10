# -*- coding: utf-8 -*-
"""Dashboard de alerta temprana de deserción por IES — "Datos al Ecosistema 2026".

Visualiza las predicciones de tasa de deserción para 2024 (t+1 y t+2) generadas por
el modelo XGBoost. Ejecutar:  streamlit run dashboard/app.py
(antes, generar los datos:    python dashboard/generar_predicciones.py)
"""
import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COLOR = {"Alto": "#d62728", "Medio": "#ff7f0e", "Bajo": "#2ca02c"}

st.set_page_config(page_title="Alerta de deserción IES — Datos al Ecosistema 2026",
                   page_icon="🎓", layout="wide")


@st.cache_data
def load_pred():
    df = pd.read_csv(os.path.join(HERE, "predicciones_2024.csv"))
    df["IES"] = df["IES"].astype(str)
    return df


@st.cache_data
def load_raw():
    df = pd.read_csv(os.path.join(ROOT, "df_forecast_raw.csv"))
    df["IES"] = df["IES"].astype(str)
    return df


pred = load_pred()

# ---------- Encabezado ----------
st.title("🎓 Alerta temprana de deserción por IES")
st.caption("Predicción de la tasa de deserción 2024 (t+1 y t+2) por Institución de "
           "Educación Superior · SNIES / MEN · *Datos al Ecosistema 2026*")

# ---------- Filtros ----------
with st.sidebar:
    st.header("Filtros")
    deptos = sorted(pred["DEPARTAMENTO"].dropna().unique())
    caracts = sorted(pred["CARACTER"].dropna().unique())
    niveles = ["Alto", "Medio", "Bajo"]
    f_dep = st.multiselect("Departamento", deptos)
    f_car = st.multiselect("Carácter institucional", caracts)
    f_niv = st.multiselect("Nivel de riesgo", niveles, default=niveles)
    solo_aumento = st.checkbox("Solo IES con tendencia al alza", value=False)
    st.markdown("---")
    st.caption("El nivel de riesgo se define por la tasa predicha de 2024-1: "
               "Bajo < 10% · Medio 10–20% · Alto ≥ 20%.")

df = pred.copy()
if f_dep:
    df = df[df["DEPARTAMENTO"].isin(f_dep)]
if f_car:
    df = df[df["CARACTER"].isin(f_car)]
if f_niv:
    df = df[df["nivel_riesgo"].isin(f_niv)]
if solo_aumento:
    df = df[df["en_aumento"]]

# ---------- KPIs ----------
c1, c2, c3, c4 = st.columns(4)
c1.metric("IES analizadas", f"{len(df)}")
c2.metric("En riesgo alto (≥20%)", int((df["nivel_riesgo"] == "Alto").sum()))
c3.metric("Con tendencia al alza", int(df["en_aumento"].sum()))
c4.metric("Tasa promedio predicha 2024-1", f"{df['pred_2024_1'].mean():.1f}%"
          if len(df) else "—")

st.markdown("---")
tab1, tab2, tab3 = st.tabs(["🚨 Ranking de riesgo", "🗺️ Por departamento", "🏫 Detalle por IES"])

# ---------- Tab 1: Ranking ----------
with tab1:
    st.subheader("IES priorizadas por riesgo de deserción (2024-1)")
    st.caption("Ordenadas por tasa de deserción predicha. La columna *tendencia* es "
               "la variación esperada frente al último semestre observado (2023-2).")
    rank = df.sort_values("pred_2024_1", ascending=False)[
        ["IES", "DEPARTAMENTO", "CARACTER", "tasa_2023_2", "pred_2024_1",
         "pred_2024_2", "tendencia", "nivel_riesgo"]
    ].rename(columns={"tasa_2023_2": "tasa 2023-2", "pred_2024_1": "pred 2024-1",
                      "pred_2024_2": "pred 2024-2", "nivel_riesgo": "riesgo"})
    st.dataframe(rank, use_container_width=True, hide_index=True, height=430)

    top = df.sort_values("pred_2024_1", ascending=False).head(20)
    if len(top):
        fig = px.bar(top, x="pred_2024_1", y="IES", orientation="h", color="nivel_riesgo",
                     color_discrete_map=COLOR, hover_data=["DEPARTAMENTO", "CARACTER"],
                     labels={"pred_2024_1": "Tasa predicha 2024-1 (%)", "IES": "IES"},
                     title="Top 20 IES de mayor riesgo")
        fig.update_layout(yaxis={"categoryorder": "total ascending"}, height=520,
                          legend_title="Riesgo")
        st.plotly_chart(fig, use_container_width=True)

# ---------- Tab 2: Por departamento ----------
with tab2:
    st.subheader("Riesgo agregado por departamento")
    if len(df):
        agg = (df.groupby("DEPARTAMENTO")
               .agg(tasa_predicha=("pred_2024_1", "mean"),
                    ies=("IES", "count"),
                    en_riesgo=("nivel_riesgo", lambda s: (s == "Alto").sum()))
               .reset_index().sort_values("tasa_predicha", ascending=False))
        agg["tasa_predicha"] = agg["tasa_predicha"].round(1)
        figd = px.bar(agg, x="tasa_predicha", y="DEPARTAMENTO", orientation="h",
                      color="tasa_predicha", color_continuous_scale="OrRd",
                      hover_data=["ies", "en_riesgo"],
                      labels={"tasa_predicha": "Tasa promedio predicha 2024-1 (%)",
                              "DEPARTAMENTO": "Departamento"},
                      title="Tasa promedio de deserción predicha por departamento")
        figd.update_layout(yaxis={"categoryorder": "total ascending"},
                           height=max(400, 22 * len(agg)))
        st.plotly_chart(figd, use_container_width=True)
        st.dataframe(agg.rename(columns={"tasa_predicha": "tasa predicha (%)",
                                         "ies": "# IES", "en_riesgo": "# riesgo alto"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("No hay IES con los filtros seleccionados.")

# ---------- Tab 3: Detalle por IES ----------
with tab3:
    st.subheader("Serie histórica y pronóstico por IES")
    opciones = df.sort_values("pred_2024_1", ascending=False)["IES"].tolist()
    if not opciones:
        st.info("No hay IES con los filtros seleccionados.")
    else:
        ies_sel = st.selectbox("Selecciona una IES (código SNIES)", opciones)
        raw = load_raw()
        serie = raw[raw["IES"] == ies_sel].sort_values("periodo")
        fila = df[df["IES"] == ies_sel].iloc[0]

        figs = go.Figure()
        figs.add_trace(go.Scatter(x=serie["periodo"], y=serie["tasa"].clip(0, 100),
                                  mode="lines+markers", name="Histórico (real)",
                                  line=dict(color="#1f77b4")))
        figs.add_trace(go.Scatter(
            x=["2024-1", "2024-2"], y=[fila["pred_2024_1"], fila["pred_2024_2"]],
            mode="lines+markers", name="Pronóstico",
            line=dict(color="#d62728", dash="dash")))
        # puntos reales 2024 si existen (para comparar)
        reales = [fila.get("real_2024_1"), fila.get("real_2024_2")]
        figs.add_trace(go.Scatter(x=["2024-1", "2024-2"], y=reales, mode="markers",
                                  name="Real 2024 (observado)",
                                  marker=dict(color="#2ca02c", size=9, symbol="x")))
        figs.update_layout(height=460, xaxis_title="Periodo",
                           yaxis_title="Tasa de deserción (%)",
                           title=f"IES {ies_sel} — {fila['DEPARTAMENTO']} · {fila['CARACTER']}")
        st.plotly_chart(figs, use_container_width=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Última real (2023-2)", f"{fila['tasa_2023_2']:.1f}%")
        m2.metric("Pred. 2024-1", f"{fila['pred_2024_1']:.1f}%",
                  delta=f"{fila['tendencia']:+.1f} pp")
        m3.metric("Pred. 2024-2", f"{fila['pred_2024_2']:.1f}%"
                  if pd.notna(fila["pred_2024_2"]) else "—")
        m4.metric("Nivel de riesgo", fila["nivel_riesgo"])

# ---------- Pie de página ----------
st.markdown("---")
st.caption(
    "⚠️ **Uso responsable.** El modelo es muy confiable para universidades (MAE ≈ 1.7 pp) "
    "y menos confiable para instituciones técnicas profesionales (MAE ≈ 21 pp); en esas "
    "IES las predicciones deben tomarse con cautela. Métricas honestas (selección por "
    "validación, test medido una sola vez): RMSE 2024-1 ≈ 11.2 · ranking Spearman 0.87. "
    "Las predicciones priorizan; no sustituyen el juicio de la secretaría de educación."
)
