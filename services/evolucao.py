from datetime import datetime
from io import BytesIO
from pathlib import Path
import uuid

import pandas as pd
import streamlit as st
from PIL import Image, UnidentifiedImageError

from database.connection import BASE_DIR, get_connection


EXTENSOES_PERMITIDAS = {".jpg", ".jpeg", ".png"}
TAMANHO_MAXIMO = 10 * 1024 * 1024
PASTA_EVOLUCAO = BASE_DIR / "uploads" / "evolucao"


def _pasta_obra(obra_id):
    identificador = str(obra_id or "").strip()
    if not identificador or identificador in {".", ".."}:
        raise ValueError("Obra inválida para armazenamento de fotos.")

    pasta = (PASTA_EVOLUCAO / identificador).resolve()
    raiz = PASTA_EVOLUCAO.resolve()
    if pasta.parent != raiz:
        raise ValueError("Identificador de obra inválido.")
    pasta.mkdir(parents=True, exist_ok=True)
    return pasta


def caminho_absoluto(caminho_relativo):
    if not caminho_relativo:
        return None
    caminho = (BASE_DIR / str(caminho_relativo)).resolve()
    raiz = PASTA_EVOLUCAO.resolve()
    if caminho != raiz and raiz not in caminho.parents:
        return None
    return caminho if caminho.exists() else None


def _validar_imagem(upload):
    extensao = Path(upload.name).suffix.lower()
    if extensao not in EXTENSOES_PERMITIDAS:
        raise ValueError(f"{upload.name}: extensão não permitida.")

    dados = upload.getvalue()
    if not dados:
        raise ValueError(f"{upload.name}: arquivo vazio.")
    if len(dados) > TAMANHO_MAXIMO:
        raise ValueError(f"{upload.name}: excede o limite de 10 MB.")

    try:
        with Image.open(BytesIO(dados)) as imagem:
            imagem.verify()
        with Image.open(BytesIO(dados)) as imagem:
            formato = imagem.format
            imagem.load()
            copia = imagem.copy()
    except (UnidentifiedImageError, OSError) as erro:
        raise ValueError(f"{upload.name}: imagem inválida.") from erro

    if formato not in {"JPEG", "PNG"}:
        raise ValueError(f"{upload.name}: formato de imagem não permitido.")
    return dados, copia, extensao


def _salvar_arquivo_e_miniatura(upload, obra_id):
    dados, imagem, extensao = _validar_imagem(upload)
    pasta = _pasta_obra(obra_id)
    identificador = uuid.uuid4().hex
    arquivo = pasta / f"{identificador}{extensao}"
    miniatura = pasta / f"{identificador}_thumb.jpg"

    arquivo.write_bytes(dados)
    imagem.thumbnail((640, 420))
    if imagem.mode not in ("RGB", "L"):
        fundo = Image.new("RGB", imagem.size, "white")
        if "A" in imagem.getbands():
            fundo.paste(imagem, mask=imagem.getchannel("A"))
        else:
            fundo.paste(imagem)
        imagem = fundo
    imagem.convert("RGB").save(miniatura, "JPEG", quality=82, optimize=True)

    return (
        arquivo.relative_to(BASE_DIR).as_posix(),
        miniatura.relative_to(BASE_DIR).as_posix(),
    )


def salvar_evolucao(
    obra_id, obra, etapa, data, titulo, descricao, responsavel, fotos,
    origem=None, diario_id=None,
):
    if not fotos:
        return False, "Selecione pelo menos uma foto."

    criado_em = datetime.now().isoformat(timespec="microseconds")
    registros = []
    arquivos_criados = []

    try:
        for foto in fotos:
            arquivo, miniatura = _salvar_arquivo_e_miniatura(foto, obra_id)
            arquivos_criados.extend([arquivo, miniatura])
            registros.append((
                str(uuid.uuid4()),
                str(obra_id),
                str(obra),
                str(etapa),
                pd.Timestamp(data).date().isoformat(),
                str(titulo).strip(),
                str(descricao).strip(),
                str(responsavel).strip(),
                arquivo,
                miniatura,
                criado_em,
                origem,
                diario_id,
            ))

        conn = get_connection()
        conn.executemany("""
            INSERT INTO evolucao_obra (
                ID, ObraID, Obra, Etapa, Data, Titulo, Descricao,
                Responsavel, Arquivo, Miniatura, CriadoEm
                , Origem, DiarioID
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, registros)
        conn.commit()
        st.cache_data.clear()
        conn.close()
        return True, None
    except Exception as erro:
        for caminho in arquivos_criados:
            absoluto = caminho_absoluto(caminho)
            if absoluto:
                absoluto.unlink(missing_ok=True)
        return False, str(erro)


def carregar_evolucoes(obra_id, etapa=None, data_inicio=None, data_fim=None, responsavel=None):
    conn = get_connection()
    condicoes = ["ObraID = ?"]
    parametros = [str(obra_id)]

    if etapa and etapa != "Todas":
        condicoes.append("Etapa = ?")
        parametros.append(str(etapa))
    if data_inicio:
        condicoes.append("date(Data) >= date(?)")
        parametros.append(pd.Timestamp(data_inicio).date().isoformat())
    if data_fim:
        condicoes.append("date(Data) <= date(?)")
        parametros.append(pd.Timestamp(data_fim).date().isoformat())
    if responsavel and responsavel != "Todos":
        condicoes.append("Responsavel = ?")
        parametros.append(str(responsavel))

    df = pd.read_sql_query(
        f"""
        SELECT *
        FROM evolucao_obra
        WHERE {" AND ".join(condicoes)}
        ORDER BY date(Data) DESC, CriadoEm DESC
        """,
        conn,
        params=parametros,
    )
    conn.close()
    return df


def excluir_registro_evolucao(obra_id, criado_em):
    conn = get_connection()
    registros = conn.execute("""
        SELECT ID, Arquivo, Miniatura
        FROM evolucao_obra
        WHERE ObraID = ? AND CriadoEm = ?
    """, (str(obra_id), str(criado_em))).fetchall()

    conn.execute(
        "DELETE FROM evolucao_obra WHERE ObraID = ? AND CriadoEm = ?",
        (str(obra_id), str(criado_em)),
    )
    conn.commit()
    st.cache_data.clear()
    conn.close()

    for registro in registros:
        for campo in ("Arquivo", "Miniatura"):
            caminho = caminho_absoluto(registro[campo])
            if caminho:
                caminho.unlink(missing_ok=True)
    return len(registros)


def excluir_evolucao_por_diario(obra_id, diario_id):
    conn = get_connection()
    grupos = conn.execute("""
        SELECT DISTINCT CriadoEm
        FROM evolucao_obra
        WHERE ObraID = ? AND DiarioID = ?
    """, (str(obra_id), str(diario_id))).fetchall()
    conn.close()
    return sum(
        excluir_registro_evolucao(obra_id, grupo["CriadoEm"])
        for grupo in grupos
    )


def contar_fotos_diario(diario_id):
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) FROM evolucao_obra WHERE DiarioID = ?",
        (str(diario_id),),
    ).fetchone()[0]
    conn.close()
    return int(total)


def contagem_fotos_por_etapa(obra_id):
    conn = get_connection()
    linhas = conn.execute("""
        SELECT Etapa, COUNT(*) AS Quantidade
        FROM evolucao_obra
        WHERE ObraID = ?
        GROUP BY Etapa
    """, (str(obra_id),)).fetchall()
    conn.close()
    return {linha["Etapa"]: int(linha["Quantidade"]) for linha in linhas}


def ultima_evolucao(obra_id):
    conn = get_connection()
    linha = conn.execute("""
        SELECT Data, Etapa, Titulo, CriadoEm, COUNT(*) AS Quantidade
        FROM evolucao_obra
        WHERE ObraID = ?
        GROUP BY Data, Etapa, Titulo, CriadoEm
        ORDER BY date(Data) DESC, CriadoEm DESC
        LIMIT 1
    """, (str(obra_id),)).fetchone()
    conn.close()
    return dict(linha) if linha else None
