import pandas as pd


def dias_con_datos(df):
    if df.empty:
        return []
    por_dia = df.groupby("fecha")["Uso_pago"].sum()
    return por_dia[por_dia > 0].index.tolist()


def promedio_por_hora(df):
    if df.empty:
        return pd.Series(dtype="float64")
    dias = len(dias_con_datos(df))
    if dias == 0:
        return pd.Series(dtype="float64")
    return df.groupby("hora")["Uso_pago"].sum() / dias


def serie_dia_por_hora(df, fecha):
    sub = df[df["fecha"] == pd.Timestamp(fecha).normalize()]
    if sub.empty:
        return pd.Series(dtype="float64")
    return sub.groupby("hora")["Uso_pago"].sum()
