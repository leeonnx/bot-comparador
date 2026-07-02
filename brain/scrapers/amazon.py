from playwright.sync_api import sync_playwright
import urllib.parse

def buscar_amazon(producto):
    print(f"🔍 [Playwright] Buscando '{producto}' en Amazon...")
    
    producto_url = urllib.parse.quote_plus(producto)
    url = f"https://www.amazon.es/s?k={producto_url}"
    
    resultados = []
    
    with sync_playwright() as p:
        # Volvemos a Headless=True para rendimiento en paralelo, camuflado
        navegador = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        pagina = context = contexto.new_page()
        pagina.set_viewport_size({"width": 1280, "height": 1000})
        
        try:
            pagina.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # 🔥 TRUCO MAESTRO: Forzamos scroll progresivo hacia abajo para despertar el Lazy Load
            # Esto hará que Amazon cargue las 30-40 tarjetas de la primera página
            for i in range(4):
                pagina.evaluate(f"window.scrollTo(0, {i * 1000});")
                pagina.wait_for_timeout(600)
            
            # Capturamos todas las tarjetas disponibles ahora que la página cargó completa
            tarjetas = pagina.query_selector_all('div[data-component-type="s-search-result"]')
            
            nombres_procesados = set()
            
            for tarjeta in tarjetas:
                try:
                    # 1. Extraer el nombre
                    nombre_elem = tarjeta.query_selector('h2 a span') or tarjeta.query_selector('h2')
                    if not nombre_elem: continue
                    nombre = nombre_elem.inner_text().strip()
                    
                    if not nombre or nombre in nombres_procesados:
                        continue
                        
                    # FILTRO DE RELEVANCIA
                    nombre_minusculas = nombre.lower()
                    palabras_busqueda = producto.lower().split()
                    
                    if not all(palabra in nombre_minusculas for palabra in palabras_busqueda):
                        continue
                        
                    # Filtro de accesorios
                    palabras_prohibidas = ["cable", "ventilador", "extensor", "soporte", "riser", "manga", "adaptador", "hub", "caja", "funda", "bolsa"]
                    if any(prohibida in nombre_minusculas for prohibida in palabras_prohibidas):
                        continue
                    
                    # 2. Extraer el precio entero y fraccionado
                    precio_entero_elem = tarjeta.query_selector('.a-price-whole')
                    if not precio_entero_elem: continue
                    
                    texto_entero = precio_entero_elem.inner_text().strip().replace(',', '').replace('.', '').replace('\n', '')
                    
                    fraccion_elem = tarjeta.query_selector('.a-price-fraction')
                    texto_fraccion = fraccion_elem.inner_text().strip() if fraccion_elem else "00"
                    
                    precio = float(f"{texto_entero}.{texto_fraccion}")
                    
                    # 3. Extraer el enlace REAL (Selector Ultra-Blindado)
                    href = tarjeta.evaluate("""elem => {
                        let link1 = elem.querySelector('h2 a') || elem.querySelector('a[href*="/dp/"]');
                        if (link1 && link1.getAttribute('href')) return link1.getAttribute('href');
                        
                        let link2 = elem.querySelector('a.a-link-normal');
                        if (link2 && link2.getAttribute('href')) return link2.getAttribute('href');
                        
                        let todosLosLinks = elem.querySelectorAll('a');
                        for (let l of todosLosLinks) {
                            let url = l.getAttribute('href');
                            if (url && (url.includes('/dp/') || url.includes('/gp/product/'))) {
                                return url;
                            }
                        }
                        return null;
                    }""")
                    
                    enlace = ""
                    if href:
                        href_limpio = href.split('/ref=')[0]
                        enlace = href_limpio if href_limpio.startswith('http') else f"https://www.amazon.es{href_limpio}"
                    else:
                        enlace = url
                    
                    if precio > 0:
                        resultados.append({
                            "tienda": "Amazon",
                            "nombre": nombre,
                            "precio": precio,
                            "enlace": enlace
                        })
                        nombres_procesados.add(nombre)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error en Amazon: {e}")
            
        contexto.close()
        navegador.close()
        
    # Devolvemos TODO lo que haya pescado sin límites duros de recortes rápidos
    return sorted(resultados, key=lambda x: x['precio'])

if __name__ == "__main__":
    # Test individual: Ahora quitamos el límite en el print para ver cuántas pesca de verdad
    lista_precios = buscar_amazon("RTX 4060")
    
    print(f"\n📊 --- RESULTADOS EN AMAZON ({len(lista_precios)} productos encontrados) ---")
    for prod in lista_precios:
        print(f"💰 {prod['precio']}€ | {prod['nombre']}")
        print(f"🔗 {prod['enlace']}\n" + "-"*40)