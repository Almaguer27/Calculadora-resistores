import ipywidgets as widgets
from IPython.display import display, HTML
import itertools
from collections import Counter
import time

# ==========================================
# 1. LÓGICA MATEMÁTICA Y DE COMPONENTES
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
# 3. INTERFAZ GRÁFICA PARA GOOGLE COLAB
# ==========================================

header_html = widgets.HTML("""
<div style="background-color: #2C3E50; padding: 20px; width: 100%; text-align: center; border-radius: 8px 8px 0 0; font-family: 'Segoe UI', sans-serif;">
    <h1 style="color: white; margin: 0; font-size: 24px;">Calculadora de Resistores de Precisión</h1>
    <p style="color: #BDC3C7; margin: 5px 0 0 0; font-size: 14px;">Análisis de topologías Serie, Paralelo y Mixtas con Código de Colores</p>
</div>
""")

input_obj = widgets.FloatText(value=4700, layout=widgets.Layout(width='100%'))
input_tol = widgets.FloatText(value=5, layout=widgets.Layout(width='100%'))
btn_calc = widgets.Button(description='🔍 Calcular Topologías', button_style='info', layout=widgets.Layout(width='100%', height='40px'))
btn_calc.style.button_color = '#2980B9'

left_panel = widgets.VBox([
    widgets.HTML("<h3 style='color: #2C3E50; font-family: \"Segoe UI\", sans-serif; margin-top: 0;'>⚙️ Parámetros</h3><hr style='border:1px solid #D5D8DC;'>"),
    widgets.HTML("<div style='color: #2C3E50; font-family: \"Segoe UI\", sans-serif; font-weight: bold; margin-bottom: 5px;'>Valor Deseado (Ω):</div>"),
    input_obj,
    widgets.HTML("<div style='color: #7F8C8D; font-family: \"Segoe UI\", sans-serif; font-size: 12px; margin-bottom: 15px;'>Ej. 4700, 330.5</div>"),
    widgets.HTML("<div style='color: #2C3E50; font-family: \"Segoe UI\", sans-serif; font-weight: bold; margin-bottom: 5px;'>Tolerancia Aceptada (%):</div>"),
    input_tol,
    widgets.HTML("<div style='color: #7F8C8D; font-family: \"Segoe UI\", sans-serif; font-size: 12px; margin-bottom: 25px;'>Aplica Serie E12 (≥10) o E24 (<10)</div>"),
    btn_calc
])
left_panel.layout = widgets.Layout(background_color='#FFFFFF', padding='25px', border='1px solid #D5D8DC', width='35%', border_radius='0 0 0 8px')

out_right = widgets.Output()
out_right.layout = widgets.Layout(width='65%', padding='0 0 0 20px')

def al_presionar_calcular(b):
    # Pantalla de carga
    with out_right:
        out_right.clear_output()
        display(HTML("""
        <div style='background-color: #FFFFFF; padding: 40px; text-align: center; border: 1px solid #D5D8DC; border-radius: 5px; font-family: "Segoe UI", sans-serif;'>
            <h2 style='color: #2980B9;'>Espere unos momentos... ⏳🔋</h2>
            <p style='color: #7F8C8D;'>Calculando la mejor red resistiva y generando códigos de colores</p>
        </div>
        """))
    
    time.sleep(1.5) # Pausa para visualizar la carga
    
    with out_right:
        out_right.clear_output()
        try:
            objetivo = float(input_obj.value)
            tolerancia = float(input_tol.value)
            if objetivo <= 0 or tolerancia < 0:
                raise ValueError
        except ValueError:
            display(HTML("<div style='background: #FFFFFF; padding: 20px; border-left: 5px solid #E74C3C; border-radius: 5px;'><h3 style='color: #E74C3C; margin:0;'>Error</h3><p style='color:#2C3E50;'>Ingresa valores numéricos positivos.</p></div>"))
            return

        resistencias = obtener_lista_resistencias(tolerancia)
        resultados = encontrar_mejores_combinaciones(objetivo, resistencias, tolerancia)
        
        if not resultados:
            display(HTML("<div style='background: #FFFFFF; padding: 20px; border-left: 5px solid #E74C3C; border-radius: 5px;'><h3 style='color: #E74C3C; margin:0;'>Sin resultados</h3><p style='color:#2C3E50;'>No existen combinaciones dentro del margen de error indicado.</p></div>"))
            return
            
        # PROCESAR 1er LUGAR
        mejor = resultados[0]
        conteo = Counter(mejor['combinacion'])
        
        colores_html = ""
        for val, cant in sorted(conteo.items()):
            colores_html += f"<div style='margin-bottom: 8px;'><span style='font-size:16px; font-weight:bold; color:#2C3E50; margin-right:8px;'>{cant}x</span> {obtener_etiqueta_resistor(val, tolerancia)}</div>"

        html_top = f"""
        <div style='background-color: #FFFFFF; padding: 25px; border: 1px solid #D5D8DC; border-radius: 5px; font-family: "Segoe UI", sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.05);'>
            <h4 style='color: #27AE60; margin: 0 0 10px 0; border-bottom: 1px solid #D5D8DC; padding-bottom: 10px; font-size:18px;'>🏆 1er LUGAR</h4>
            <h1 style='color: #2C3E50; margin: 15px 0; font-family: Consolas, monospace; font-size: 32px;'>{mejor['expresion']}</h1>
            <p style='color: #7F8C8D; font-size: 15px;'>Valor Eq: <b style='color:#2C3E50;'>{mejor['valor_eq']:g} Ω</b> &nbsp;&nbsp;|&nbsp;&nbsp; Error: <b style='color:#2C3E50;'>{mejor['error']}%</b> &nbsp;&nbsp;|&nbsp;&nbsp; Tipo: <b style='color:#2C3E50;'>{mejor['tipo']}</b></p>
            <div style='margin-top: 20px; background: #F8F9F9; padding: 15px; border-radius: 5px; border-left: 4px solid #2980B9;'>
                <h5 style='color: #2C3E50; margin: 0 0 15px 0; font-size:14px;'>🛒 Requisito de Componentes (Bandas de Color):</h5>
                {colores_html}
            </div>
        </div>
        """
        
        # PROCESAR 2do y 3er LUGAR
        html_alts = ""
        if len(resultados) > 1:
            iconos = ["🥈 2do Lugar", "🥉 3er Lugar"]
            html_alts += "<h4 style='color: #2C3E50; margin-top: 25px; font-family: \"Segoe UI\", sans-serif;'>Alternativas Secundarias:</h4>"
            for i, r in enumerate(resultados[1:3]):
                conteo_alt = Counter(r['combinacion'])
                colores_alt_html = ""
                for val, cant in sorted(conteo_alt.items()):
                    for _ in range(cant): 
                        colores_alt_html += obtener_etiqueta_resistor(val, tolerancia)

                html_alts += f"""
                <div style='background-color: #FFFFFF; border: 1px solid #D5D8DC; border-radius: 5px; padding: 15px; margin-bottom: 10px; font-family: "Segoe UI", sans-serif;'>
                    <div style='display: flex; justify-content: space-between; margin-bottom: 15px;'>
                        <span style='font-family: Consolas, monospace; font-size: 18px; font-weight: bold; color: #2C3E50;'>{iconos[i]}: &nbsp;{r['expresion']}</span>
                        <span style='color: #7F8C8D; font-size: 15px; font-weight:bold;'>{r['valor_eq']:g} Ω (Err: {r['error']}%)</span>
                    </div>
                    <div style='display:flex; flex-wrap: wrap;'>
                        {colores_alt_html}
                    </div>
                </div>
                """
        
        display(HTML(html_top + html_alts))

btn_calc.on_click(al_presionar_calcular)

main_box = widgets.HBox([left_panel, out_right])
main_box.layout = widgets.Layout(background_color='#EAECEE', padding='20px', display='flex', flex_flow='row', border_radius='0 0 8px 8px')

display(header_html, main_box)
