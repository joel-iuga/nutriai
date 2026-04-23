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
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_PATH)

    # Cabecera
    pdf.set_font("DejaVu", "B", 18)
    pdf.cell(0, 12, "NutriAI — Plan de alimentacion", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Para: {nombre_usuario}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Macros
    calorias = contenido.get("calorias_diarias", "")
    macros = contenido.get("macros", {})
    if calorias:
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 8, f"Calorias diarias: {calorias} kcal", new_x="LMARGIN", new_y="NEXT")
    if macros:
        pdf.set_font("DejaVu", "", 10)
        pdf.multi_cell(0, 6,
            f"Proteinas: {macros.get('proteinas_g','')}g  |  "
            f"Carbohidratos: {macros.get('carbohidratos_g','')}g  |  "
            f"Grasas: {macros.get('grasas_g','')}g")
    pdf.ln(4)

    # Días
    for dia in contenido.get("dias", []):
        pdf.set_font("DejaVu", "B", 12)
        pdf.set_fill_color(225, 245, 238)
        pdf.cell(0, 9, f"  {dia.get('dia','')}  -  {dia.get('calorias','')} kcal",
                new_x="LMARGIN", new_y="NEXT", fill=True)
        pdf.set_font("DejaVu", "", 10)
        for label, key in [("Desayuno","desayuno"),("Almuerzo","almuerzo"),
                            ("Cena","cena"),("Snack","snack")]:
            if dia.get(key):
                # Label en su propia línea, luego el contenido
                pdf.set_font("DejaVu", "B", 10)
                pdf.multi_cell(0, 6, f"{label}:")
                pdf.set_font("DejaVu", "", 10)
                pdf.multi_cell(0, 6, str(dia[key]))
        pdf.ln(3)
        
    # Consejos
    consejos = contenido.get("consejos", [])
    if consejos:
        pdf.set_font("DejaVu", "B", 12)
        pdf.cell(0, 9, "Consejos personalizados", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        for i, c in enumerate(consejos, 1):
            pdf.multi_cell(0, 6, f"{i}. {c}")
        pdf.ln(3)

    # Advertencia
    advertencia = contenido.get("advertencia", "")
    if advertencia:
        pdf.set_font("DejaVu", "B", 10)
        pdf.multi_cell(0, 6, f"Nota: {advertencia}")

    return bytes(pdf.output())