# Instalação do DELTA Gestor de Obras

## Bancos

- `database/gestor_clean.db`: modelo limpo incluído no instalador.
- `data/gestor_dev.db`: banco local de desenvolvimento. Não entra no instalador.
- `data/gestor.db`: banco do cliente em produção.

O launcher de produção define:

```text
DELTA_GESTOR_MODE=production
DELTA_GESTOR_ENV=production
DELTA_GESTOR_DB_PATH={pasta_instalada}\data\gestor.db
```

Se `data/gestor.db` não existir, o sistema cria uma cópia a partir de `database/gestor_clean.db`.

## Atualização

O instalador não inclui `data/gestor.db`, portanto não sobrescreve o banco do cliente.

Antes de alterar arquivos do sistema, o instalador faz backup automático quando encontra:

```text
{pasta_instalada}\data\gestor.db
```

O backup é salvo em:

```text
{pasta_instalada}\backups\gestor_YYYYMMDD_HHMMSS.db
```

As pastas abaixo são preservadas:

- `data`
- `uploads`
- `recibos`
- `logs`
- `backups`

## Build

Pré-requisitos:

- Python com dependências do `requirements.txt`
- PyInstaller
- Inno Setup 6

Comando:

```powershell
.\build_installer.ps1
```

Saídas esperadas:

- Build PyInstaller: `dist\DeltaGestor\`
- Instalador: `dist_installer\DELTA_Gestor_Setup.exe`

## Instalação limpa

1. Instalar o DELTA Gestor.
2. Abrir pelo atalho da Área de Trabalho ou Menu Iniciar.
3. O sistema cria `data/gestor.db` a partir de `database/gestor_clean.db`.
4. Como não existe ADMIN, abre a tela de Primeiro Acesso.
5. Criar o primeiro ADMIN.
6. Fazer login.
7. Cadastrar a primeira obra.

## Validações antes de distribuir

- Confirmar que `database/gestor_clean.db` está sem usuários, obras e lançamentos.
- Confirmar que `data/gestor_dev.db` não está dentro de `dist\DeltaGestor`.
- Confirmar que `backups_bancos_antigos` não está dentro de `dist\DeltaGestor`.
- Confirmar que atualização preserva `data/gestor.db`.
- Confirmar que o backup de atualização é criado em `backups`.
- Confirmar que o backup manual gera um `.zip` valido em `backups`.

## Backups do sistema

Os backups do DELTA Gestor ficam em:

```text
{pasta_instalada}\backups
```

A tela fica em:

```text
Administracao > Backup
```

O backup manual gera um arquivo `.zip` contendo:

- banco atual em `data/gestor.db` na producao;
- banco atual em `data/gestor_dev.db` no desenvolvimento;
- pasta `uploads`, quando existir;
- pasta `recibos`, quando existir;
- pasta `logs`, quando existir;
- `.streamlit/secrets.toml`, quando existir.

Nome padrao:

```text
Backup_DELTA_Gestor_YYYY-MM-DD_HH-MM-SS.zip
```

Para restaurar um backup:

1. Acesse `Administracao > Backup`.
2. Selecione ou envie um arquivo `.zip` valido.
3. Digite `RESTAURAR` para confirmar.
4. O sistema cria antes um backup automatico do estado atual:

```text
Backup_PRE_RESTAURACAO_YYYY-MM-DD_HH-MM-SS.zip
```

5. Reinicie o DELTA Gestor apos a restauracao.

Recomendacao comercial: copie periodicamente os arquivos da pasta `backups` para um pendrive, HD externo ou armazenamento em nuvem. Isso protege o cliente contra falha de disco, formatacao da maquina ou perda fisica do computador.

O sistema tambem tenta criar um backup automatico diario ao iniciar. Caso ja exista backup automatico no dia, ele nao duplica o arquivo. Sao mantidos no maximo os ultimos 30 backups automaticos.
