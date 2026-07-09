import uuid

import pandas as pd
import streamlit as st

from database.connection import get_connection


COLUNAS_CRONOGRAMA = [
    "ID", "ObraID", "Obra", "Etapa", "Duracao", "Dependencia",
    "Inicio", "Fim", "Progresso", "Status", "Ordem",
]


def calcular_cronograma(df):
    """Calcula datas respeitando ordem, inicio informado e dependencias."""
    if df is None or df.empty:
        return pd.DataFrame(columns=COLUNAS_CRONOGRAMA + ["Folga", "Critico"])

    resultado = df.copy()
    resultado["Duracao"] = pd.to_numeric(resultado["Duracao"], errors="coerce").fillna(1).clip(lower=1)
    resultado["Inicio"] = pd.to_datetime(resultado.get("Inicio"), errors="coerce")
    resultado["Fim"] = pd.to_datetime(resultado.get("Fim"), errors="coerce")
    resultado["Ordem"] = pd.to_numeric(resultado.get("Ordem"), errors="coerce")
    resultado = resultado.sort_values(["Ordem", "Etapa"], na_position="last").reset_index(drop=True)

    hoje = pd.Timestamp.today().normalize()
    datas_fim = {}

    for _ in range(max(len(resultado), 1)):
        alterou = False
        for indice, row in resultado.iterrows():
            inicio_informado = row["Inicio"] if pd.notna(row["Inicio"]) else hoje
            dependencia = row.get("Dependencia")
            fim_dependencia = datas_fim.get(str(dependencia)) if pd.notna(dependencia) else None
            inicio = fim_dependencia if fim_dependencia is not None else inicio_informado
            fim = inicio + pd.Timedelta(days=int(row["Duracao"]))

            if resultado.at[indice, "Inicio"] != inicio or resultado.at[indice, "Fim"] != fim:
                resultado.at[indice, "Inicio"] = inicio
                resultado.at[indice, "Fim"] = fim
                alterou = True
            datas_fim[str(row["Etapa"])] = fim
        if not alterou:
            break

    return resultado


def caminho_critico(df):
    if df is None or df.empty:
        return df.copy()

    resultado = df.copy()
    resultado["Fim"] = pd.to_datetime(resultado["Fim"], errors="coerce")
    max_fim = resultado["Fim"].max()
    resultado["Folga"] = resultado["Fim"].apply(
        lambda fim: (max_fim - fim).days if pd.notna(fim) and pd.notna(max_fim) else 0
    )
    resultado["Critico"] = resultado["Folga"] == 0
    return resultado


def aplicar_status(df):
    if df is None or df.empty:
        return df.copy()

    resultado = df.copy()
    hoje = pd.Timestamp.today().normalize()
    resultado["Inicio"] = pd.to_datetime(resultado["Inicio"], errors="coerce")
    resultado["Fim"] = pd.to_datetime(resultado["Fim"], errors="coerce")
    resultado["Progresso"] = pd.to_numeric(resultado.get("Progresso"), errors="coerce").fillna(0).clip(0, 100)

    def status(row):
        if row["Progresso"] >= 100:
            return "Concluida"
        if pd.notna(row["Fim"]) and hoje > row["Fim"]:
            return "Atrasada"
        if row["Progresso"] > 0 or (pd.notna(row["Inicio"]) and hoje >= row["Inicio"]):
            return "Em andamento"
        return "Nao iniciada"

    resultado["Status"] = resultado.apply(status, axis=1)
    return resultado


def processar_cronograma(df):
    return aplicar_status(caminho_critico(calcular_cronograma(df)))


def carregar_cronograma(obra_id=None, obra=None):
    conn = get_connection()
    condicoes = []
    parametros = []

    if obra_id:
        condicoes.append("ObraID = ?")
        parametros.append(str(obra_id))
    if obra:
        condicoes.append("(Obra = ? AND (ObraID IS NULL OR ObraID = ''))")
        parametros.append(str(obra))

    if not condicoes:
        conn.close()
        return pd.DataFrame(columns=COLUNAS_CRONOGRAMA)

    query = f"""
        SELECT {", ".join(COLUNAS_CRONOGRAMA)}
        FROM cronograma
        WHERE {" OR ".join(condicoes)}
        ORDER BY COALESCE(Ordem, 999999), Etapa
    """
    df = pd.read_sql_query(query, conn, params=parametros)
    conn.close()
    return processar_cronograma(df) if not df.empty else df


def salvar_etapa(dados):
    registro = {coluna: dados.get(coluna) for coluna in COLUNAS_CRONOGRAMA}
    registro["ID"] = registro["ID"] or str(uuid.uuid4())
    registro["Duracao"] = max(1, int(registro["Duracao"] or 1))
    registro["Progresso"] = min(100.0, max(0.0, float(registro["Progresso"] or 0)))
    registro["Ordem"] = int(registro["Ordem"] or 1)

    conn = get_connection()
    existe = conn.execute(
        "SELECT Etapa, ObraID, Obra FROM cronograma WHERE ID = ?",
        (registro["ID"],),
    ).fetchone()
    if existe:
        etapa_anterior = existe["Etapa"]
        conn.execute("""
            UPDATE cronograma SET
                ObraID = ?, Obra = ?, Etapa = ?, Duracao = ?, Dependencia = ?,
                Inicio = ?, Fim = ?, Progresso = ?, Status = ?, Ordem = ?
            WHERE ID = ?
        """, (
            registro["ObraID"], registro["Obra"], registro["Etapa"], registro["Duracao"],
            registro["Dependencia"], registro["Inicio"], registro["Fim"], registro["Progresso"],
            registro["Status"], registro["Ordem"], registro["ID"],
        ))
        if etapa_anterior != registro["Etapa"]:
            conn.execute("""
                UPDATE cronograma
                SET Dependencia = ?
                WHERE Dependencia = ?
                  AND (
                    (ObraID = ? AND ? IS NOT NULL)
                    OR (Obra = ? AND (ObraID IS NULL OR ObraID = ''))
                  )
            """, (
                registro["Etapa"], etapa_anterior,
                registro["ObraID"], registro["ObraID"], registro["Obra"],
            ))
    else:
        conn.execute("""
            INSERT INTO cronograma
                (ID, ObraID, Obra, Etapa, Duracao, Dependencia, Inicio, Fim, Progresso, Status, Ordem)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, tuple(registro[coluna] for coluna in COLUNAS_CRONOGRAMA))
    conn.commit()
    st.cache_data.clear()
    conn.close()
    return registro["ID"]


def excluir_etapa(etapa_id):
    conn = get_connection()
    etapa = conn.execute(
        "SELECT Etapa, ObraID, Obra FROM cronograma WHERE ID = ?",
        (etapa_id,),
    ).fetchone()
    if etapa:
        conn.execute("""
            UPDATE cronograma
            SET Dependencia = NULL
            WHERE Dependencia = ?
              AND (
                (ObraID = ? AND ? IS NOT NULL)
                OR (Obra = ? AND (ObraID IS NULL OR ObraID = ''))
              )
        """, (
            etapa["Etapa"], etapa["ObraID"], etapa["ObraID"], etapa["Obra"],
        ))
    conn.execute("DELETE FROM cronograma WHERE ID = ?", (etapa_id,))
    conn.commit()
    st.cache_data.clear()
    conn.close()


def sincronizar_calculos(obra_id=None, obra=None):
    df = carregar_cronograma(obra_id, obra)
    if df.empty:
        return df

    conn = get_connection()
    for _, row in df.iterrows():
        conn.execute("""
            UPDATE cronograma
            SET ObraID = COALESCE(NULLIF(ObraID, ''), ?), Inicio = ?, Fim = ?, Status = ?
            WHERE ID = ?
        """, (
            str(obra_id) if obra_id else None,
            row["Inicio"].strftime("%Y-%m-%d") if pd.notna(row["Inicio"]) else None,
            row["Fim"].strftime("%Y-%m-%d") if pd.notna(row["Fim"]) else None,
            row["Status"],
            row["ID"],
        ))
    conn.commit()
    st.cache_data.clear()
    conn.close()
    return df


def resumo_cronograma(obra_id=None, obra=None):
    df = carregar_cronograma(obra_id, obra)
    if df.empty:
        return {
            "execucao": 0.0,
            "atrasadas": 0,
            "proxima_etapa": "Nenhuma etapa cadastrada",
            "termino": None,
        }

    progresso = pd.to_numeric(df["Progresso"], errors="coerce").fillna(0)
    duracao = pd.to_numeric(df["Duracao"], errors="coerce").fillna(1).clip(lower=1)
    execucao = float((progresso * duracao).sum() / duracao.sum())
    pendentes = df[df["Progresso"] < 100].sort_values(["Inicio", "Ordem"], na_position="last")
    proxima = pendentes.iloc[0]["Etapa"] if not pendentes.empty else "Cronograma concluido"
    fim = pd.to_datetime(df["Fim"], errors="coerce").max()

    return {
        "execucao": execucao,
        "atrasadas": int((df["Status"] == "Atrasada").sum()),
        "proxima_etapa": proxima,
        "termino": fim,
    }


def atualizar_progresso_etapa(obra_id, obra, etapa, progresso):
    progresso = min(100.0, max(0.0, float(progresso)))
    conn = get_connection()
    registro = conn.execute("""
        SELECT ID
        FROM cronograma
        WHERE Etapa = ?
          AND (
            ObraID = ?
            OR (Obra = ? AND (ObraID IS NULL OR ObraID = ''))
          )
        ORDER BY COALESCE(Ordem, 999999)
        LIMIT 1
    """, (str(etapa), str(obra_id), str(obra))).fetchone()
    if not registro:
        conn.close()
        return False

    conn.execute(
        "UPDATE cronograma SET Progresso = ? WHERE ID = ?",
        (progresso, registro["ID"]),
    )
    conn.commit()
    st.cache_data.clear()
    conn.close()

    atual = carregar_cronograma(obra_id, obra)
    linha = atual[atual["ID"] == registro["ID"]]
    if not linha.empty:
        conn = get_connection()
        conn.execute(
            "UPDATE cronograma SET Status = ? WHERE ID = ?",
            (linha.iloc[0]["Status"], registro["ID"]),
        )
        conn.commit()
        st.cache_data.clear()
        conn.close()
    return True
