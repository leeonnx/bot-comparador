import os
import sys
import subprocess
import concurrent.futures
import streamlit as st

# 🔥 CONFIGURACIÓN GLOBAL CRÍTICA: Debe ir ANTES de cualquier import de scrapers
# Usamos un directorio dentro del proyecto donde SÍ tenemos permisos de escritura
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), ".playwright")

# 📦 IMPORTS DEL PROYECTO
from brain.scrapers.pccom import buscar_pccomponentes
from brain.scrapers.coolmod import buscar_coolmod
from brain.scrapers.amazon import buscar_amazon
from brain.scrapers.neobyte import buscar_neobyte

# Configuración de la página
st.set_page_config(page_title="Hardware Comparator Bot", layout="wide", page_icon="🖥️")

st.title("🖥️ Bot Comparador de Hardware en Tiempo Real")

def asegurar_navegador():
    """Instala el navegador solo si no existe en nuestra carpeta local .playwright"""
    if not os.path.exists(os.environ["PLAYWRIGHT_BROWSERS_PATH"]):
        with st.spinner("🔧 Descargando navegador (primera vez)..."):
            try:
                # Forzamos la instalación de chromium en nuestra ruta definida
                subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
            except Exception as e:
                st.error(f"Error al preparar el navegador: {e}")
                st.stop()

# ====================================================================
# MOTOR DE BÚSQUEDA
# ====================================================================
def orquestar_busqueda_web(producto, filtrar):
    asegurar_navegador() 
    
    TIENDAS_ACTIVAS = [
        {"nombre": "PcComponentes", "funcion": buscar_pccomponentes},
        {"nombre": "Coolmod",       "funcion": buscar_coolmod},
        {"nombre": "Amazon",        "funcion": buscar_amazon},
        {"nombre": "Neobyte",       "funcion": buscar_neobyte},
    ]
    
    todos_los_resultados = []
    log_status = st.empty()
    log_status.text("🚀 Iniciando búsqueda paralela...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TIENDAS_ACTIVAS)) as executor:
        futuros = {executor.submit(t["funcion"], producto): t["nombre"] for t in TIENDAS_ACTIVAS}
        for futuro in concurrent.futures.as_completed(futuros):
            try:
                res = futuro.result()
                if res: todos_los_resultados.extend(res)
            except Exception as e:
                st.error(f"Error en {futuros[futuro]}: {e}")

    # Filtrado
    if filtrar:
        bloqueadas = ["portátil", "laptop", "sobremesa", "desktop", "ordenador", "pc gaming", "premontado"]
        todos_los_resultados = [p for p in todos_los_resultados if not any(b in p["nombre"].lower() for b in bloqueadas)]

    log_status.empty()
    return sorted(todos_los_resultados, key=lambda x: x['precio'])

# UI principal
producto_a_buscar = st.sidebar.text_input("🔎 ¿Qué producto buscas?", placeholder="Ej. RTX 4060")
excluir_equipos = st.sidebar.checkbox("✂️ Excluir PCs premontados", value=True)

if st.sidebar.button("⚡ Ejecutar Comparación", type="primary"):
    if not producto_a_buscar.strip():
        st.warning("Introduce un producto.")
    else:
        with st.spinner("Buscando..."):
            resultados = orquestar_busqueda_web(producto_a_buscar, excluir_equipos)
            
        if not resultados:
            st.error("No se encontraron resultados.")
        else:
            for i, prod in enumerate(resultados[:10], start=1):
                with st.container(border=True):
                    col1, col2, col3 = st.columns([1, 6, 2])
                    col1.markdown(f"### #{i}")
                    col2.markdown(f"**{prod['nombre']}**")
                    col3.markdown(f"### {prod['precio']} €")
                    col3.link_button("Ir a la oferta", prod['enlace'])