from fpdf import FPDF
import os
import json

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")

def generar_pdf(nombre_usuario: str, contenido) -> bytes:
    if isinstance(contenido, str):
        try:
            contenido = json.loads(contenido)
        except Exception:
            contenido = {"dias": [], "consejos": [], "advertencia": contenido}

    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_left_margin(15)
    pdf.set_right_margin(15)
    pdf.set_top_margin(15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_PATH)

    W = pdf.epw  # ancho efectivo — siempre usa esto, nunca 0

    # Cabecera
    pdf.set_font("DejaVu", "B", 18)
    pdf.multi_cell(W, 12, "NutriAI - Plan de alimentacion", align="C")
    pdf.set_font("DejaVu", "", 11)
    pdf.multi_cell(W, 8, f"Para: {nombre_usuario}", align="C")
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Macros
    calorias = contenido.get("calorias_diarias", "")
    macros = contenido.get("macros", {})
    if calorias:
        pdf.set_font("DejaVu", "B", 11)
        pdf.multi_cell(W, 7, f"Calorias diarias: {calorias} kcal")
    if macros:
        pdf.set_font("DejaVu", "", 10)
        linea = (f"Proteinas: {macros.get('proteinas_g','')}g  |  "
                 f"Carbohidratos: {macros.get('carbohidratos_g','')}g  |  "
                 f"Grasas: {macros.get('grasas_g','')}g")
        pdf.multi_cell(W, 6, linea)
    pdf.ln(4)

    # Días
    for dia in contenido.get("dias", []):
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_fill_color(225, 245, 238)
        titulo_dia = f"{dia.get('dia','')} - {dia.get('calorias','')} kcal"
        pdf.multi_cell(W, 9, titulo_dia, fill=True)
        pdf.set_font("DejaVu", "", 10)
        for label, key in [("Desayuno", "desayuno"), ("Almuerzo", "almuerzo"),
                            ("Cena", "cena"), ("Snack", "snack")]:
            valor = dia.get(key, "")
            if valor:
                pdf.set_x(15)
                pdf.set_font("DejaVu", "B", 10)
                pdf.multi_cell(W, 6, f"{label}:")
                pdf.set_x(15)
                pdf.set_font("DejaVu", "", 10)
                pdf.multi_cell(W, 6, str(valor))
        pdf.ln(3)

    # Consejos
    consejos = contenido.get("consejos", [])
    if consejos:
        pdf.set_font("DejaVu", "B", 12)
        pdf.multi_cell(W, 9, "Consejos personalizados")
        pdf.set_font("DejaVu", "", 10)
        for i, c in enumerate(consejos, 1):
            pdf.set_x(15)
            pdf.multi_cell(W, 6, f"{i}. {c}")
        pdf.ln(3)

    # Advertencia
    advertencia = contenido.get("advertencia", "")
    if advertencia:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_x(15)
        pdf.multi_cell(W, 6, f"Nota: {advertencia}")

    return bytes(pdf.output())