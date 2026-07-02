import concurrent.futures
from brain.scrapers.pccom import buscar_pccomponentes
from brain.scrapers.coolmod import buscar_coolmod
from brain.scrapers.amazon import buscar_amazon
from brain.scrapers.neobyte import buscar_neobyte

def orquestar_busqueda(producto, excluir_equipos):
    print(f"\n🚀 Iniciando búsqueda paralela para: '{producto}'...")
    
    TIENDAS_ACTIVAS = [
        {"nombre": "PcComponentes", "funcion": buscar_pccomponentes},
        {"nombre": "Coolmod",       "funcion": buscar_coolmod},
        {"nombre": "Amazon",        "funcion": buscar_amazon},
        {"nombre": "Neobyte",       "funcion": buscar_neobyte},
    ]
    
    todos_los_resultados = []
    
    # Ejecución en paralelo de los scrapers
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
                    print(f"✅ {nombre_tienda} finalizado con éxito ({len(resultados_tienda)} productos).")
                else:
                    print(f"⚠️ {nombre_tienda} no devolvió ningún resultado.")
            except Exception as e:
                print(f"❌ Error crítico en {nombre_tienda}: {e}")

    # ====================================================================
    # 🧹 FILTRO EXTRA: Excluir Portátiles y PCs Premontados
    # ====================================================================
    if excluir_equipos:
        palabras_bloqueadas = [
            "portátil", "laptop", "sobremesa", "desktop", "ordenador", 
            "pc gaming", "premontado", " workstation", "intel core", "amd ryzen"
        ]
        resultados_filtrados = []
        
        for prod in todos_los_resultados:
            nombre_minusculas = prod["nombre"].lower()
            # Si el producto contiene alguna palabra de la lista negra, lo saltamos
            if any(palabra in nombre_minusculas for palabra in palabras_bloqueadas):
                continue
            resultados_filtrados.append(prod)
            
        print(f"✂️ Filtro activado: Se han descartado {len(todos_los_resultados) - len(resultados_filtrados)} PCs/Portátiles.")
        todos_los_resultados = resultados_filtrados

    # Ordenamos la lista unificada final
    resultados_ordenados = sorted(todos_los_resultados, key=lambda x: x['precio'])
    return resultados_ordenados

if __name__ == "__main__":
    # 1. Entrada de usuario
    producto_a_buscar = input("🔎 ¿Qué componente o producto quieres comparar hoy?: ")
    
    if producto_a_buscar.strip():
        # 2. Preguntamos por el filtro (S/N)
        filtro_input = input("🖥️ ¿Deseas EXCLUIR PCs premontados y portátiles de la lista? (s/n): ").strip().lower()
        excluir = True if filtro_input == 's' else False
        
        resultados = orquestar_busqueda(producto_a_buscar, excluir)
        
        # 3. Imprimir el Podio de Precios
        print("\n🏆 ================== TOP OFERTAS ENCONTRADAS ==================")
        if not resultados:
            print("No se encontraron resultados que coincidan con los filtros.")
        else:
            for i, prod in enumerate(resultados[:10], start=1):
                print(f"{i}. [🏬 {prod['tienda']}] 💰 {prod['precio']}€")
                print(f"   📦 {prod['nombre']}")
                print(f"   🔗 {prod['enlace']}")
                print("-" * 65)
    else:
        print("Búsqueda cancelada.")