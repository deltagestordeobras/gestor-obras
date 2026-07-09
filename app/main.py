import streamlit as st

from database.init_db import inicializar_banco


inicializar_banco()

st.set_page_config(
    page_title="Delta",
    page_icon="icons/favicon.ico",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    """
    <link rel="manifest" href="/manifest.json">
    <meta name="theme-color" content="#0f172a">
    """,
    unsafe_allow_html=True,
)

from app.administracao import tela_administracao
from app.auditoria import tela_auditoria
from app.backup import tela_backup
from app.auth import tela_recuperacao
from app.configuracoes import tela_configuracoes
from app.consulta_pagamentos import tela_consulta_pagamentos
from app.cronograma import tela_cronograma
from app.dashboard import tela_dashboard
from app.diario_obra import tela_diario_obra
from app.erp import tela_erp_lancamento
from app.evolucao import tela_evolucao
from app.fornecedores import tela_fornecedores
from app.lancamentos_parceiro import tela_lancamentos_parceiro
from app.lancamentos import tela_painel_completo
from app.materiais import tela_materiais
from app.orcamento import tela_orcamento
from app.painel import tela_painel
from app.produtos import tela_produtos
from app.relatorio_materiais import tela_relatorio_materiais
from app.style import aplicar_estilo
from app.usuarios import tela_usuarios
from services.lancamento import carregar_lancamentos
from services.obra import buscar_nome_obra, criar_obra, listar_obras, normalizar_nome_obra
from services.permissoes import permissoes_por_perfil, tem_permissao
from services.backup import criar_backup_automatico_diario
from services.usuario import autenticar_usuario, criar_primeiro_admin, definir_senha, existe_admin


def _tela_login():
    _, centro, _ = st.columns([1.25, 0.9, 1.25])
    with centro:
        if st.session_state.pop("primeiro_admin_criado", False):
            st.success("ADMIN criado com sucesso. Fa?a login para continuar.")
        st.image("icons/logo.png", use_container_width=True)
        st.markdown(
            """
            <div class="delta-login-title">
                <span>Gestão de obras inteligente</span>
                <h1>DELTA Gestor de Obras</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("login", border=True):
            usuario = st.text_input("Usuário", key="login_usuario")
            senha = st.text_input("Senha", type="password", key="login_senha")
            entrar = st.form_submit_button("Entrar", type="primary", use_container_width=True)
            if entrar:
                user = autenticar_usuario(usuario, senha)
                if not user:
                    st.error("Usuário ou senha inválidos.")
                    return
                if user.get("primeiro_acesso"):
                    st.session_state["primeiro_acesso"] = True
                    st.session_state["usuario_temp"] = usuario
                    st.rerun()
                st.session_state.update({
                    "logado": True,
                    "usuario": usuario,
                    "perfil": user["Perfil"],
                    "obra_id": user["ObraID"],
                    "permissoes": user.get("Permissoes", []),
                })
                st.rerun()
        if st.button("Esqueci minha senha", use_container_width=True, key="login_recuperar"):
            st.session_state["recuperacao"] = True
            st.rerun()
        st.markdown('<div class="delta-login-footer">Powered by Delta Sistemas</div>', unsafe_allow_html=True)


def _tela_primeiro_admin():
    _, centro, _ = st.columns([1.2, 0.95, 1.2])
    with centro:
        st.image("icons/logo.png", use_container_width=True)
        st.markdown(
            """
            <div class="delta-login-title">
                <span>Instalação inicial</span>
                <h1>Primeiro acesso</h1>
            </div>
            """,
            unsafe_allow_html=True,
        )
        with st.form("primeiro_admin", border=True):
            nome = st.text_input("Nome")
            email = st.text_input("E-mail")
            usuario = st.text_input("Usuário")
            senha = st.text_input("Senha", type="password")
            confirmar = st.text_input("Confirmar senha", type="password")
            criar = st.form_submit_button("Criar primeiro ADMIN", type="primary", use_container_width=True)

            if criar:
                if senha != confirmar:
                    st.warning("Informe senhas iguais.")
                    return

                ok, erro = criar_primeiro_admin(nome, email, usuario, senha)
                if ok:
                    st.session_state["primeiro_admin_criado"] = True
                    st.session_state["logado"] = False
                    st.session_state["recuperacao"] = False
                    st.session_state["primeiro_acesso"] = False
                    st.rerun()
                else:
                    st.error(erro)

        st.markdown('<div class="delta-login-footer">Powered by Delta Sistemas</div>', unsafe_allow_html=True)


def _tela_primeiro_acesso():
    st.title("Criar senha")
    st.info("Este é seu primeiro acesso. Defina sua senha.")
    nova_senha = st.text_input("Nova senha", type="password")
    confirmar = st.text_input("Confirmar senha", type="password")
    if st.button("Salvar senha", type="primary"):
        if not nova_senha or nova_senha != confirmar:
            st.error("Preencha senhas iguais.")
            return
        ok, erro = definir_senha(st.session_state["usuario_temp"], nova_senha)
        if ok:
            st.session_state["primeiro_acesso"] = False
            st.success("Senha criada.")
            st.rerun()
        st.error(erro)


for chave, valor in {
    "logado": False,
    "recuperacao": False,
    "primeiro_acesso": False,
    "primeiro_admin_criado": False,
    "usuario_temp": None,
}.items():
    st.session_state.setdefault(chave, valor)

aplicar_estilo()
if "backup_automatico_diario_verificado" not in st.session_state:
    criar_backup_automatico_diario()
    st.session_state["backup_automatico_diario_verificado"] = True

if not existe_admin():
    _tela_primeiro_admin()
    st.stop()
if st.session_state["recuperacao"]:
    tela_recuperacao()
    st.stop()
if st.session_state["primeiro_acesso"]:
    _tela_primeiro_acesso()
    st.stop()
if not st.session_state["logado"]:
    _tela_login()
    st.stop()

permissoes = permissoes_por_perfil(
    st.session_state.get("perfil"),
    st.session_state.get("permissoes", []),
)

GRUPOS = [
    ("🏠 Início", "inicio"),
    ("📋 Cadastros", "cadastros"),
    ("💰 Financeiro", "financeiro"),
    ("🏗 Obras", "obras"),
    ("⚙ Administração", "administracao_grupo"),
]

GRUPOS_PARCEIRO = {
    "administracao_grupo": "Minha Conta",
}

ROTAS = [
    ("🏠 Geral", "painel", "painel", "inicio"),
    ("📊 Dashboard", "dashboard", "dashboard", "inicio"),
    ("📋 Fornecedores", "fornecedores", "fornecedores", "cadastros"),
    ("📦 Produtos", "produtos", "produtos", "cadastros"),
    ("🧱 Materiais", "materiais", "materiais", "cadastros"),
    ("👥 Usuários", "usuarios", "usuarios", "cadastros"),
    ("📝 Notas", "lancamentos", "lancamentos", "financeiro"),
    ("💰 Pagamentos", "consulta_pagamentos", "consulta_pagamentos", "financeiro"),
    ("📋 Despesas", "relatorio_materiais", "relatorio_materiais", "financeiro"),
    ("📦 ERP", "erp", "erp", "financeiro"),
    ("📐 Orçamento", "orcamento", "orcamento", "obras"),
    ("📅 Cronograma", "cronograma", "cronograma", "obras"),
    ("📸 Evolução", "evolucao", "evolucao", "obras"),
    ("📔 Diário de Obra", "diario_obra", "diario_obra", "obras"),
    ("⚙ Permissões", "administracao", "administracao", "administracao_grupo"),
    ("🔧 Configurações", "configuracoes", "configuracoes", "administracao_grupo"),
    ("✉ E-mail", "config_email", "configuracoes", "administracao_grupo"),
    ("📋 Listas do Sistema", "config_listas", "configuracoes", "administracao_grupo"),
    ("Auditoria", "auditoria", "administracao", "administracao_grupo"),
    ("Backup", "backup", "backup", "administracao_grupo"),
]


def _permitido(regra):
    return tem_permissao(regra, permissoes=permissoes)


rotas_visiveis = [rota for rota in ROTAS if _permitido(rota[2])]
if st.session_state["perfil"] != "ADMIN":
    rotas_visiveis = [
        rota for rota in rotas_visiveis
        if rota[1] not in {"usuarios", "config_email", "config_listas", "backup"}
    ]
if not rotas_visiveis:
    st.error("Sem permissões de acesso.")
    st.stop()

atalhos_legados = {
    "📐 Orçamento da Obra": "orcamento",
    "📊 Painel Financeiro": "painel",
}
rota_pendente = st.session_state.pop("painel_aba_ativa", None)
menu_pendente = st.session_state.pop("menu_principal_pendente", None)
if menu_pendente:
    rota_pendente = atalhos_legados.get(menu_pendente, rota_pendente)

ids_visiveis = [rota[1] for rota in rotas_visiveis]
if rota_pendente in ids_visiveis:
    st.session_state["modulo_ativo"] = rota_pendente
    st.session_state["grupo_ativo"] = next(
        rota[3] for rota in rotas_visiveis if rota[1] == rota_pendente
    )
if st.session_state.get("modulo_ativo") not in ids_visiveis:
    st.session_state["modulo_ativo"] = ids_visiveis[0]

grupos_visiveis = [
    grupo for grupo in GRUPOS
    if any(rota[3] == grupo[1] for rota in rotas_visiveis)
]
ids_grupos_visiveis = [grupo[1] for grupo in grupos_visiveis]
if st.session_state.get("grupo_ativo") not in ids_grupos_visiveis:
    st.session_state["grupo_ativo"] = next(
        rota[3] for rota in rotas_visiveis
        if rota[1] == st.session_state["modulo_ativo"]
    )

df_obras = listar_obras()
sem_obras = df_obras is None or df_obras.empty

with st.sidebar:
    st.image("icons/logo.png", use_container_width=True)
    perfil_exibicao = "ADMIN" if st.session_state["perfil"] == "ADMIN" else "PARCEIRO"
    st.markdown(
        f"""
        <div class="delta-sidebar-profile">
            <span>Conectado como</span>
            <strong>{perfil_exibicao}</strong>
            <small>{st.session_state["usuario"]}</small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state["perfil"] == "ADMIN":
        if sem_obras:
            obra_selecionada = None
            obra_id = None
            st.caption("Obra selecionada")
            st.info("Nenhuma obra cadastrada.")
        else:
            obras_dict = {row["Nome"]: row["ID"] for _, row in df_obras.iterrows()}
            nomes_obras = list(obras_dict.keys())
            obra_anterior = st.session_state.get("obra_nome")
            indice_obra = nomes_obras.index(obra_anterior) if obra_anterior in nomes_obras else 0
            obra_selecionada = st.selectbox("Obra selecionada", nomes_obras, index=indice_obra)
            obra_id = obras_dict[obra_selecionada]
        if st.button("+ Nova Obra", use_container_width=True, key="abrir_nova_obra"):
            st.session_state["mostrar_nova_obra"] = not st.session_state.get("mostrar_nova_obra", False)
        if st.session_state.get("mostrar_nova_obra"):
            nome_obra = st.text_input("Nome da obra", key="nova_obra_sidebar")
            if st.button("Criar obra", use_container_width=True):
                ok, erro = criar_obra(nome_obra)
                if ok:
                    st.session_state["mostrar_nova_obra"] = False
                    st.session_state["obra_nome"] = normalizar_nome_obra(nome_obra)
                    st.success("Obra criada.")
                    st.rerun()
                st.error(erro)
    else:
        obra_id = st.session_state.get("obra_id")
        obra_selecionada = buscar_nome_obra(obra_id) if obra_id else None
        if not obra_selecionada:
            st.error("Usuário sem obra vinculada.")
            st.stop()
        st.caption("Obra selecionada")
        st.markdown(f"**{obra_selecionada}**")

    st.session_state["obra_id_atual"] = obra_id
    st.session_state["obra_nome"] = obra_selecionada
    st.markdown('<div class="delta-menu-label">MENU PRINCIPAL</div>', unsafe_allow_html=True)
    for rotulo_grupo, grupo_id in grupos_visiveis:
        rotulo_exibido = (
            GRUPOS_PARCEIRO.get(grupo_id, rotulo_grupo)
            if st.session_state["perfil"] != "ADMIN"
            else rotulo_grupo
        )
        if st.button(
            rotulo_exibido,
            key=f"grupo_{grupo_id}",
            type="primary" if grupo_id == st.session_state["grupo_ativo"] else "secondary",
            use_container_width=True,
        ):
            st.session_state.pop("admin_navegacao_interna", None)
            st.session_state.pop("usuarios_secao", None)
            st.session_state["grupo_ativo"] = grupo_id
            st.rerun()
    grupo_ativo = st.session_state["grupo_ativo"]
    if st.button("Sair", use_container_width=True, key="logout_sidebar"):
        st.session_state.clear()
        st.rerun()
    st.markdown('<div class="delta-sidebar-footer">Powered by Delta Sistemas</div>', unsafe_allow_html=True)

if sem_obras:
    st.markdown(
        """
        <div class="delta-admin-hero">
            <span>Primeiros passos</span>
            <h1>Bem-vindo ao DELTA Gestor de Obras</h1>
            <p>Para come?ar, cadastre sua primeira obra.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if st.button("+ Cadastrar primeira obra", type="primary", use_container_width=True):
        st.session_state["mostrar_nova_obra"] = True
        st.rerun()
    st.stop()

rotas_grupo = [rota for rota in rotas_visiveis if rota[3] == grupo_ativo]
ids_rotas_grupo = [rota[1] for rota in rotas_grupo]
if st.session_state.get("modulo_ativo") not in ids_rotas_grupo:
    st.session_state["modulo_ativo"] = ids_rotas_grupo[0]

rotulo_grupo_ativo = next(grupo[0] for grupo in grupos_visiveis if grupo[1] == grupo_ativo)
if st.session_state["perfil"] != "ADMIN":
    rotulo_grupo_ativo = GRUPOS_PARCEIRO.get(grupo_ativo, rotulo_grupo_ativo)

admin_navegacao_interna = bool(st.session_state.get("admin_navegacao_interna"))
mostrar_voltar_admin = (
    admin_navegacao_interna
    and st.session_state.get("modulo_ativo") != "administracao"
)
mostrar_submenu = (
    grupo_ativo != "administracao_grupo"
    and not mostrar_voltar_admin
)

if mostrar_voltar_admin:
    if st.button("← Voltar para Administração", key="voltar_administracao", use_container_width=False):
        st.session_state["modulo_ativo"] = "administracao"
        st.session_state["grupo_ativo"] = "administracao_grupo"
        st.session_state.pop("admin_navegacao_interna", None)
        st.session_state.pop("usuarios_secao", None)
        st.rerun()
elif mostrar_submenu:
    st.markdown(
        f'<div class="delta-submenu-context"><span>Módulos</span><strong>{rotulo_grupo_ativo}</strong></div>',
        unsafe_allow_html=True,
    )

    for inicio in range(0, len(rotas_grupo), 4):
        linha = rotas_grupo[inicio:inicio + 4]
        colunas = st.columns(4)
        for indice, rota in enumerate(linha):
            rotulo, rota_id = rota[0], rota[1]
            rotulo_exibido = rotulo
            if st.session_state["perfil"] != "ADMIN" and rota_id == "administracao":
                rotulo_exibido = "Perfil"
            with colunas[indice]:
                if st.button(
                    rotulo_exibido,
                    key=f"submenu_{rota_id}",
                    type="primary" if rota_id == st.session_state["modulo_ativo"] else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["modulo_ativo"] = rota_id
                    st.session_state.pop("admin_navegacao_interna", None)
                    if rota_id == "usuarios":
                        st.session_state["usuarios_secao"] = "usuarios"
                    else:
                        st.session_state.pop("usuarios_secao", None)
                    st.rerun()

modulo_ativo = st.session_state["modulo_ativo"]

df_obra = carregar_lancamentos(obra_selecionada)

if modulo_ativo == "painel":
    tela_painel(df_obra, obra_selecionada, obra_id)
elif modulo_ativo == "lancamentos":
    if st.session_state["perfil"] == "PARCEIRO":
        tela_lancamentos_parceiro(df_obra, obra_selecionada, key_prefix="filtro_notas_parceiro")
    else:
        tela_painel_completo(obra_selecionada)
elif modulo_ativo == "materiais":
    tela_materiais(obra_selecionada)
elif modulo_ativo == "erp":
    tela_erp_lancamento(obra_selecionada)
elif modulo_ativo == "dashboard":
    tela_dashboard(df_obra)
elif modulo_ativo == "cronograma":
    tela_cronograma(obra_id, obra_selecionada)
elif modulo_ativo == "evolucao":
    tela_evolucao(obra_id, obra_selecionada)
elif modulo_ativo == "diario_obra":
    tela_diario_obra(obra_id, obra_selecionada)
elif modulo_ativo == "relatorio_materiais":
    tela_relatorio_materiais(obra_selecionada)
elif modulo_ativo == "produtos":
    tela_produtos()
elif modulo_ativo == "consulta_pagamentos":
    tela_consulta_pagamentos(obra_selecionada, df_obra=df_obra)
elif modulo_ativo == "fornecedores":
    tela_fornecedores(obra_selecionada, df_obra=df_obra)
elif modulo_ativo == "orcamento":
    tela_orcamento(obra_selecionada)
elif modulo_ativo == "usuarios":
    tela_usuarios()
elif modulo_ativo == "administracao":
    tela_administracao(obra_selecionada)
elif modulo_ativo == "auditoria":
    tela_auditoria(obra_selecionada)
elif modulo_ativo == "backup":
    tela_backup()
elif modulo_ativo in {"configuracoes", "config_email", "config_listas"}:
    aba_configuracao = {
        "config_email": "✉ E-mail",
        "config_listas": "Listas do Sistema",
    }.get(modulo_ativo)
    tela_configuracoes(aba_configuracao)
