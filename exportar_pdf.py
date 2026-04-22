from fpdf import FPDF
import re

def limpiar_texto(texto: str) -> str:
    reemplazos = {
        "—": "-", "–": "-", "→": "->", "←": "<-",
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "Á": "A", "É": "E", "Í": "I", "Ó": "O", "Ú": "U",
        "ñ": "n", "Ñ": "N", "ü": "u", "Ü": "U",
        "¿": "", "¡": "", "•": "-", "\u2022": "-",
        "✅": "[OK]", "⚠": "[!]", "🥗": "", "🤖": "",
        "📋": "", "💾": "", "📄": "", "🔄": "",
    }
    for orig, reemplazo in reemplazos.items():
        texto = texto.replace(orig, reemplazo)
    return texto.encode("ascii", "ignore").decode("ascii").strip()

def generar_pdf(nombre_usuario: str, dieta_texto: str) -> bytes:
    pdf = FPDF(format="A4")
    pdf.add_page()
    pdf.set_margins(15, 15, 15)  # márgenes más pequeños
    pdf.set_auto_page_break(auto=True, margin=15)

    # Cabecera
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, "NutriAI - Plan de alimentacion", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Para: {limpiar_texto(nombre_usuario)}", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(4)
    pdf.set_draw_color(180, 180, 180)
    pdf.line(15, pdf.get_y(), 195, pdf.get_y())
    pdf.ln(5)

    # Contenido línea a línea
    for linea in dieta_texto.split("\n"):
        # Limpiar markdown
        linea = re.sub(r"\*\*(.+?)\*\*", r"\1", linea)
        linea = re.sub(r"\*(.+?)\*", r"\1", linea)
        linea = re.sub(r"#{1,3} ", "", linea)
        linea = limpiar_texto(linea)

        if not linea:
            pdf.ln(2)
            continue

        try:
            if linea.startswith("# ") or linea.startswith("## "):
                pdf.set_font("Helvetica", "B", 12)
                pdf.multi_cell(0, 7, linea.lstrip("# "))
                pdf.set_font("Helvetica", "", 10)
            else:
                pdf.set_font("Helvetica", "", 10)
                pdf.multi_cell(0, 6, linea)
        except Exception:
            # Si una línea sigue fallando, la omitimos y continuamos
            continue

    return bytes(pdf.output())