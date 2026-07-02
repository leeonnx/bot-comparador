from playwright.sync_api import sync_playwright
import urllib.parse

def buscar_pccomponentes(producto):
    print(f"🔍 [Playwright] Buscando '{producto}' en PcComponentes...")
    
    producto_url = urllib.parse.quote_plus(producto)
    url = f"https://www.pccomponentes.com/buscar/?query={producto_url}"
    
    resultados = []
    
    with sync_playwright() as p:
        # Modo headless blindado contra detección de automatización
        navegador = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        ) 
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        pagina = contexto.new_page()
        pagina.set_viewport_size({"width": 1280, "height": 1000})
        
        try:
            pagina.goto(url, wait_until="domcontentloaded", timeout=20000)
            pagina.wait_for_timeout(2000)
            
            # Clic automático en cookies si aparece
            if pagina.query_selector('button:has-text("Aceptar todas")'):
                pagina.click('button:has-text("Aceptar todas")')
                pagina.wait_for_timeout(500)
            
            # 🔥 SCROLL PROGRESIVO: Bajamos la página para activar el Lazy Load de PcComponentes
            for i in range(4):
                pagina.evaluate(f"window.scrollTo(0, {i * 1200});")
                pagina.wait_for_timeout(600)
            
            # Seleccionamos todas las tarjetas disponibles tras el scroll
            tarjetas = pagina.query_selector_all('div[class*="product-card"]')
            
            nombres_procesados = set()
            
            for tarjeta in tarjetas:
                try:
                    # 1. Extraer el nombre
                    nombre_elem = tarjeta.query_selector('strong') or tarjeta.query_selector('h3')
                    if not nombre_elem: continue
                    nombre = nombre_elem.inner_text().strip()
                    
                    if not nombre or nombre in nombres_procesados:
                        continue
                    
                    # FILTRO DE RELEVANCIA BÁSICO INTERNO (Asegurar que coincida con la búsqueda)
                    nombre_minusculas = nombre.lower()
                    palabras_busqueda = producto.lower().split()
                    if not all(palabra in nombre_minusculas for palabra in palabras_busqueda):
                        continue
                    
                    # 2. Extraer el precio
                    precio_elem = tarjeta.query_selector('span:has-text("€")') or tarjeta.query_selector('div:has-text("€")')
                    if not precio_elem: continue
                    
                    texto_precio = precio_elem.inner_text()
                    if '€' in texto_precio:
                        # Limpieza estricta del precio aislando el formato de PcCom
                        texto_precio = texto_precio.split('€')[0].strip()
                        texto_precio = texto_precio.replace('.', '').replace(',', '.')
                        precio = float(texto_precio)
                    else:
                        continue
                    
                    # 3. Extraer el enlace real
                    href = tarjeta.evaluate("""elem => {
                        if (elem.tagName === 'A') return elem.getAttribute('href');
                        let padreLink = elem.closest('a');
                        if (padreLink) return padreLink.getAttribute('href');
                        let hijoLink = elem.querySelector('a');
                        if (hijoLink) return hijoLink.getAttribute('href');
                        return null;
                    }""")
                    
                    if href:
                        enlace = href if href.startswith('http') else f"https://www.pccomponentes.com{href}"
                    else:
                        enlace = url
                    
                    if precio > 0:
                        resultados.append({
                            "tienda": "PcComponentes",
                            "nombre": nombre,
                            "precio": precio,
                            "enlace": enlace
                        })
                        nombres_procesados.add(nombre)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error en PcComponentes: {e}")
            
        contexto.close()
        navegador.close()
        
    return sorted(resultados, key=lambda x: x['precio'])

if __name__ == "__main__":
    lista_precios = buscar_pccomponentes("RTX 4060")
    print(f"\n📊 --- RESULTADOS EN PCCOMPONENTES ({len(lista_precios)} productos encontrados) ---")
    for prod in lista_precios:
        print(f"💰 {prod['precio']}€ | {prod['nombre']}")
        print(f"🔗 {prod['enlace']}\n" + "-"*40)