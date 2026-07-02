import concurrent.futures
import streamlit as st

# ====================================================================
# 📦 IMPORTS DEL PROYECTO
# ====================================================================
from brain.scrapers.pccom import buscar_pccomponentes
from brain.scrapers.coolmod import buscar_coolmod
from brain.scrapers.amazon import buscar_amazon
from brain.scrapers.neobyte import buscar_neobyte

# Configuración de la página (Título en la pestaña del navegador y layout ancho)
st.set_page_config(page_title="Hardware Comparator Bot", layout="wide", page_icon="🖥️")

st.title("🖥️ Bot Comparador de Hardware en Tiempo Real")
st.markdown("Busca componentes en múltiples tiendas simultáneamente y encuentra el mejor precio de forma limpia.")

# ====================================================================
# 🎛️ BARRA LATERAL / PANEL DE CONTROL
# ====================================================================
st.sidebar.header("Filtros y Configuración")

# Input de texto en la web
producto_a_buscar = st.sidebar.text_input("🔎 ¿Qué producto quieres buscar?", placeholder="Ej. RTX 4060")

# Checkbox visual para activar el filtro de exclusión
excluir_equipos = st.sidebar.checkbox("✂️ Excluir PCs premontados y portátiles", value=True)

st.sidebar.markdown("---")
st.sidebar.info("Este bot realiza búsquedas en paralelo usando Playwright y aplica filtros automáticos de relevancia.")

# ====================================================================
# 🧠 MOTOR DE BÚSQUEDA (Adaptado para la Web)
# ====================================================================
def asegurar_navegador():
    """Descarga el binario ligero necesario justo antes de iniciar el scraping"""
    import subprocess
    import os
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/playwright"
    if not os.path.exists("/tmp/playwright"):
        subprocess.run(["python", "-m", "playwright", "install", "chromium"])

def orquestar_busqueda_web(producto, filtrar):
    asegurar_navegador()  # Aseguramos que el navegador esté listo antes de iniciar
    TIENDAS_ACTIVAS = [
        {"nombre": "PcComponentes", "funcion": buscar_pccomponentes},
        {"nombre": "Coolmod",       "funcion": buscar_coolmod},
        {"nombre": "Amazon",        "funcion": buscar_amazon},
        {"nombre": "Neobyte",       "funcion": buscar_neobyte},
    ]
    
    todos_los_resultados = []
    
    # Creamos un contenedor de texto dinámico para ir mostrando el progreso en la web
    log_status = st.empty()
    log_status.text("🚀 Iniciando búsqueda paralela en las tiendas...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(TIENDAS_ACTIVAS)) as executor:
        futuros = {
            executor.submit(tienda["funcion"], producto): tienda["nombre"] 
            for tienda in TIENDAS_ACTIVAS
        }
        
        for futuro in concurrent.futures.as_completed(futuros):
            nombre_tienda = futuros[futuro]
            try:
                resultados_tienda = futuro.result()
                if resultados_tienda:
                    todos_los_resultados.extend(resultados_tienda)
            except Exception as e:
                st.error(f"❌ Error crítico en {nombre_tienda}: {e}")

    # Aplicar el filtro si está activo
    if filtrar:
        palabras_bloqueadas = [
            "portátil", "laptop", "sobremesa", "desktop", "ordenador", 
            "pc gaming", "premontado", " workstation", "intel core", "amd ryzen"
        ]
        resultados_filtrados = []
        for prod in todos_los_resultados:
            nombre_minusculas = prod["nombre"].lower()
            if any(palabra in nombre_minusculas for palabra in palabras_bloqueadas):
                continue
            resultados_filtrados.append(prod)
        todos_los_resultados = resultados_filtrados

    log_status.empty() # Borramos el log de estado cuando termina
    return sorted(todos_los_resultados, key=lambda x: x['precio'])

# ====================================================================
# 🚀 ACCIÓN DE BÚSQUEDA
# ====================================================================
if st.sidebar.button("⚡ Ejecutar Comparación", type="primary"):
    if not producto_a_buscar.strip():
        st.warning("Por favor, introduce un nombre de producto válido.")
    else:
        # Añadimos un spinner de carga animado precioso en la web
        with st.spinner(f"Buscando '{producto_a_buscar}' en todas las tiendas..."):
            resultados = orquestar_busqueda_web(producto_a_buscar, excluir_equipos)
            
        if not resultados:
            st.error("No se encontraron resultados que coincidan con los criterios de búsqueda.")
        else:
            st.success(f"📊 ¡Búsqueda completada! Se han encontrado {len(resultados)} ofertas optimizadas.")
            
            # 🏆 Mostramos los resultados en un formato de tarjetas o bloques limpios
            st.subheader("🏆 TOP OFERTAS ENCONTRADAS (Ordenadas de menor a mayor precio)")
            
            for i, prod in enumerate(resultados[:10], start=1):
                # Creamos una caja visual para cada producto
                with st.container(border=True):
                    # Dividimos en columnas: Posición/Tienda, Nombre, Precio y Enlace
                    col1, col2, col3 = st.columns([1.5, 6, 2.5])
                    
                    with col1:
                        st.markdown(f"### #{i}")
                        st.caption(f"🏬 {prod['tienda']}")
                        
                    with col2:
                        st.markdown(f"**{prod['nombre']}**")
                        
                    with col3:
                        st.markdown(f"### {prod['precio']} €")
                        # Botón web real que redirige a la tienda en otra pestaña
                        st.link_button("🛒 Ir a la Oferta", prod['enlace'], use_container_width=True)