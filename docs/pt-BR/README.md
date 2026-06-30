# SQL Server Docker Manager

Aplicação desktop em Python/PySide6 para gerenciar backups, restores e consulta de bancos SQL Server rodando em Docker.

## Idiomas disponíveis

- Português Portugal
- Português Brasil
- English
- Español
- Français

O idioma pode ser alterado em **Settings > Interface > Idioma**.

## Funcionalidades

- Restore de backups `.bak`;
- Backup de bancos existentes;
- Consulta de bancos SQL Server;
- Configurações locais;
- Tema Dark Premium e Light Professional;
- Logs em tempo real;
- Senha em sessão ou salva localmente por opção do usuário.

## Requisitos

- Python 3.10+ para modo desenvolvimento;
- Docker instalado;
- Container SQL Server em execução;
- `sqlcmd` disponível dentro do container;
- Permissão para executar `docker`.

## Executar em desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

No Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Segurança

Por padrão, a senha fica apenas em memória enquanto a aplicação está aberta.
Se o usuário ativar a opção de salvar senha, ela será armazenada localmente por conta e risco do próprio usuário.

## Documentação

- [Build](BUILD.md)
- [Manual](MANUAL.md)
