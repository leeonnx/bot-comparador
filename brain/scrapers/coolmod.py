from playwright.sync_api import sync_playwright
import urllib.parse

def buscar_coolmod(producto):
    print(f"🔍 [Playwright] Buscando '{producto}' en Coolmod (Doofinder)...")
    
    producto_url = urllib.parse.quote_plus(producto)
    url = f"https://www.coolmod.com/#01cc/fullscreen/m=and&q={producto_url}"
    
    resultados = []
    
    with sync_playwright() as p:
        # Modo oculto optimizado para rendimiento paralelo
        navegador = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        ) 
        pagina = navegador.new_page()
        pagina.set_viewport_size({"width": 1280, "height": 900})
        
        try:
            # 1. Cargamos rápido sin esperar a que toda la publicidad de la red termine
            pagina.goto(url, wait_until="domcontentloaded", timeout=20000)
            
            # 2. Espera fija de 4 segundos para que los scripts de Doofinder se despierten
            pagina.wait_for_timeout(4000) 
            
            # 🔥 SCROLL INTERNO: Bajamos para despertar más productos
            for _ in range(2):
                pagina.evaluate("window.scrollTo(0, document.body.scrollHeight);")
                pagina.evaluate("let box = document.querySelector('.df-fullscreen, [id*=\"doofinder\"]'); if(box) box.scrollTo(0, box.scrollHeight);")
                pagina.wait_for_timeout(500)
            
            # 3. Capturamos directamente sin lanzar excepciones si tarda de más
            tarjetas = pagina.query_selector_all('div[class*="df-card"], .df-result, div[data-id], [class*="product"]')
            
            nombres_procesados = set()
            
            for tarjeta in tarjetas:
                try:
                    # Extraer el nombre
                    nombre_elem = (tarjeta.query_selector('[class*="title"]') or 
                                   tarjeta.query_selector('[class*="name"]') or 
                                   tarjeta.query_selector('h3') or
                                   tarjeta.query_selector('h4'))
                                   
                    if not nombre_elem: continue
                    nombre = nombre_elem.inner_text().strip()
                    
                    if not nombre or nombre in nombres_procesados:
                        continue

                    # FILTRO DE RELEVANCIA BÁSICO
                    nombre_minusculas = nombre.lower()
                    palabras_busqueda = producto.lower().split()
                    if not all(palabra in nombre_minusculas for palabra in palabras_busqueda):
                        continue
                        
                    # Extraer el precio
                    precio_elem = tarjeta.query_selector('[class*="price"]') or tarjeta.query_selector('span:has-text("€")') or tarjeta.query_selector('div:has-text("€")')
                    if not precio_elem: continue
                    
                    texto_precio = precio_elem.inner_text()
                    if '€' in texto_precio:
                        if '\n' in texto_precio:
                            texto_precio = texto_precio.split('\n')[-1]
                        
                        texto_precio = ''.join(c for c in texto_precio if c.isdigit() or c in [',', '.'])
                        texto_precio = texto_precio.replace('.', '').replace(',', '.')
                        precio = float(texto_precio)
                    else:
                        continue
                        
                    # Extraer el enlace de la tarjeta
                    href = tarjeta.evaluate("""elem => {
                        if (elem.tagName === 'A') return elem.getAttribute('href');
                        let padre = elem.closest('a');
                        if (padre) return padre.getAttribute('href');
                        let hijo = elem.querySelector('a');
                        if (hijo) return hijo.getAttribute('href');
                        return null;
                    }""")
                    
                    enlace = ""
                    if href:
                        enlace = href if href.startswith('http') else f"https://www.coolmod.com{href}"
                    else:
                        enlace = url
                    
                    if precio > 0:
                        resultados.append({
                            "tienda": "Coolmod",
                            "nombre": nombre,
                            "precio": precio,
                            "enlace": enlace
                        })
                        nombres_procesados.add(nombre)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error en Coolmod: {e}")
            
        navegador.close()
        
    return sorted(resultados, key=lambda x: x['precio'])

if __name__ == "__main__":
    # Test local sin límites de recorte para comprobar volumen
    lista_precios = buscar_coolmod("RTX 4060")
    print(f"\n📊 --- RESULTADOS EN COOLMOD ({len(lista_precios)} productos encontrados) ---")
    for prod in lista_precios:
        print(f"💰 {prod['precio']}€ | {prod['nombre']}")
        print(f"🔗 {prod['enlace']}\n" + "-"*40)