# Manual de Uso

## Primeiro passo: Settings

Abra **Settings** e configure:

- Container padrão;
- Usuário SQL;
- Senha;
- Diretório de backups;
- Diretório de dados;
- Idioma;
- Tema.

Depois clique em **Testar conexão**.

## Databases

Use este menu para consultar os bancos disponíveis no container configurado.

1. Abra **Databases**.
2. Clique em **Atualizar bases**.
3. Veja nome, estado, recovery, collation, compatibilidade e tamanho.

## Backup

1. Abra **Backup**.
2. Clique em **Atualizar bases**.
3. Escolha o banco origem.
4. Gere ou informe o nome do `.bak`.
5. Clique em **Fazer backup**.
6. Acompanhe os logs.

O backup é criado no diretório configurado, normalmente `/var/opt/mssql/backup`.

## Restore

1. Abra **Restore**.
2. Clique em **Atualizar backups**.
3. Escolha o `.bak`.
4. Informe o banco destino.
5. Clique em **Restaurar backup**.
6. Confirme caso o banco destino já exista.

Para testar com segurança, restaure com outro nome, por exemplo `MeuBanco_Restored`.

## Logs

A área de logs mostra o progresso e erros técnicos. Use **Copiar log** para copiar tudo.

## Segurança

Use com cuidado em produção. Confirmar sobrescrita evita restaurar por cima de um banco real sem querer.
