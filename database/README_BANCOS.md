# Bancos do DELTA Gestor

## `database/gestor_clean.db`

Banco modelo limpo para distribuição e instalador.

- Deve ficar versionado/incluído no instalador.
- Não deve ser usado para desenvolvimento.
- Não deve ser alterado em runtime.
- Mantém estrutura das tabelas, listas padrão e materiais base.
- Não deve conter usuários, obras, lançamentos, fornecedores, cronogramas, evolução ou diário.

## `data/gestor_dev.db`

Banco de desenvolvimento e testes locais.

- Usado por padrão quando `DELTA_GESTOR_MODE`/`DELTA_GESTOR_ENV` não indica produção.
- Ignorado pelo Git.
- Se não existir, é criado a partir de `database/gestor_clean.db`.

## `data/gestor.db`

Banco do cliente instalado em produção.

- Usado quando `DELTA_GESTOR_MODE=production` ou `DELTA_GESTOR_ENV=production`.
- Ignorado pelo Git.
- Nunca deve ser sobrescrito durante atualização.
- Se não existir na primeira instalação, é criado a partir de `database/gestor_clean.db`.

## Backups antigos

Arquivos `.db` soltos e fora de uso devem ficar em `backups_bancos_antigos/`.
