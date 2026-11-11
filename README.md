# 100%LIFE

Aplicación local en Streamlit para organizar actividades y hábitos de estudiantes generales y atletas. Usa SQLite; no requiere servicios externos ni datos simulados.

Incluye cuentas separadas, panel principal con calendario mensual interactivo, resumen y cierre de pendientes, recordatorios de fechas e hidratación, vaso de agua animado, perfil configurable, entrenamiento con orientación de recuperación y nutrición, hidratación en mililitros y seguimiento histórico.

Los recordatorios aparecen dentro de la aplicación mientras está abierta. Las actividades se muestran cuando comienzan o vencen en las siguientes 24 horas; la hidratación se recuerda cuando faltan 500 ml o más para la meta diaria.

## Instalar y ejecutar en openSUSE

Se requiere Python 3.10 o posterior (el Streamlit actual ya no admite Python 3.6).

```bash
cd /home/hector/tec/prepa/vibeCoding/pruebas/santiago/100-Life
sudo zypper install python311 python311-pip python311-devel
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
export LIFE_DB_PATH="$PWD/data/life.db"
python -c "from src.db import init_db; init_db()"
streamlit run main.py
```

Abre la dirección local mostrada por Streamlit. `LIFE_DB_PATH` es opcional; por defecto se usa `data/life.db`. Las horas se guardan como hora local del equipo, sin conversiones silenciosas.

## Pruebas

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
```

SQLite es apropiado para uso local o de baja concurrencia. Para un despliegue público con alta concurrencia conviene usar HTTPS y una base de datos de servidor.
