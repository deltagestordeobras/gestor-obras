import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata

from services.insumos import carregar_insumos
from services.orcamento import calcular_obra
from services.orcamento_engine import (
    MAPA_ETAPAS,
    PRECOS_MATERIAIS_COMPLEMENTARES,
    corrigir_mojibake,
    gerar_orcamento_completo,
)
from services.modelagem_arquitetonica import gerar_quantitativos_arquitetonicos
from services.previsto_real import gerar_comparativo_por_dimensao


def _normalizar_nome_orcamento(valor):
    texto = corrigir_mojibake(valor)
    texto = texto.replace("m?", "m2").replace("mm?", "mm2")
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = "".join(ch.lower() if ch.isalnum() else " " for ch in texto)
    return " ".join(texto.split())


def _materiais_com_preco_cadastrado(tabela_materiais):
    if tabela_materiais is None or tabela_materiais.empty:
        return set()

    coluna_material = None
    for coluna in tabela_materiais.columns:
        if _normalizar_nome_orcamento(coluna) == "material":
            coluna_material = coluna
            break

    if not coluna_material:
        return set()

    return {
        _normalizar_nome_orcamento(material)
        for material in tabela_materiais[coluna_material].dropna()
        if str(material).strip()
    }


def _detectar_materiais_fallback(materiais_custos, tabela_materiais):
    if materiais_custos is None or materiais_custos.empty:
        return []

    cadastrados = _materiais_com_preco_cadastrado(tabela_materiais)
    fallback = []

    for _, row in materiais_custos.iterrows():
        material = row.get("Material", "")
        chave = _normalizar_nome_orcamento(material)
        if (
            chave in PRECOS_MATERIAIS_COMPLEMENTARES
            and chave not in cadastrados
            and material not in fallback
        ):
            fallback.append(str(material))

    return fallback


def _exibir_resultado_orcamento_tecnico(render):
    col_resultado, col_limpar = st.columns([4, 1])
    with col_resultado:
        st.success("Orçamento técnico carregado da última geração.")
    with col_limpar:
        if st.button("Limpar resultado", key="limpar_orcamento_tecnico", use_container_width=True):
            st.session_state.pop("orcamento_tecnico_resultado", None)
            st.session_state.pop("orcamento_tecnico_render", None)
            st.rerun()

    materiais_fallback = render.get("materiais_fallback", [])
    if materiais_fallback:
        st.warning(
            f"⚠️ {len(materiais_fallback)} material(ais) sem preço cadastrado usaram "
            f"estimativas: {', '.join(materiais_fallback[:5])}. "
            "Cadastre os preços em Configurações para maior precisão."
        )

    comparativo_etapas = render.get("comparativo_etapas", pd.DataFrame())
    if comparativo_etapas is not None and not comparativo_etapas.empty:
        st.divider()
        st.subheader("Orçamento vs Real por Etapa")
        for _, row in comparativo_etapas.iterrows():
            etapa = row.get("Etapa", "")
            orcado = row.get("Previsto", 0)
            real = row.get("Real", 0)
            diferenca = row.get("Desvio", 0)
            percentual = row.get("% Execução", 0)
            col1, col2, col3, col4 = st.columns(4)
            col1.write(f"Etapa: {etapa}")
            col2.write(f"Orçado: R$ {orcado:,.2f}")
            col3.write(f"Real: R$ {real:,.2f}")
            col4.write(f"{percentual:.1f}%")
            if orcado == 0 and real > 0:
                st.warning(f"{etapa} não estava no orçamento!")
            elif real > orcado:
                st.error(f"{etapa} estourou em R$ {diferenca:,.2f}")
            elif percentual > 80:
                st.warning(f"{etapa} já consumiu {percentual:.1f}%")
            else:
                st.success(f"{etapa} dentro do planejado")
            st.divider()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Mão de obra", f"R$ {render.get('custo_mao_obra', 0):,.0f}")
    c2.metric("Material", f"R$ {render.get('custo_material', 0):,.0f}")
    c3.metric("Total", f"R$ {render.get('custo_total', 0):,.0f}")
    c4.metric("R$/m²", f"R$ {render.get('custo_m2', 0):,.0f}")

    st.dataframe(
        pd.DataFrame(
            render.get("lista_mat", []),
            columns=["Material", "Qtd", "Preço", "Total"],
        ),
        use_container_width=True,
        height=300,
    )

    custos_etapas = render.get("custos_etapas", {})
    if custos_etapas:
        st.divider()
        st.subheader("Orçamento por Etapa")
        for etapa, valor in custos_etapas.items():
            st.metric(f"{etapa}", f"R$ {valor:,.2f}")


def tela_orcamento(obra):
    orcamento_salvo = st.session_state.get("ultimo_orcamento")
    modo_orcamento = st.session_state.get("orcamento_modo")
    orcamento_da_obra = (
        isinstance(orcamento_salvo, dict)
        and str(orcamento_salvo.get("obra", "")) == str(obra)
    )

    if modo_orcamento == "visualizar" and orcamento_da_obra:
        st.title("Orçamento da Obra")
        c1, c2, c3 = st.columns(3)
        c1.metric("Custo total", f"R$ {orcamento_salvo.get('custo_total', 0):,.2f}")
        c2.metric("Custo/m²", f"R$ {orcamento_salvo.get('custo_m2', 0):,.2f}")
        c3.metric("Venda sugerida", f"R$ {orcamento_salvo.get('venda', 0):,.2f}")

        st.subheader("Materiais")
        st.dataframe(orcamento_salvo.get("materiais", pd.DataFrame()), width="stretch")
        st.subheader("Mão de obra")
        st.dataframe(orcamento_salvo.get("mao_obra", pd.DataFrame()), width="stretch")

        if st.button("Editar orçamento", type="primary"):
            st.session_state["orcamento_modo"] = "editar"
            st.rerun()
        return

    st.title("📐 Orçamento Técnico da Obra")

    aba_estimativa, aba_tecnico, aba_calcular_obra = st.tabs(
        ["📊 Orçamento por Estimativa", "📐 Orçamento Técnico (Projeto)", "Orçamento Completo"]
    )

    with aba_estimativa:
        st.subheader("1️⃣ Dados gerais da obra")

        col1, col2, col3 = st.columns(3)

        with col1:
            tipo_obra = st.selectbox("Tipo de obra", ["Casa", "Sobrado", "Apartamento"])
            area_total = st.number_input(
                "Área construída (m²)", min_value=30.0, step=10.0
            )

        with col2:
            pavimentos = st.selectbox("Número de pavimentos", [1, 2, 3])
            sistema = st.selectbox("Sistema construtivo", ["Alvenaria", "Steel Frame"])

        with col3:
            fundacao = st.selectbox("Tipo de fundação", ["Sapata", "Tubulão", "Radier"])
            laje = st.selectbox("Tipo de laje", ["Treliçada", "Maciça"])

        st.divider()
        st.subheader("2️⃣ Ambientes da casa")

        colA, colB, colC = st.columns(3)

        with colA:
            quartos = st.number_input("Quartos", 0, 10, 2)
            banheiros = st.number_input("Banheiros", 0, 10, 2)

        with colB:
            salas = st.number_input("Salas", 0, 5, 1)
            cozinhas = st.number_input("Cozinhas", 0, 3, 1)

        with colC:
            area_gourmet = st.number_input("Área gourmet", 0, 2, 0)
            lavanderia = st.number_input("Lavanderia", 0, 2, 1)

        st.divider()
        st.subheader("3️⃣ Tipo de acabamento")

        colD, colF = st.columns(2)

        with colD:
            piso = st.selectbox("Tipo de piso", ["Cerâmico", "Porcelanato", "Vinílico"])

        with colF:
            revestimento = st.selectbox("Revestimento", ["Cerâmico", "Porcelanato"])

        st.divider()
        st.subheader("⚙️ Parâmetros da estimativa")

        if "parametros_estimativa" not in st.session_state:
            st.session_state.parametros_estimativa = pd.DataFrame(
                {
                    "Item": [
                        "Base m²",
                        "Fundação Sapata",
                        "Fundação Tubulão",
                        "Fundação Radier",
                        "Laje Treliçada",
                        "Laje Maciça",
                        "Piso Cerâmico",
                        "Piso Porcelanato",
                        "Piso Vinílico",
                        "Revest Cerâmico",
                        "Revest Porcelanato",
                        "Casa",
                        "Sobrado",
                        "Apartamento",
                    ],
                    "Valor": [
                        1200,
                        120,
                        200,
                        150,
                        180,
                        300,
                        120,
                        220,
                        180,
                        100,
                        180,
                        0,
                        150,
                        -100,
                    ],
                }
            )

        edited = st.data_editor(
            st.session_state.parametros_estimativa, use_container_width=True
        )
        st.session_state.parametros_estimativa = edited

        def get_param(nome):
            df = st.session_state.parametros_estimativa
            linha = df[df["Item"] == nome]

            if not linha.empty:
                return float(linha.iloc[0]["Valor"])
            return 0

        st.divider()

        if st.button("📊 Gerar estimativa"):
            area = area_total
            custo_m2 = get_param("Base m²")
            custo_m2 += get_param(tipo_obra)
            custo_m2 += get_param(f"Fundação {fundacao}")
            custo_m2 += get_param(f"Laje {laje}")
            custo_m2 += get_param(f"Piso {piso}")
            custo_m2 += get_param(f"Revest {revestimento}")

            custo_total = area * custo_m2
            custo_mao_obra = custo_total * 0.42
            custo_material = custo_total * 0.58

            st.success("Estimativa inteligente gerada")
            c1, c2, c3 = st.columns(3)
            c1.metric("Material", f"R$ {custo_material:,.2f}")
            c2.metric("Mão de obra", f"R$ {custo_mao_obra:,.2f}")
            c3.metric("Custo total", f"R$ {custo_total:,.2f}")
            st.metric("💰 Custo por m²", f"R$ {custo_m2:,.2f}")

    with aba_tecnico:
        mapa_etapas = MAPA_ETAPAS

        st.markdown("""
        <style>
        [data-testid="stNumberInput"] {
            background-color: #0f172a;
            border-radius: 8px;
            padding: 6px;
        }
        </style>
        """, unsafe_allow_html=True)

        st.markdown("## Orçamento Técnico do Projeto")

        render = st.session_state.get("orcamento_tecnico_render")
        if render:
            _exibir_resultado_orcamento_tecnico(render)

        tecnico_bloqueado = False

        if "tabela_mao_obra" not in st.session_state:
            st.warning(
                "Cadastre a mão de obra na aba Configurações antes de continuar."
            )
            df_mao = pd.DataFrame(columns=["Serviço", "Preco", "Preço"])
            tecnico_bloqueado = True
        else:
            df_mao = st.session_state.tabela_mao_obra

        if "tabela_composicao" not in st.session_state:
            st.session_state.tabela_composicao = pd.DataFrame()

        if "tabela_materiais" not in st.session_state:
            st.warning("Cadastre os materiais primeiro.")
            st.session_state.tabela_materiais = pd.DataFrame()
            tecnico_bloqueado = True

        area_cobertura = 0.0

        col_main, col_side = st.columns([4, 1])

        with col_main:
            with st.expander("1. Implantação", expanded=True):
                st.subheader("🏗️ Dados da Obra")

                c1, c2 = st.columns(2)

                with c1:
                    tipo_obra = st.selectbox(
                        "Tipo", ["Casa", "Sobrado", "Apartamento", "Galpão"]
                    )

                with c2:
                    area_total = st.number_input("Área construída (m²)", value=150.0)

                c3, c4 = st.columns(2)

                with c3:
                    area_lote = st.number_input(
                        "Área do lote (m²)",
                        min_value=0.0,
                        value=300.0,
                        key="implantacao_area_lote"
                    )
                    perimetro_externo = st.number_input(
                        "Perímetro externo (m)",
                        min_value=0.0,
                        value=50.0,
                        key="implantacao_perimetro_externo"
                    )

                with c4:
                    area_permeavel = st.number_input(
                        "Área permeável (m²)",
                        min_value=0.0,
                        value=90.0,
                        key="implantacao_area_permeavel"
                    )
                    numero_pavimentos = st.number_input(
                        "Número de pavimentos",
                        min_value=1,
                        value=1,
                        step=1,
                        key="implantacao_numero_pavimentos"
                    )

            quantidades_servicos = {}

            with st.expander("📊 Quantidades de Serviços", expanded=True):
                servicos = [
                    row["Serviço"]
                    for _, row in df_mao.iterrows()
                    if row["Serviço"]
                    not in ["Concreto", "Forma Pilares e Vigas", "Furo Fundação"]
                ]

                cols = st.columns(4)

                for i, servico in enumerate(servicos):
                    with cols[i % 4]:
                        with st.container():
                            st.markdown(f"**{servico}**")

                            qtd = st.number_input(
                                "Quantidade",
                                min_value=0.0,
                                value=0.0,
                                key=f"qtd_{servico}",
                                label_visibility="collapsed"
                            )

                        quantidades_servicos[servico] = qtd

            with st.expander("2. Estrutura"):
                usar_quantitativos_projeto_estrutural = st.checkbox(
                    "Utilizar quantitativos do projeto estrutural",
                    value=False,
                    key="estrutura_usar_quantitativos_projeto"
                )

                if usar_quantitativos_projeto_estrutural:
                    c1, c2, c3, c4 = st.columns(4)

                    with c1:
                        projeto_volume_concreto = st.number_input(
                            "Volume concreto (m³)",
                            min_value=0.0,
                            value=0.0,
                            key="estrutura_projeto_volume_concreto"
                        )

                    with c2:
                        projeto_aco_ca50 = st.number_input(
                            "Aço CA50 (kg)",
                            min_value=0.0,
                            value=0.0,
                            key="estrutura_projeto_aco_ca50"
                        )

                    with c3:
                        projeto_aco_ca60 = st.number_input(
                            "Aço CA60 (kg)",
                            min_value=0.0,
                            value=0.0,
                            key="estrutura_projeto_aco_ca60"
                        )

                    with c4:
                        projeto_area_forma = st.number_input(
                            "Área forma (m²)",
                            min_value=0.0,
                            value=0.0,
                            key="estrutura_projeto_area_forma"
                        )

                    pe_direito_estrutura = 2.8
                    area_piso = area_total
                    espessura = 0.0
                    comprimento_viga = 0.0
                    qtd_pilares = 0
                    secao_viga_largura = 0.0
                    secao_viga_altura = 0.0
                    altura_media_pilares = pe_direito_estrutura
                    area_laje = 0.0
                    tipo_fundacao = "sapata"
                    secao_pilar_largura = 0.0
                    secao_pilar_altura = 0.0
                    volume_estimado_concreto = 0.0
                    qtd_tubulao = 0
                    diametro = 0.0
                    profundidade = 0.0
                    comprimento_pilar = 0.0
                else:
                    projeto_volume_concreto = 0.0
                    projeto_aco_ca50 = 0.0
                    projeto_aco_ca60 = 0.0
                    projeto_area_forma = 0.0

                    c1, c2, c3, c4 = st.columns(4)

                    with c1:
                        pe_direito_estrutura = st.number_input(
                            "Pé-direito (m)",
                            min_value=0.0,
                            value=2.8,
                            key="estrutura_pe_direito"
                        )
                        area_piso = st.number_input("Área (m²)", 0.0, key="piso_area")
                        espessura = st.number_input("Espessura (cm)", 10.0, key="piso_esp")

                    with c2:
                        comprimento_viga = st.number_input(
                            "Comprimento total de vigas (m)", 0.0, key="viga_comp"
                        )
                        qtd_pilares = st.number_input(
                            "Quantidade de pilares",
                            min_value=0,
                            value=0,
                            step=1,
                            key="estrutura_qtd_pilares"
                        )
                        secao_viga_largura = st.number_input(
                            "Largura (cm)", 0.0, key="viga_largura"
                        )
                        secao_viga_altura = st.number_input(
                            "Altura (cm)", 0.0, key="viga_altura"
                        )

                    with c3:
                        altura_media_pilares = st.number_input(
                            "Altura média dos pilares (m)",
                            min_value=0.0,
                            value=pe_direito_estrutura,
                            key="estrutura_altura_media_pilares"
                        )
                        area_laje = st.number_input(
                            "Área de laje (m²)",
                            min_value=0.0,
                            value=area_total,
                            key="estrutura_area_laje"
                        )
                        tipo_fundacao = st.selectbox(
                            "Tipo de fundação",
                            ["sapata", "radier", "tubulão", "bloco"],
                            key="estrutura_tipo_fundacao"
                        )
                        secao_pilar_largura = st.number_input(
                            "Largura (cm)", 0.0, key="pilar_largura"
                        )
                        secao_pilar_altura = st.number_input(
                            "Altura (cm)", 0.0, key="pilar_altura"
                        )

                    with c4:
                        volume_estimado_concreto = st.number_input(
                            "Volume estimado concreto (opcional)",
                            min_value=0.0,
                            value=0.0,
                            key="estrutura_volume_estimado_concreto"
                        )
                        qtd_tubulao = st.number_input("Tubulões", 0, key="fund_qtd")
                        diametro = st.number_input("Diâmetro (cm)", 0.0, key="fund_diam")
                        profundidade = st.number_input(
                            "Profundidade (m)", 0.0, key="fund_prof"
                        )

                    comprimento_pilar = qtd_pilares * altura_media_pilares

            ambientes_arquitetonicos = []

            with st.container(border=True):
                st.markdown("### 3. Arquitetura")

                if "ambientes_orcamento" not in st.session_state:
                    st.session_state["ambientes_orcamento"] = []

                if st.button("+ Adicionar ambiente", key="adicionar_ambiente_orcamento"):
                    st.session_state["ambientes_orcamento"].append({})
                    st.rerun()

                for i, ambiente in enumerate(st.session_state["ambientes_orcamento"]):
                    with st.expander(
                        ambiente.get("nome") or f"Ambiente {i + 1}",
                        expanded=True,
                    ):
                        col_titulo, col_remover = st.columns([4, 1])
                        with col_titulo:
                            st.markdown(f"#### Ambiente {i + 1}")
                        with col_remover:
                            if st.button("Remover", key=f"remover_ambiente_orcamento_{i}"):
                                st.session_state["ambientes_orcamento"].pop(i)
                                st.rerun()

                        c1, c2, c3 = st.columns(3)

                        with c1:
                            nome_ambiente = st.text_input(
                                "Nome",
                                value=ambiente.get("nome") or f"Ambiente {i + 1}",
                                key=f"arq_nome_{i}"
                            )
                            tipos_ambiente = [
                                "Sala",
                                "Quarto",
                                "Cozinha",
                                "Banheiro",
                                "Lavanderia",
                                "Área Gourmet",
                                "Garagem",
                                "Área externa",
                                "Outro",
                            ]
                            tipo_atual = ambiente.get("tipo") or "Sala"
                            tipo_ambiente = st.selectbox(
                                "Tipo",
                                tipos_ambiente,
                                index=tipos_ambiente.index(tipo_atual) if tipo_atual in tipos_ambiente else 0,
                                key=f"arq_tipo_{i}"
                            )
                            area_piso_ambiente = st.number_input(
                                "Área piso (m²)",
                                min_value=0.0,
                                value=float(ambiente.get("area_piso") or 0.0),
                                key=f"arq_area_piso_{i}"
                            )

                        with c2:
                            perimetro_ambiente = st.number_input(
                                "Perímetro (m)",
                                min_value=0.0,
                                value=float(ambiente.get("perimetro") or 0.0),
                                key=f"arq_perimetro_{i}"
                            )
                            pe_direito_ambiente = st.number_input(
                                "Pé-direito (m)",
                                min_value=0.0,
                                value=float(ambiente.get("pe_direito") or 2.8),
                                key=f"arq_pe_direito_{i}"
                            )
                            tipos_piso = ["Piso Porcelanato", "Piso Cerâmico"]
                            tipo_piso_atual = ambiente.get("tipo_piso") or "Piso Porcelanato"
                            tipo_piso_ambiente = st.selectbox(
                                "Tipo piso",
                                tipos_piso,
                                index=tipos_piso.index(tipo_piso_atual) if tipo_piso_atual in tipos_piso else 0,
                                key=f"arq_tipo_piso_{i}"
                            )

                        with c3:
                            altura_revestimento = st.number_input(
                                "Altura revestimento (m)",
                                min_value=0.0,
                                value=float(ambiente.get("altura_revestimento") or 0.0),
                                key=f"arq_altura_revestimento_{i}"
                            )
                            possui_pintura = st.checkbox(
                                "Possui pintura",
                                value=bool(ambiente.get("possui_pintura", True)),
                                key=f"arq_possui_pintura_{i}"
                            )
                            area_azulejada = st.number_input(
                                "Área azulejada (m²)",
                                min_value=0.0,
                                value=float(ambiente.get("area_azulejada") or 0.0),
                                key=f"arq_area_azulejada_{i}"
                            )
                            percentual_perdas = st.number_input(
                                "Percentual perdas",
                                min_value=0.0,
                                value=float(ambiente.get("percentual_perdas") or 0.0),
                                key=f"arq_percentual_perdas_{i}"
                            )

                        ambiente_atualizado = {
                            "nome": nome_ambiente,
                            "tipo": tipo_ambiente,
                            "area_piso": area_piso_ambiente,
                            "perimetro": perimetro_ambiente,
                            "pe_direito": pe_direito_ambiente,
                            "tipo_piso": tipo_piso_ambiente,
                            "altura_revestimento": altura_revestimento,
                            "possui_pintura": possui_pintura,
                            "area_azulejada": area_azulejada,
                            "percentual_perdas": percentual_perdas,
                        }
                        st.session_state["ambientes_orcamento"][i] = ambiente_atualizado
                        ambientes_arquitetonicos.append(ambiente_atualizado)

                qtd_ambientes = len(ambientes_arquitetonicos)

                comprimento_paredes_internas = st.number_input(
                    "Comprimento total paredes internas (m)",
                    min_value=0.0,
                    value=0.0,
                    key="arquitetura_comprimento_paredes_internas"
                )

            with st.expander("4. Esquadrias"):
                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    qtd_portas_internas = st.number_input(
                        "Quantidade portas internas",
                        min_value=0,
                        value=0,
                        step=1,
                        key="esquadrias_portas_internas"
                    )

                with c2:
                    qtd_portas_externas = st.number_input(
                        "Quantidade portas externas",
                        min_value=0,
                        value=0,
                        step=1,
                        key="esquadrias_portas_externas"
                    )

                with c3:
                    area_total_janelas = st.number_input(
                        "Área total janelas (m²)",
                        min_value=0.0,
                        value=0.0,
                        key="esquadrias_area_janelas"
                    )

                with c4:
                    area_total_vidro = st.number_input(
                        "Área total vidro (m²)",
                        min_value=0.0,
                        value=area_total_janelas,
                        key="esquadrias_area_vidro"
                    )

            with st.expander("5. Instalações"):
                st.markdown("**Elétrica**")
                c1, c2, c3, c4 = st.columns(4)

                with c1:
                    pontos_iluminacao = st.number_input(
                        "Pontos iluminação",
                        min_value=0,
                        value=max(1, int(area_total / 12)),
                        step=1,
                        key="instalacoes_pontos_iluminacao"
                    )

                with c2:
                    tomadas = st.number_input(
                        "Tomadas",
                        min_value=0,
                        value=max(1, int(area_total / 6)),
                        step=1,
                        key="instalacoes_tomadas"
                    )

                with c3:
                    interruptores = st.number_input(
                        "Interruptores",
                        min_value=0,
                        value=max(1, int(area_total / 15)),
                        step=1,
                        key="instalacoes_interruptores"
                    )

                with c4:
                    circuitos_especiais = st.number_input(
                        "Circuitos especiais",
                        min_value=0,
                        value=2,
                        step=1,
                        key="instalacoes_circuitos_especiais"
                    )

                st.markdown("**Hidráulica**")
                c5, c6, c7, c8, c9 = st.columns(5)

                with c5:
                    pontos_agua_fria = st.number_input(
                        "Pontos água fria",
                        min_value=0,
                        value=8,
                        step=1,
                        key="instalacoes_pontos_agua_fria"
                    )

                with c6:
                    pontos_esgoto = st.number_input(
                        "Pontos esgoto",
                        min_value=0,
                        value=6,
                        step=1,
                        key="instalacoes_pontos_esgoto"
                    )

                with c7:
                    banheiros = st.number_input(
                        "Banheiros",
                        min_value=0,
                        value=2,
                        step=1,
                        key="instalacoes_banheiros"
                    )

                with c8:
                    cozinha = st.number_input(
                        "Cozinha",
                        min_value=0,
                        value=1,
                        step=1,
                        key="instalacoes_cozinha"
                    )

                with c9:
                    area_servico = st.number_input(
                        "Área serviço",
                        min_value=0,
                        value=1,
                        step=1,
                        key="instalacoes_area_servico"
                    )

            with st.expander("6. Acabamento"):
                c1, c2, c3 = st.columns(3)

                with c1:
                    padrao_construtivo = st.selectbox(
                        "Padrão construtivo",
                        ["econômico", "médio", "alto padrão"],
                        index=1,
                        key="acabamento_padrao_construtivo"
                    )
                    area_pintura_interna = st.number_input(
                        "Área pintura interna",
                        min_value=0.0,
                        value=area_total * 2.5,
                        key="acabamento_area_pintura_interna"
                    )

                with c2:
                    area_pintura_externa = st.number_input(
                        "Área pintura externa",
                        min_value=0.0,
                        value=perimetro_externo * pe_direito_estrutura,
                        key="acabamento_area_pintura_externa"
                    )
                    area_revestimento_parede = st.number_input(
                        "Área revestimento parede",
                        min_value=0.0,
                        value=0.0,
                        key="acabamento_area_revestimento_parede"
                    )

                with c3:
                    area_impermeabilizacao = st.number_input(
                        "Área impermeabilização",
                        min_value=0.0,
                        value=max(0.0, area_total * 0.12),
                        key="acabamento_area_impermeabilizacao"
                    )
                    tipo_cobertura = st.selectbox(
                        "Tipo cobertura",
                        ["Cerâmica", "Metálica Simples", "Telha Sanduíche"]
                    )
                    area_cobertura = st.number_input(
                        "Área cobertura (m²)",
                        min_value=0.0,
                        value=area_total,
                        key="acabamento_area_cobertura"
                    )

                st.markdown("**Louças e metais**")
                c4, c5, c6, c7, c8 = st.columns(5)

                with c4:
                    vasos_sanitarios = st.number_input(
                        "Vasos sanitários",
                        min_value=0,
                        value=banheiros,
                        step=1,
                        key="loucas_vasos_sanitarios"
                    )

                with c5:
                    cubas = st.number_input(
                        "Cubas",
                        min_value=0,
                        value=banheiros + cozinha,
                        step=1,
                        key="loucas_cubas"
                    )

                with c6:
                    torneiras = st.number_input(
                        "Torneiras",
                        min_value=0,
                        value=banheiros + cozinha + area_servico,
                        step=1,
                        key="loucas_torneiras"
                    )

                with c7:
                    chuveiros = st.number_input(
                        "Chuveiros",
                        min_value=0,
                        value=banheiros,
                        step=1,
                        key="loucas_chuveiros"
                    )

                with c8:
                    tanques = st.number_input(
                        "Tanques",
                        min_value=0,
                        value=area_servico,
                        step=1,
                        key="loucas_tanques"
                    )

            gerar = st.button("🚀 Gerar Orçamento", use_container_width=True)

            if gerar and area_total > 0:
                quantitativos_estruturais_vazios = (
                    usar_quantitativos_projeto_estrutural
                    and projeto_volume_concreto <= 0
                    and projeto_aco_ca50 <= 0
                    and projeto_aco_ca60 <= 0
                    and projeto_area_forma <= 0
                )

                if tecnico_bloqueado:
                    st.error("Não é possível gerar o orçamento técnico sem as tabelas obrigatórias.")
                elif quantitativos_estruturais_vazios:
                    st.warning("Quantitativos estruturais não carregados.")
                else:
                    projeto_arquitetonico = {
                        "obra": {
                            "nome": obra,
                            "tipo": tipo_obra,
                            "area_total": area_total,
                        },
                        "ambientes": ambientes_arquitetonicos,
                    }

                    resultado_arquitetonico = gerar_quantitativos_arquitetonicos(
                        projeto_arquitetonico
                    )

                    quantidades_engine = quantidades_servicos.copy()

                    for servico, quantidade in resultado_arquitetonico["quantitativos"].items():
                        quantidades_engine[servico] = (
                            quantidades_engine.get(servico, 0) + quantidade
                        )

                    incluir_piso_porcelanato = (
                        area_piso > 0
                        and quantidades_engine.get("Piso Porcelanato", 0) == 0
                        and quantidades_engine.get("Piso Cerâmico", 0) == 0
                    )

                    dados_obra = {
                        "area_total": area_total,
                        "implantacao": {
                            "area_construida": area_total,
                            "area_lote": area_lote,
                            "perimetro_externo": perimetro_externo,
                            "area_permeavel": area_permeavel,
                            "numero_pavimentos": numero_pavimentos,
                        },
                        "estrutura": {
                            "pe_direito": pe_direito_estrutura,
                            "comprimento_total_vigas": comprimento_viga,
                            "quantidade_pilares": qtd_pilares,
                            "altura_media_pilares": altura_media_pilares,
                            "area_laje": area_laje,
                            "tipo_fundacao": tipo_fundacao,
                            "volume_estimado_concreto": volume_estimado_concreto,
                            "usar_quantitativos_projeto": usar_quantitativos_projeto_estrutural,
                            "projeto_volume_concreto_m3": projeto_volume_concreto,
                            "projeto_aco_ca50_kg": projeto_aco_ca50,
                            "projeto_aco_ca60_kg": projeto_aco_ca60,
                            "projeto_area_forma_m2": projeto_area_forma,
                        },
                        "arquitetura": {
                            "quantidade_ambientes": qtd_ambientes,
                            "ambientes": ambientes_arquitetonicos,
                            "comprimento_paredes_internas": comprimento_paredes_internas,
                        },
                        "esquadrias": {
                            "portas_internas": qtd_portas_internas,
                            "portas_externas": qtd_portas_externas,
                            "area_total_janelas": area_total_janelas,
                            "area_total_vidro": area_total_vidro,
                        },
                        "instalacoes": {
                            "eletrica": {
                                "pontos_iluminacao": pontos_iluminacao,
                                "tomadas": tomadas,
                                "interruptores": interruptores,
                                "circuitos_especiais": circuitos_especiais,
                            },
                            "hidraulica": {
                                "pontos_agua_fria": pontos_agua_fria,
                                "pontos_esgoto": pontos_esgoto,
                                "banheiros": banheiros,
                                "cozinha": cozinha,
                                "area_servico": area_servico,
                            },
                        },
                        "acabamento": {
                            "padrao_construtivo": padrao_construtivo,
                            "area_pintura_interna": area_pintura_interna,
                            "area_pintura_externa": area_pintura_externa,
                            "area_revestimento_parede": area_revestimento_parede,
                            "area_impermeabilizacao": area_impermeabilizacao,
                        },
                        "loucas_metais": {
                            "vasos_sanitarios": vasos_sanitarios,
                            "cubas": cubas,
                            "torneiras": torneiras,
                            "chuveiros": chuveiros,
                            "tanques": tanques,
                        },
                        "quantidades_servicos": quantidades_engine,
                        "area_piso": area_piso,
                        "espessura_piso_cm": espessura,
                        "comprimento_viga": comprimento_viga,
                        "largura_viga_cm": secao_viga_largura,
                        "altura_viga_cm": secao_viga_altura,
                        "comprimento_pilar": comprimento_pilar,
                        "largura_pilar_cm": secao_pilar_largura,
                        "altura_pilar_cm": secao_pilar_altura,
                        "quantidade_tubuloes": qtd_tubulao,
                        "diametro_tubulao_cm": diametro,
                        "profundidade_tubulao_m": profundidade,
                        "area_cobertura": area_cobertura,
                        "tipo_cobertura": tipo_cobertura,
                        "incluir_piso_porcelanato": incluir_piso_porcelanato,
                        "tabela_mao_obra": st.session_state.tabela_mao_obra,
                        "tabela_composicao": st.session_state.get("tabela_composicao", pd.DataFrame()),
                        "tabela_materiais": st.session_state.tabela_materiais,
                            "mapa_etapas": MAPA_ETAPAS,
                        "aplicar_perdas": False,
                    }

                    with st.spinner("Gerando orçamento técnico..."):
                        orcamento = gerar_orcamento_completo(dados_obra)
                    resumo = orcamento["resumo"]

                    quantidades_servicos = orcamento["quantitativos"]
                    custo_mao_obra = resumo["custo_mao_obra"]
                    custo_material = resumo["custo_material"]
                    custo_total = resumo["custo_total"]
                    custo_m2 = resumo["custo_m2"]

                    materiais_custos = orcamento.get("materiais_custos")

                    if materiais_custos is None or materiais_custos.empty:
                        materiais_custos = orcamento.get("materiais_agrupados")

                    materiais_fallback = _detectar_materiais_fallback(
                        materiais_custos,
                        st.session_state.tabela_materiais,
                    )

                    lista_mat = []

                    if materiais_custos is not None and not materiais_custos.empty:
                        for _, row in materiais_custos.iterrows():
                            lista_mat.append([
                                row.get("Material", ""),
                                round(row.get("Quantidade", 0), 2),
                                row.get("Preço", 0),
                                round(row.get("Custo", 0), 2),
                            ])

                    custos_etapas = {}
                    df_custos_etapas = orcamento.get("custos_etapas")

                    if df_custos_etapas is not None and not df_custos_etapas.empty:
                        for _, row in df_custos_etapas.iterrows():
                            etapa = row.get("Etapa", "Outros")
                            custo = row.get("Total", 0)
                            custos_etapas[etapa] = custos_etapas.get(etapa, 0) + custo

                    df_insumos = carregar_insumos(obra)

                    if df_insumos is None or df_insumos.empty:
                        df_insumos = pd.DataFrame(columns=[
                            "Material",
                            "Etapa",
                            "ValorTotal",
                            "NotaID"
                        ])

                    df_previsto_etapas = pd.DataFrame([
                        {"Etapa": etapa, "Previsto": valor}
                        for etapa, valor in custos_etapas.items()
                    ])

                    df_real_etapas = df_insumos.copy()

                    if "ValorTotal" in df_real_etapas.columns:
                        df_real_etapas = df_real_etapas.rename(columns={"ValorTotal": "Valor"})

                    auditoria_etapas = gerar_comparativo_por_dimensao(
                        df_previsto_etapas,
                        df_real_etapas,
                        dimensao="Etapa"
                    )

                    comparativo_etapas = auditoria_etapas["comparativo"]

                    st.session_state["orcamento_tecnico_resultado"] = orcamento
                    st.session_state["orcamento_tecnico_render"] = {
                        "area_total": area_total,
                        "area_cobertura": area_cobertura,
                        "custo_mao_obra": custo_mao_obra,
                        "custo_material": custo_material,
                        "custo_total": custo_total,
                        "custo_m2": custo_m2,
                        "lista_mat": lista_mat,
                        "custos_etapas": custos_etapas,
                        "comparativo_etapas": comparativo_etapas,
                        "materiais_fallback": materiais_fallback,
                    }
                    st.rerun()

        with col_side:
            st.markdown("### 📊 Resumo")
            st.metric("Área", f"{area_total} m²")
            st.metric("Cobertura", f"{area_cobertura} m²")

    with aba_calcular_obra:
        st.divider()
        st.subheader("🧠 Orçamento completo da obra")

        col1, col2 = st.columns(2)

        with col1:
            area = st.number_input("Área da obra (m²)", min_value=10.0, step=10.0)

        with col2:
            margem = st.slider("Margem de lucro (%)", 0, 100, 25)

        tipo_obra = st.selectbox(
            "🏗 Tipo de obra",
            ["Casa", "Prédio", "Galpão"]
        )

        if st.button("🚀 Calcular obra completa", use_container_width=True):
            if "tabela_composicao" not in st.session_state:
                st.error("Cadastre a composição primeiro")
                return

            if "tabela_materiais" not in st.session_state:
                st.error("Cadastre os materiais primeiro")
                return

            if "tabela_mao_obra" not in st.session_state:
                st.error("Cadastre a mão de obra primeiro")
                return

            try:
                mat, mo, total, m2, p_mat, p_mo = calcular_obra(
                    area,
                    tipo_obra,
                    st.session_state.tabela_composicao,
                    st.session_state.tabela_materiais,
                    st.session_state.tabela_mao_obra
                )

            except Exception as e:
                st.error(f"Erro no cálculo: {e}")
                return

            st.success("Orçamento gerado com base técnica")
            venda = total * (1 + margem / 100)
            lucro = venda - total

            c1, c2, c3, c4 = st.columns(4)

            c1.metric("💰 Custo total", f"R$ {total:,.2f}")
            c2.metric("📊 Custo/m²", f"R$ {m2:,.2f}")
            c3.metric("💵 Venda sugerida", f"R$ {venda:,.2f}")
            c4.metric("📈 Lucro", f"R$ {lucro:,.2f}")

            st.divider()
            c5, c6 = st.columns(2)
            c5.metric("🧱 % Material", f"{p_mat*100:.1f}%")
            c6.metric("👷 % Mão de obra", f"{p_mo*100:.1f}%")

            fig = px.pie(
                names=["Material", "Mão de obra"],
                values=[mat["Custo"].sum(), mo["Custo"].sum()],
                title="Distribuição de custos"
            )

            st.plotly_chart(fig, use_container_width=True, key="grafico_custos_obra")

            st.divider()
            st.subheader("🏆 Materiais mais caros")

            top = mat.sort_values("Custo", ascending=False).head(10)
            st.dataframe(top, use_container_width=True)

            if not mat.empty:
                maior = mat.iloc[0]
                st.warning(
                    f"⚠️ Maior custo: {maior['Material']} → R$ {maior['Custo']:,.2f}"
                )

            st.divider()
            st.subheader("📦 Materiais necessários")
            st.dataframe(mat, use_container_width=True)

            st.subheader("👷 Mão de obra")
            st.dataframe(mo, use_container_width=True)

            st.divider()

            if st.button("💾 Salvar orçamento"):
                st.session_state["ultimo_orcamento"] = {
                    "obra": obra,
                    "area": area,
                    "materiais": mat,
                    "mao_obra": mo,
                    "custo_total": total,
                    "custo_m2": m2,
                    "venda": venda,
                    "lucro": lucro
                }

                st.success("Orçamento salvo com sucesso!")
