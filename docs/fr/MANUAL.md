# Manuel d’Utilisation

## Première étape : Paramètres

Ouvrez **Settings** et configurez :

- Conteneur par défaut;
- Utilisateur SQL;
- Mot de passe;
- Dossier des sauvegardes;
- Dossier des données;
- Langue;
- Thème.

Cliquez ensuite sur **Tester la connexion**.

## Databases

Utilisez ce menu pour consulter les bases disponibles dans le conteneur configuré.

1. Ouvrez **Databases**.
2. Cliquez sur **Actualiser les bases**.
3. Vérifiez nom, état, recovery, collation, compatibilité et taille.

## Backup

1. Ouvrez **Backup**.
2. Cliquez sur **Actualiser les bases**.
3. Choisissez la base source.
4. Générez ou saisissez le nom du fichier `.bak`.
5. Cliquez sur **Créer la sauvegarde**.
6. Suivez les logs.

La sauvegarde est créée dans le dossier configuré, généralement `/var/opt/mssql/backup`.

## Restore

1. Ouvrez **Restore**.
2. Cliquez sur **Actualiser les sauvegardes**.
3. Choisissez le `.bak`.
4. Saisissez la base cible.
5. Cliquez sur **Restaurer la sauvegarde**.
6. Confirmez si la base cible existe déjà.

Pour tester en sécurité, restaurez avec un autre nom, par exemple `MaBase_Restored`.

## Logs

La zone de logs affiche la progression et les erreurs techniques. Utilisez **Copier le log** pour tout copier.

## Sécurité

Utilisez avec prudence en production. La confirmation d’écrasement évite de remplacer une base réelle par erreur.
