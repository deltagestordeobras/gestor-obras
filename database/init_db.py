from database.connection import criar_tabela_insumos, get_connection
import logging


# ===============================
# 🏗 TABELA OBRAS
# ===============================
def criar_tabela_obras():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS obras (
            ID TEXT,
            Nome TEXT,
            DataCriacao TEXT
        )
    """)

    conn.commit()
    conn.close()


# ===============================
# 👤 TABELA USUÁRIOS
# ===============================
def criar_tabela_usuarios():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            Nome TEXT,
            Usuario TEXT PRIMARY KEY,
            Senha TEXT,
            Perfil TEXT,
            ObraID TEXT,
            Permissoes TEXT,
            TokenReset TEXT,
            TokenExpira TEXT,
            Telefone TEXT,
            Email TEXT,
            TokenTentativas INTEGER DEFAULT 0
        )
    """)

    conn.commit()
    conn.close()


# ===============================
# 📊 TABELA LANÇAMENTOS
# ===============================
def criar_tabela_lancamentos():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS lancamentos (
            ID TEXT,
            Obra TEXT,
            Tipo TEXT,
            "Nº Nota" TEXT,
            "Entrada Nota" TEXT,
            "Data Vencimento" TEXT,
            "Data Pagto" TEXT,
            "Criado Em" TEXT,
            "Pago Em" TEXT,
            "Descrição" TEXT,
            Categoria TEXT,
            Etapa TEXT,
            Valor REAL,
            Status TEXT,
            Foto TEXT,
            StatusNota TEXT,
            Fornecedor TEXT,
            Frete REAL,
            Desconto REAL,
            Imposto REAL
        )
    """)

    conn.commit()
    conn.close()


# ===============================
# 📦 TABELA MATERIAIS BASE
# ===============================
def criar_tabela_materiais():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS materiais (
            ID TEXT,
            Material TEXT,
            Unidade TEXT,
            Preco REAL
        )
    """)

    conn.commit()
    conn.close()


# ===============================
# 🏢 FORNECEDORES
# ===============================
def criar_tabela_fornecedores():
    conn = get_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS fornecedores (
            ID TEXT,
            Nome TEXT,
            Rua TEXT,
            Numero TEXT,
            Bairro TEXT,
            Cidade TEXT,
            CEP TEXT,
            Telefone TEXT,
            Documento TEXT,
            ChavePix TEXT,
            Ativo INTEGER DEFAULT 1
        )
    """)

    colunas = {
        row[1] for row in conn.execute("PRAGMA table_info(fornecedores)").fetchall()
    }
    if "Ativo" not in colunas:
        conn.execute("ALTER TABLE fornecedores ADD COLUMN Ativo INTEGER DEFAULT 1")

    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_fornecedores_ativo_nome
        ON fornecedores (Ativo, Nome)
    """)

    conn.commit()
    conn.close()


def criar_tabela_cronograma():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS cronograma (
            ID TEXT,
            ObraID TEXT,
            Obra TEXT,
            Etapa TEXT,
            Duracao INTEGER,
            Dependencia TEXT,
            Inicio TEXT,
            Fim TEXT,
            Progresso REAL DEFAULT 0,
            Status TEXT,
            Ordem INTEGER
        )
    """)

    colunas = {
        row[1] for row in c.execute("PRAGMA table_info(cronograma)").fetchall()
    }
    migracoes = {
        "ObraID": "TEXT",
        "Obra": "TEXT",
        "Etapa": "TEXT",
        "Duracao": "INTEGER",
        "Dependencia": "TEXT",
        "Inicio": "TEXT",
        "Fim": "TEXT",
        "Progresso": "REAL DEFAULT 0",
        "Status": "TEXT",
        "Ordem": "INTEGER",
    }

    for coluna, tipo in migracoes.items():
        if coluna not in colunas:
            c.execute(f'ALTER TABLE cronograma ADD COLUMN "{coluna}" {tipo}')

    conn.commit()
    conn.close()


def criar_tabela_evolucao_obra():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS evolucao_obra (
            ID TEXT PRIMARY KEY,
            ObraID TEXT,
            Obra TEXT,
            Etapa TEXT,
            Data TEXT,
            Titulo TEXT,
            Descricao TEXT,
            Responsavel TEXT,
            Arquivo TEXT,
            Miniatura TEXT,
            CriadoEm TEXT
        )
    """)

    colunas = {
        row[1] for row in c.execute("PRAGMA table_info(evolucao_obra)").fetchall()
    }
    migracoes = {
        "ObraID": "TEXT",
        "Obra": "TEXT",
        "Etapa": "TEXT",
        "Data": "TEXT",
        "Titulo": "TEXT",
        "Descricao": "TEXT",
        "Responsavel": "TEXT",
        "Arquivo": "TEXT",
        "Miniatura": "TEXT",
        "CriadoEm": "TEXT",
        "Origem": "TEXT",
        "DiarioID": "TEXT",
    }
    for coluna, tipo in migracoes.items():
        if coluna not in colunas:
            c.execute(f'ALTER TABLE evolucao_obra ADD COLUMN "{coluna}" {tipo}')

    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_evolucao_obra_data
        ON evolucao_obra (ObraID, Data DESC)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_evolucao_obra_etapa
        ON evolucao_obra (ObraID, Etapa)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_evolucao_diario
        ON evolucao_obra (ObraID, DiarioID)
    """)

    conn.commit()
    conn.close()


def criar_tabela_diario_obra():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS diario_obra (
            ID TEXT PRIMARY KEY,
            ObraID TEXT,
            Obra TEXT,
            Data TEXT,
            Etapa TEXT,
            Clima TEXT,
            Responsavel TEXT,
            Equipe TEXT,
            ServicosExecutados TEXT,
            Ocorrencias TEXT,
            Observacoes TEXT,
            ProgressoEtapa REAL,
            AtualizarCronograma INTEGER,
            CriarEvolucao INTEGER,
            CriadoEm TEXT,
            AtualizadoEm TEXT
        )
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_diario_obra_data
        ON diario_obra (ObraID, Data DESC)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_diario_obra_etapa
        ON diario_obra (ObraID, Etapa)
    """)
    conn.commit()
    conn.close()


def criar_tabela_listas_sistema():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS listas_sistema (
            ID TEXT PRIMARY KEY,
            Tipo TEXT,
            Nome TEXT,
            Ativo INTEGER DEFAULT 1,
            Ordem INTEGER,
            CriadoEm TEXT
        )
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_listas_sistema_tipo_nome
        ON listas_sistema (Tipo, Nome)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_listas_sistema_tipo_ativo
        ON listas_sistema (Tipo, Ativo, Ordem)
    """)
    conn.commit()
    conn.close()


def criar_tabela_produtos():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            ID TEXT PRIMARY KEY,
            Nome TEXT,
            Unidade TEXT,
            Categoria TEXT,
            Ativo INTEGER DEFAULT 1,
            CriadoEm TEXT
        )
    """)
    c.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_produtos_nome
        ON produtos (Nome COLLATE NOCASE)
    """)
    c.execute("""
        CREATE INDEX IF NOT EXISTS idx_produtos_ativo_nome
        ON produtos (Ativo, Nome)
    """)
    conn.commit()
    conn.close()


# ===============================
# 🔧 ATUALIZAÇÕES SEGURAS
# ===============================
def atualizar_lancamentos_fornecedor():
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute('ALTER TABLE lancamentos ADD COLUMN Fornecedor TEXT')
    except Exception:
        logging.debug("Coluna lancamentos.Fornecedor já existe ou não pôde ser criada.", exc_info=True)
    try:
        c.execute('ALTER TABLE lancamentos ADD COLUMN FornecedorID TEXT')
    except Exception:
        logging.debug("Coluna lancamentos.FornecedorID já existe ou não pôde ser criada.", exc_info=True)

    c.execute("""
        UPDATE lancamentos
        SET FornecedorID = (
            SELECT f.ID
            FROM fornecedores f
            WHERE lower(trim(f.Nome)) = lower(trim(
                COALESCE(NULLIF(lancamentos.Fornecedor, ''), lancamentos."Descrição")
            ))
            LIMIT 1
        )
        WHERE FornecedorID IS NULL OR FornecedorID = ''
    """)

    conn.commit()
    conn.close()


def atualizar_campos_financeiros():
    conn = get_connection()
    c = conn.cursor()

    for campo in ["Frete", "Desconto", "Imposto"]:
        try:
            c.execute(f'ALTER TABLE lancamentos ADD COLUMN {campo} REAL')
        except Exception:
            logging.debug(
                "Campo financeiro %s já existe ou não pôde ser criado.",
                campo,
                exc_info=True,
            )

    conn.commit()
    conn.close()


def atualizar_permissoes_usuario():
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN Permissoes TEXT')
    except Exception:
        logging.debug("Coluna usuarios.Permissoes j? existe ou n?o p?de ser criada.", exc_info=True)

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN Nome TEXT')
    except Exception:
        logging.debug("Coluna usuarios.Nome j? existe ou n?o p?de ser criada.", exc_info=True)

    conn.commit()
    conn.close()


def criar_indices_performance():
    conn = get_connection()
    try:
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_obra ON lancamentos(Obra)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_lancamentos_status ON lancamentos(Status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_insumos_nota ON insumos(NotaID)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_insumos_obra ON insumos(Obra)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_usuarios_usuario ON usuarios(Usuario)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cronograma_obra ON cronograma(ObraID)")

        tabelas = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        if "evolucao_obra" in tabelas:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evolucao_obra ON evolucao_obra(ObraID)")
        if "evolucao" in tabelas:
            conn.execute("CREATE INDEX IF NOT EXISTS idx_evolucao_obra_legacy ON evolucao(ObraID)")

        conn.commit()
    except Exception:
        logging.exception("Erro ao criar indices de performance.")
    finally:
        conn.close()


# ===============================
def inserir_materiais_base():
    conn = get_connection()
    c = conn.cursor()

    materiais = [
        ("1", "Cimento CP II", "saco", 38),
        ("2", "Cal hidratada", "saco", 32),
        ("3", "Areia média", "m3", 140),
        ("4", "Brita 1", "m3", 160),
        ("5", "Aço CA-50", "kg", 8.5),
    ]

    for m in materiais:
        c.execute("""
            INSERT OR IGNORE INTO materiais (ID, Material, Unidade, Preco)
            VALUES (?, ?, ?, ?)
        """, m)

    conn.commit()
    conn.close()


# ===============================
# 🚀 INICIALIZAÇÃO
# ===============================
def inicializar_banco():
    print("Inicializando banco...")

    criar_tabela_obras()
    criar_tabela_usuarios()
    criar_tabela_lancamentos()
    criar_tabela_insumos()
    criar_tabela_materiais()
    criar_tabela_fornecedores()
    criar_tabela_cronograma()
    criar_tabela_evolucao_obra()
    criar_tabela_listas_sistema()
    criar_tabela_produtos()
    criar_tabela_diario_obra()

    atualizar_lancamentos_fornecedor()
    atualizar_campos_financeiros()
    atualizar_permissoes_usuario()
    atualizar_recuperacao_senha()
    inserir_listas_sistema_iniciais()
    migrar_produtos_existentes()
    criar_indices_performance()

    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute("SELECT COUNT(*) FROM materiais")
        total = c.fetchone()[0]
    except Exception:
        logging.exception("Erro ao contar materiais base.")
        total = 0

    conn.close()

    if total == 0:
        inserir_materiais_base()

    print("Banco pronto")


def inserir_listas_sistema_iniciais():
    from services.listas import garantir_listas_iniciais

    garantir_listas_iniciais()


def migrar_produtos_existentes():
    from services.produtos import migrar_insumos_para_produtos

    migrar_insumos_para_produtos()

def atualizar_recuperacao_senha():
    conn = get_connection()
    c = conn.cursor()

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN TokenReset TEXT')
    except Exception:
        logging.debug("Coluna usuarios.TokenReset já existe ou não pôde ser criada.", exc_info=True)

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN TokenExpira TEXT')
    except Exception:
        logging.debug("Coluna usuarios.TokenExpira já existe ou não pôde ser criada.", exc_info=True)

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN Email TEXT')
    except Exception:
        logging.debug("Coluna usuarios.Email já existe ou não pôde ser criada.", exc_info=True)

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN Telefone TEXT')
    except Exception:
        logging.debug("Coluna usuarios.Telefone já existe ou não pôde ser criada.", exc_info=True)

    try:
        c.execute('ALTER TABLE usuarios ADD COLUMN TokenTentativas INTEGER DEFAULT 0')
    except Exception:
        logging.debug("Coluna usuarios.TokenTentativas já existe ou não pôde ser criada.", exc_info=True)

    c.execute("""
        CREATE TABLE IF NOT EXISTS auditoria_recuperacao_senha (
            ID TEXT PRIMARY KEY,
            Usuario TEXT,
            Identificador TEXT,
            Evento TEXT,
            DataHora TEXT,
            Detalhes TEXT
        )
    """)

    conn.commit()
    conn.close()
