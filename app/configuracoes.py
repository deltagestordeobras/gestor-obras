import streamlit as st
import pandas as pd
from services.recuperacao_senha import (
    _config_email,
    diagnosticar_configuracao_smtp,
    salvar_configuracao_smtp,
    testar_envio_email,
)
from services.listas import (
    TIPO_ETAPA_OBRA,
    adicionar_item,
    carregar_lista,
    definir_item_ativo,
    renomear_item,
)


def _tela_listas_sistema():
    st.divider()
    st.subheader("Listas do Sistema")
    st.caption("Itens desativados permanecem nos registros antigos, mas não aparecem em novos lançamentos.")

    etapas = carregar_lista(TIPO_ETAPA_OBRA, somente_ativos=False)
    with st.form("form_adicionar_etapa"):
        nova_etapa = st.text_input("Nova etapa da obra")
        if st.form_submit_button("Adicionar etapa", type="primary"):
            ok, erro = adicionar_item(TIPO_ETAPA_OBRA, nova_etapa)
            if ok:
                st.success("Etapa adicionada.")
                st.rerun()
            st.error(erro)

    if etapas.empty:
        st.info("Nenhuma etapa cadastrada.")
        return

    st.markdown("#### Etapas da obra")
    for _, etapa in etapas.iterrows():
        col_nome, col_status, col_acao = st.columns([3, 1, 1.2], vertical_alignment="center")
        with col_nome:
            novo_nome = st.text_input(
                "Nome",
                value=str(etapa["Nome"]),
                key=f"lista_nome_{etapa['ID']}",
                label_visibility="collapsed",
            )
        with col_status:
            ativo = st.toggle(
                "Ativa",
                value=bool(etapa["Ativo"]),
                key=f"lista_ativo_{etapa['ID']}",
            )
        with col_acao:
            if st.button("Salvar", key=f"lista_salvar_{etapa['ID']}", use_container_width=True):
                ok, erro = renomear_item(etapa["ID"], novo_nome)
                if not ok:
                    st.error(erro)
                    continue
                definir_item_ativo(etapa["ID"], ativo)
                st.success("Etapa atualizada.")
                st.rerun()


def _tela_email():
    st.divider()
    st.subheader("Configuração de e-mail")
    st.caption("As credenciais são armazenadas no arquivo seguro do Streamlit.")

    config = _config_email()
    diagnostico = diagnosticar_configuracao_smtp()
    if diagnostico["faltando"]:
        st.warning("Campos ausentes: " + ", ".join(diagnostico["faltando"]))
    else:
        st.success("Configuração SMTP completa.")

    with st.form("form_configuracao_smtp"):
        smtp_server = st.text_input(
            "Servidor SMTP",
            value=config.get("smtp_server", ""),
        )
        smtp_port = st.text_input(
            "Porta",
            value=config.get("smtp_port", ""),
        )
        smtp_user = st.text_input(
            "Usuário SMTP",
            value=config.get("smtp_user", ""),
        )
        smtp_password = st.text_input(
            "Senha SMTP",
            type="password",
            placeholder="Deixe vazio para manter a senha atual",
        )
        smtp_from = st.text_input(
            "E-mail remetente",
            value=config.get("smtp_from", ""),
        )

        if st.form_submit_button("Salvar configuração"):
            ok, erro = salvar_configuracao_smtp(
                smtp_server,
                smtp_port,
                smtp_user,
                smtp_password,
                smtp_from,
            )
            if ok:
                st.success("Configuração SMTP salva.")
                st.rerun()
            else:
                st.error(erro)

    email_teste = st.text_input(
        "Destinatário do teste",
        value="diegobessas@gmail.com",
        key="smtp_email_teste",
    )
    if st.button("Testar envio", key="config_testar_smtp"):
        ok, erro = testar_envio_email(email_teste)
        if ok:
            st.success(f"E-mail de teste enviado para {email_teste}.")
        else:
            st.error(erro)


def tela_configuracoes(aba_inicial=None):

    st.subheader("🔧 Configurações")

    admin = st.session_state.get("perfil") == "ADMIN"
    if admin and aba_inicial == "Listas do Sistema":
        _tela_listas_sistema()
        return
    if admin and aba_inicial == "✉ E-mail":
        _tela_email()
        return

    abas = [
        "👷 Mão de obra",
        "🧱 Materiais",
        "📐 Composição",
        "📊 Parâmetros",
        "🌎 SINAPI",
    ]
    if admin:
        abas.extend(["Listas do Sistema", "✉ E-mail"])

    tabs = st.tabs(abas)
    aba_mo, aba_mat, aba_comp, aba_param, aba_sinapi = tabs[:5]
    aba_listas = tabs[5] if len(tabs) > 5 else None
    aba_email = tabs[6] if len(tabs) > 6 else None

    # ==============================
    # 👷 MÃO DE OBRA
    # ==============================
    with aba_mo:

        st.divider()
        st.subheader("👷 Tabela de Mão de Obra")

        if "tabela_mao_obra" not in st.session_state:
            st.session_state.tabela_mao_obra = pd.DataFrame({
                "Serviço": [
                    "Revestimento", "Forma Baldrame", "Forma Pilares e Vigas",
                    "Piso Cerâmico", "Piso Porcelanato", "Reboco Externo",
                    "Reboco Interno", "Alvenaria", "Concreto",
                    "Contra Piso", "Demolição", "Laje com Escoramento",
                    "Furo Fundação", "Armação", "Marcação Terreno"
                ],
                "Preço": [
                    55, 70, 90, 45, 50, 35, 30, 34, 18, 25, 30, 95, 90, 8, 3500
                ]
            })

        edited_mo = st.data_editor(st.session_state.tabela_mao_obra, use_container_width=True)

        if st.button("💾 Salvar mão de obra"):
            st.session_state.tabela_mao_obra = edited_mo
            st.success("Tabela atualizada!")

    # ==============================
    # 🧱 MATERIAIS
    # ==============================
    with aba_mat:

        st.divider()
        st.subheader("🧱 Tabela de Materiais")

        if "tabela_materiais" not in st.session_state:
            st.session_state.tabela_materiais = pd.DataFrame({
                "Material": [
                    "Cimento CP II","Cal hidratada","Areia média","Areia fina","Brita 1","Brita 0",
                    "Tijolo cerâmico","Bloco estrutural","Aço CA50","Arame recozido",
                    "Laje treliçada","Laje maciça","Telha cerâmica","Telha metálica",
                    "Argamassa AC1","Argamassa AC2","Rejunte","Piso cerâmico",
                    "Piso porcelanato","Piso vinílico","Revestimento cerâmico",
                    "Tinta acrílica","Massa corrida","Porta madeira","Janela alumínio",
                    "Vaso sanitário","Cuba lavatório","Cuba inox","Granito",
                    "Caixa d'água 1000L","Tubo PVC 100mm","Tubo PVC 50mm",
                    "Fio 2.5mm","Fio 4mm","Disjuntor","Madeira",
                    "Telha metálica","Telha sanduíche","Estrutura metálica"
                ],
                "Unidade": [
                    "saco","saco","m³","m³","m³","m³","un","un","kg","kg",
                    "m²","m²","m²","m²","saco","saco","kg","m²","m²","m²",
                    "m²","L","kg","un","un","un","un","un","m²","un","m",
                    "m","m","m","un","m³","m²","m²","kg ou m²"
                ],
                "Preço": [
                    38,32,140,150,180,190,1.2,3.5,8,12,
                    110,150,65,95,18,28,9,45,85,120,
                    50,22,6,420,650,350,220,280,420,520,
                    35,18,2.8,4.2,28,900,200,120,25
                ]
            })

        edited_mat = st.data_editor(st.session_state.tabela_materiais, use_container_width=True)

        if st.button("💾 Salvar materiais"):
            st.session_state.tabela_materiais = edited_mat
            st.success("Materiais atualizados!")

    # ==============================
    # 📐 COMPOSIÇÃO
    # ==============================
    with aba_comp:

        st.divider()
        st.subheader("📐 Composição de Serviços")

        if "tabela_composicao" not in st.session_state:

            st.session_state.tabela_composicao = pd.DataFrame({
                "Serviço": [
                    "Alvenaria","Alvenaria","Alvenaria","Alvenaria",
                    "Chapisco","Chapisco",
                    "Reboco Interno","Reboco Interno","Reboco Interno",
                    "Reboco Externo","Reboco Externo","Reboco Externo",
                    "Concreto","Concreto","Concreto",
                    "Contra Piso","Contra Piso",
                    "Piso Cerâmico","Piso Cerâmico",
                    "Piso Porcelanato","Piso Porcelanato",
                    "Revestimento","Revestimento",
                    "Pintura","Pintura",
                    "Cobertura Cerâmica","Cobertura Cerâmica",
                    "Cobertura Metálica","Cobertura Metálica",
                    "Cobertura Sanduíche","Cobertura Sanduíche",
                    "Instalação Elétrica","Instalação Elétrica","Instalação Elétrica",
                    "Instalação Hidráulica","Instalação Hidráulica",
                    "Armação","Armação",
                    "Laje com Escoramento","Laje com Escoramento",
                ],
                "Material": [
                    "Tijolo cerâmico","Cimento CP II","Areia média","Cal hidratada",
                    "Cimento CP II","Areia média",
                    "Cimento CP II","Areia média","Cal hidratada",
                    "Cimento CP II","Areia média","Cal hidratada",
                    "Cimento CP II","Areia média","Brita 1",
                    "Cimento CP II","Areia média",
                    "Argamassa AC1","Rejunte",
                    "Argamassa AC2","Rejunte",
                    "Argamassa AC1","Rejunte",
                    "Tinta acrílica","Massa corrida",
                    "Telha cerâmica","Madeira",
                    "Telha metálica","Estrutura metálica",
                    "Telha sanduíche","Estrutura metálica",
                    "Fio 2.5mm","Fio 4mm","Disjuntor",
                    "Tubo PVC 50mm","Tubo PVC 100mm",
                    "Aço CA50","Arame recozido",
                    "Concreto","Aço CA50",
                ],
                "Consumo": [
                    18,0.12,0.02,0.02,
                    0.10,0.015,
                    0.12,0.018,2,
                    0.15,0.020,2,
                    7,0.55,0.80,
                    0.12,0.018,
                    0.20,0.05,
                    0.5,0.05,
                    0.20,0.05,
                    0.18,0.10,
                    1.10,0.03,
                    1.05,15,
                    1.05,15,
                    4,2,0.05,
                    1.5,0.5,
                    12,0.3,
                    0.15,8,
                ]
            })

        edited_comp = st.data_editor(st.session_state.tabela_composicao, use_container_width=True)

        if st.button("💾 Salvar composição"):
            st.session_state.tabela_composicao = edited_comp
            st.success("Composição atualizada!")

    # ==============================
    # 📊 PARÂMETROS
    # ==============================
    with aba_param:

        st.divider()
        st.subheader("📊 Parâmetros de Orçamento")

        if "parametros_obra" not in st.session_state:

            st.session_state.parametros_obra = {
                "coef_concreto": 0.13,
                "coef_aco": 12,
                "coef_tijolo": 27,
                "coef_cimento": 6.5,
                "coef_areia": 0.09,
                "coef_brita": 0.08,
                "coef_telha": 1.3,
                "coef_pintura": 3,
                "custo_instalacoes_m2": 120,
            }

        p = st.session_state.parametros_obra

        c1, c2, c3 = st.columns(3)

        with c1:
            p["coef_concreto"] = st.number_input("Concreto m³/m²", value=p["coef_concreto"])
            p["coef_aco"] = st.number_input("Aço kg/m²", value=p["coef_aco"])
            p["coef_tijolo"] = st.number_input("Tijolos un/m²", value=p["coef_tijolo"])

        with c2:
            p["coef_cimento"] = st.number_input("Cimento saco/m²", value=p["coef_cimento"])
            p["coef_areia"] = st.number_input("Areia m³/m²", value=p["coef_areia"])
            p["coef_brita"] = st.number_input("Brita m³/m²", value=p["coef_brita"])

        with c3:
            p["coef_telha"] = st.number_input("Coef Telhado", value=p["coef_telha"])
            p["coef_pintura"] = st.number_input("Coef Pintura", value=p["coef_pintura"])
            p["custo_instalacoes_m2"] = st.number_input("Instalações R$/m²", value=p["custo_instalacoes_m2"])

        if st.button("💾 Salvar parâmetros", key="salvar_parametros"):
            st.session_state.parametros_obra = p
            st.success("Parâmetros atualizados")

    # ==============================
    # 🌎 SINAPI
    # ==============================
    with aba_sinapi:

        st.divider()
        st.subheader("🌎 Atualizar SINAPI")

        if st.button("⬇️ Atualizar preços SINAPI"):
            st.info("Integração futura com SINAPI")

    if aba_listas is not None:
        with aba_listas:
            _tela_listas_sistema()

    if aba_email is not None:
        with aba_email:
            _tela_email()
