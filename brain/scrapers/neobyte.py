from playwright.sync_api import sync_playwright
import urllib.parse

def buscar_neobyte(producto):
    print(f"🔍 [Playwright] Buscando '{producto}' en Neobyte...")
    
    producto_url = urllib.parse.quote_plus(producto)
    url = f"https://www.neobyte.es/buscador?s={producto_url}"
    
    resultados = []
    
    with sync_playwright() as p:
        # Añadimos argumentos de camuflaje al navegador para evitar que detecte el modo oculto
        navegador = p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        
        # Le pasamos un perfil de usuario (User-Agent) totalmente real
        contexto = navegador.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-ES"
        )
        
        pagina = contexto.new_page()
        pagina.set_viewport_size({"width": 1280, "height": 800})
        
        try:
            # Navegamos y esperamos a que cargue la red por completo
            pagina.goto(url, wait_until="networkidle", timeout=20000)
            
            # Buscamos los bloques de producto usando clases genéricas y específicas
            tarjetas = pagina.query_selector_all('.product-miniature, [data-id-product], .product-description')
            
            nombres_procesados = set()
            
            for tarjeta in tarjetas:
                try:
                    # 1. Título
                    nombre_elem = tarjeta.query_selector('.product-title a') or tarjeta.query_selector('h3 a')
                    if not nombre_elem: continue
                    nombre = nombre_elem.inner_text().strip()
                    
                    if not nombre or nombre in nombres_procesados:
                        continue
                    
                    # 2. Precio
                    precio_elem = tarjeta.query_selector('.price') or tarjeta.query_selector('[class*="price"]')
                    if not precio_elem: continue
                    
                    texto_precio = precio_elem.inner_text().strip()
                    texto_precio = texto_precio.replace('€', '').replace('.', '').replace(',', '.').strip()
                    precio = float(texto_precio)
                    
                    # 3. Enlace
                    enlace = nombre_elem.get_attribute('href')
                    if not enlace:
                        enlace = url
                        
                    if precio > 0:
                        resultados.append({
                            "tienda": "Neobyte",
                            "nombre": nombre,
                            "precio": precio,
                            "enlace": enlace
                        })
                        nombres_procesados.add(nombre)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"❌ Error en Neobyte: {e}")
            
        contexto.close()
        navegador.close()
        
    return sorted(resultados, key=lambda x: x['precio'])