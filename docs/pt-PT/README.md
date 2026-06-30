# SQL Server Docker Manager

Aplicação desktop em Python/PySide6 para gerir backups, restores e consulta de bases SQL Server a correr em Docker.

## Idiomas disponíveis

- Português Portugal
- Português Brasil
- English
- Español
- Français

O idioma pode ser alterado em **Settings > Interface > Idioma**.

## Funcionalidades

- Restore de backups `.bak`;
- Backup de bases existentes;
- Consulta de bases SQL Server;
- Settings locais;
- Tema Dark Premium e Light Professional;
- Logs em tempo real;
- Password em sessão ou guardada localmente por opção do utilizador.

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

Por padrão, a password fica apenas em memória enquanto a aplicação está aberta.
Se o utilizador ativar a opção de guardar password, ela será guardada localmente por conta e risco do próprio utilizador.

## Documentação

- [Build](BUILD.md)
- [Manual](MANUAL.md)
