# SQL Server Docker Manager

Aplicación desktop en Python/PySide6 para gestionar copias, restauraciones y consulta de bases SQL Server en Docker.

## Idiomas disponibles

- Portugués Portugal
- Portugués Brasil
- Inglés
- Español
- Francés

El idioma se puede cambiar en **Settings > Interface > Idioma**.

## Funcionalidades

- Restaurar copias `.bak`;
- Crear copias de bases existentes;
- Consultar bases SQL Server;
- Ajustes locales;
- Temas Dark Premium y Light Professional;
- Logs en tiempo real;
- Contraseña en sesión o guardada localmente por elección explícita del usuario.

## Requisitos

- Python 3.10+ para modo desarrollo;
- Docker instalado;
- Contenedor SQL Server en ejecución;
- `sqlcmd` disponible dentro del contenedor;
- Permiso para ejecutar `docker`.

## Ejecutar en modo desarrollo

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

En Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Seguridad

Por defecto, la contraseña se mantiene solo en memoria mientras la aplicación está abierta.
Si el usuario activa guardar contraseña, se almacenará localmente bajo su propia responsabilidad.

## Documentación

- [Build](BUILD.md)
- [Manual](MANUAL.md)
