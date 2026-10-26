import streamlit as st
import itertools
from collections import Counter
import time

# ==========================================
# 1. LÓGICA MATEMÁTICA
# ==========================================
E12 = [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2]
E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 
       3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]

def generar_valores_comerciales(serie, max_decadas=6):
    valores = []
    for decada in range(max_decadas):
        for valor_base in serie:
            valores.append(round(valor_base * (10 ** decada), 2))
    return sorted(valores)

def obtener_lista_resistencias(tolerancia):
    return generar_valores_comerciales(E12) if tolerancia >= 10 else generar_valores_comerciales(E24)

def _topologias_3r(a, b, c):
    opciones = {}
    for sola, p1, p2 in [(a, b, c), (b, a, c), (c, a, b)]:
        den = p1 + p2 + sola
        if den > 0:
            v = (p1 + p2) * sola / den
            opciones[f"({p1:g} + {p2:g}) || {sola:g}"] = ('Serie-Paralelo', v)
        if p1 + p2 > 0:
            v = p1 * p2 / (p1 + p2) + sola
            opciones[f"({p1:g} || {p2:g}) + {sola:g}"] = ('Paralelo-Serie', v)
    return [(t, v, e) for e, (t, v) in opciones.items()]

def encontrar_mejores_combinaciones(target, resistencias, tolerancia_pct):
    resultados = []
    for r in range(1, 4):
        for combo in itertools.combinations_with_replacement(resistencias, r):
            v_serie = sum(combo)
            err_serie = abs(v_serie - target) / target * 100
            if err_serie <= tolerancia_pct:
                resultados.append({'tipo': 'Serie', 'expresion': ' + '.join(f"{x:g}" for x in combo), 
                                   'combinacion': combo, 'valor_eq': round(v_serie, 2), 'error': round(err_serie, 3), 'n': r})
            
            if r > 1:
                v_paralelo = 1 / sum(1/x for x in combo)
                err_paralelo = abs(v_paralelo - target) / target * 100
                if err_paralelo <= tolerancia_pct:
                    resultados.append({'tipo': 'Paralelo', 'expresion': ' || '.join(f"{x:g}" for x in combo), 
                                       'combinacion': combo, 'valor_eq': round(v_paralelo, 2), 'error': round(err_paralelo, 3), 'n': r})
            
            if r == 3:
                for tipo, v_mixta, expr in _topologias_3r(*combo):
                    err_mixta = abs(v_mixta - target) / target * 100
                    if err_mixta <= tolerancia_pct:
                        resultados.append({'tipo': tipo, 'expresion': expr, 'combinacion': combo, 
                                           'valor_eq': round(v_mixta, 2), 'error': round(err_mixta, 3), 'n': r})

    vistos, unicos = set(), []
    for r in resultados:
        k = (r['expresion'], r['valor_eq'])
        if k not in vistos:
            vistos.add(k)
            unicos.append(r)
    return sorted(unicos, key=lambda x: (x['error'], x['n']))

def obtener_etiqueta_resistor(value, tol):
    color_map = {0: '#000000', 1: '#8B4513', 2: '#FF0000', 3: '#FFA500', 
                 4: '#FFFF00', 5: '#008000', 6: '#0000FF', 7: '#800080', 
                 8: '#808080', 9: '#FFFFFF'}
    mult_map = {-2: '#C0C0C0', -1: '#FFD700', 0: '#000000', 1: '#8B4513', 
                2: '#FF0000', 3: '#FFA500', 4: '#FFFF00', 5: '#008000', 6: '#0000FF'}
    
    if tol <= 1: ct = '#8B4513'
    elif tol <= 2: ct = '#FF0000'
    elif tol <= 5: ct = '#FFD700'
    else: ct = '#C0C0C0'
        
    s = f"{value:.2e}" 
    parts = s.split('e')
    num = float(parts[0]) 
    exp = int(parts[1])   
    
    d1 = int(num)
    d2 = int(round((num - d1) * 10))
    if d2 == 10:
        d1 += 1
        d2 = 0
        
    m = exp - 1
    
    c1 = color_map.get(d1, '#000000')
    c2 = color_map.get(d2, '#000000')
    cm = mult_map.get(m, '#000000')
    
    return f"""
    <div style="display:inline-flex; align-items:center; background:#F5DEB3; padding:4px 10px; border-radius:8px; border:1px solid #D2B48C; margin-right:10px; margin-top: 5px; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
        <span style="margin-right:10px; color:#2C3E50; font-weight:bold; font-family: monospace; font-size:15px;">{value:g}Ω</span>
        <div style="width:8px; height:22px; background:{c1}; margin:0 2px; border: 1px solid rgba(0,0,0,0.3);"></div>
        <div style="width:8px; height:22px; background:{c2}; margin:0 2px; border: 1px solid rgba(0,0,0,0.3);"></div>
        <div style="width:8px; height:22px; background:{cm}; margin:0 2px; border: 1px solid rgba(0,0,0,0.3);"></div>
        <div style="width:15px; height:22px;"></div>
        <div style="width:8px; height:22px; background:{ct}; margin:0 2px; border: 1px solid rgba(0,0,0,0.3);"></div>
    </div>
    """

# ==========================================
# 2. INTERFAZ STREAMLIT
# ==========================================
st.set_page_config(page_title="Calculadora de Resistores", page_icon="⚡", layout="centered")

st.title("⚡ Calculadora de Redes Resistivas")
st.markdown("### Análisis de topologías con Código de Colores")

col1, col2 = st.columns(2)
with col1:
    objetivo = st.number_input("Valor Deseado (Ω):", min_value=0.1, value=4700.0, step=100.0)
with col2:
    tolerancia = st.number_input("Tolerancia Aceptada (%):", min_value=0.1, value=5.0, step=1.0)

if st.button("🔍 Calcular Topologías", type="primary"):
    # Animación de carga y dibujo
    with st.spinner("Espere unos momentos... ⏳🔋 Calculando la mejor red..."):
        time.sleep(1) # Pausa visual de 1 segundo para que se vea la animación
        
        resistencias = obtener_lista_resistencias(tolerancia)
        resultados = encontrar_mejores_combinaciones(objetivo, resistencias, tolerancia)

    if not resultados:
        st.error("❌ No existen combinaciones dentro de los parámetros indicados.")
    else:
        st.success("¡Cálculo finalizado exitosamente!")
        
        # 1er LUGAR (Trofeo)
        mejor = resultados[0]
        st.markdown(f"## 🏆 1er Lugar: `{mejor['expresion']}`")
        st.markdown(f"**Eq:** {mejor['valor_eq']:g} Ω &nbsp;&nbsp;|&nbsp;&nbsp; **Error:** {mejor['error']}% &nbsp;&nbsp;|&nbsp;&nbsp; **Tipo:** {mejor['tipo']}")
        
        conteo = Counter(mejor['combinacion'])
        colores_html = "<div>"
        for val, cant in sorted(conteo.items()):
            colores_html += f"<div style='margin-bottom: 8px;'><span style='font-size:16px; font-weight:bold; color:#2C3E50; margin-right:8px;'>{cant}x</span> {obtener_etiqueta_resistor(val, tolerancia)}</div>"
        colores_html += "</div>"
        st.markdown(colores_html, unsafe_allow_html=True)

        st.divider()

        # 2do y 3er LUGAR
        if len(resultados) > 1:
            iconos = ["🥈", "🥉"]
            textos = ["2do Lugar", "3er Lugar"]
            
            for i, r in enumerate(resultados[1:3]):
                st.markdown(f"#### {iconos[i]} {textos[i]}: `{r['expresion']}`")
                st.markdown(f"**Eq:** {r['valor_eq']:g} Ω &nbsp;&nbsp;|&nbsp;&nbsp; **Error:** {r['error']}%")
                
                conteo_alt = Counter(r['combinacion'])
                colores_alt_html = "<div style='display:flex; flex-wrap: wrap; margin-bottom: 20px;'>"
                for val, cant in sorted(conteo_alt.items()):
                    for _ in range(cant): # Dibuja cada resistencia individualmente
                        colores_alt_html += obtener_etiqueta_resistor(val, tolerancia)
                colores_alt_html += "</div>"
                st.markdown(colores_alt_html, unsafe_allow_html=True)