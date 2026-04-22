from fpdf import FPDF
import re
import os

FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "DejaVuSans.ttf")

def limpiar_markdown(texto: str) -> str:
    texto = re.sub(r"\*\*(.+?)\*\*", r"\1", texto)
    texto = re.sub(r"\*(.+?)\*", r"\1", texto)
    texto = re.sub(r"#{1,3} ", "", texto)
    return texto.strip()

def generar_pdf(nombre_usuario: str, dieta_texto: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    pdf.set_auto_page_break(auto=True, margin=15)

    # Registrar fuente Unicode
    pdf.add_font("DejaVu", "", FONT_PATH)
    pdf.add_font("DejaVu", "B", FONT_PATH)

    # Cabecera
    pdf.set_font("DejaVu", "B", 18)
    pdf.cell(0, 12, "NutriAI — Plan de alimentación", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 8, f"Generado para: {nombre_usuario}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Contenido
    for linea in dieta_texto.split("\n"):
        linea = limpiar_markdown(linea)

        if not linea:
            pdf.ln(2)
            continue

        try:
            if linea.startswith("# ") or linea.startswith("## "):
                pdf.set_font("DejaVu", "B", 13)
                pdf.multi_cell(0, 8, linea.lstrip("# "))
                pdf.set_font("DejaVu", "", 10)
            elif linea.startswith("- ") or linea.startswith("* "):
                pdf.set_font("DejaVu", "", 10)
                pdf.multi_cell(0, 6, "  • " + linea[2:])
            else:
                pdf.set_font("DejaVu", "", 10)
                pdf.multi_cell(0, 6, linea)
        except Exception:
            continue

    return bytes(pdf.output())