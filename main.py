# Genera el punto de principal para una aplicación interactiva en Streamlit para el proyecto "100%LIFE".
# Requisitos y funcionalidades:
# 1. Configurar la página con st.set_page_config (título "100%LIFE", icono de deporte/salud, layout "wide").
# 2. Inicializar st.session_state para controlar el estado del usuario ('authenticated', 'user_data', 'page').
# 3. Implementar un menú de navegación en la barra lateral (sidebar) o mediante st.navigation que cambie entre las páginas:
#    - 'Login/Registro' (llama a views.login_page)
#    - 'Onboarding' (llama a views.onboarding_page)
#    - 'Dashboard' (llama a views.dashboard_page)
#    - 'Recomendaciones' (llama a views.recommendations_page)
# 4. Manejo de Casos Borde:
#    - Si el usuario no está autenticado, redirigir automáticamente a la página de 'Login/Registro'.
#    - Si está autenticado pero no ha completado sus datos iniciales (medidas/horarios), redirigir a 'Onboarding'.
#    - Manejar la ausencia de llaves en st.session_state inicializándolas de forma segura con valores predeterminados.
# 5. Incluir docstrings generales al inicio y comentarios detallados en español en cada bloque de control.

"""
Punto de entrada principal para la aplicación interactiva "100%LIFE" en Streamlit.

Este módulo se encarga de la configuración inicial de la interfaz, la gestión del
estado global de la sesión (st.session_state), el control de acceso y redirecciones
según el estado de autenticación/onboarding del usuario, y la orquestación de la navegación.
"""

import streamlit as st

# Importación de vistas desde el módulo 'views'
from views.login_page import render_login_page
from views.onboarding_page import render_onboarding_page
from views.dashboard_page import render_dashboard_page
from views.recommendations_page import render_recommendations_page


def init_session_state() -> None:
    """
    Inicializa de manera segura las llaves necesarias en st.session_state
    si no existen previamente, evitando errores por llaves ausentes (KeyError).
    """
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False

    if 'user_data' not in st.session_state:
        st.session_state['user_data'] = None

    if 'page' not in st.session_state:
        st.session_state['page'] = 'Login/Registro'


def check_navigation_rules() -> str:
    """
    Evalúa el estado actual de la sesión y aplica las reglas de redirección.

    Retorna:
        str: La clave de la página a la que el usuario tiene permitido acceder.
    """
    is_authenticated = st.session_state.get('authenticated', False)
    user_data = st.session_state.get('user_data', None)

    # Caso borde 1: Usuario no autenticado -> Forzar redirección a Login/Registro
    if not is_authenticated:
        return 'Login/Registro'

    # Caso borde 2: Usuario autenticado pero sin completar el perfil (medidas/horarios) -> Redirigir a Onboarding
    profile_completed = False
    if isinstance(user_data, dict):
        has_measures = bool(user_data.get('measures'))
        has_schedule = bool(user_data.get('schedule'))
        profile_completed = has_measures and has_schedule

    if not profile_completed:
        return 'Onboarding'

    # Si está autenticado y completó onboarding, permitir la página seleccionada
    return st.session_state.get('page', 'Dashboard')


def main() -> None:
    """
    Función principal que configura la aplicación, controla el menú lateral
    y renderiza la vista correspondiente.
    """
    # 1. Configuración global de la página
    st.set_page_config(
        page_title="100%LIFE",
        page_icon="⚽",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. Inicializar estado de la sesión
    init_session_state()

    # 3. Determinar la página válida a mostrar según las reglas de negocio
    allowed_page = check_navigation_rules()

    # 4. Construcción de la barra lateral (sidebar) para navegación
    st.sidebar.title("100%LIFE 🏃‍♂️")

    if st.session_state['authenticated']:
        # Mostrar información básica del usuario en la barra lateral
        user_name = st.session_state['user_data'].get('username', 'Atleta') if st.session_state['user_data'] else 'Atleta'
        st.sidebar.write(f"Bienvenido, **{user_name}**")
        st.sidebar.markdown("---")

        # Opciones de menú disponibles para usuarios totalmente autenticados y configurados
        menu_options = ['Dashboard', 'Recomendaciones', 'Onboarding']
        
        # Ajustar el índice seleccionado de forma segura
        current_index = menu_options.index(allowed_page) if allowed_page in menu_options else 0

        selected_page = st.sidebar.radio(
            "Navegación",
            options=menu_options,
            index=current_index
        )
        st.session_state['page'] = selected_page

        # Botón para cerrar sesión
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state['authenticated'] = False
            st.session_state['user_data'] = None
            st.session_state['page'] = 'Login/Registro'
            st.rerun()
    else:
        st.sidebar.info("Por favor, inicia sesión o regístrate para continuar.")
        st.session_state['page'] = 'Login/Registro'

    # 5. Enrutamiento y renderizado de la vista correspondiente
    target_page = st.session_state['page'] if st.session_state['authenticated'] else allowed_page

    if target_page == 'Login/Registro':
        render_login_page()
    elif target_page == 'Onboarding':
        render_onboarding_page()
    elif target_page == 'Dashboard':
        render_dashboard_page()
    elif target_page == 'Recomendaciones':
        render_recommendations_page()
    else:
        # Manejo de fallback para páginas desconocidas
        st.error("La página solicitada no existe. Redirigiendo...")
        render_login_page()


if __name__ == '__main__':
    main()