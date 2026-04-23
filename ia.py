import os
import json
from groq import Groq

def get_client():
    return Groq(api_key=os.getenv("GROQ_API_KEY"))

def persona_a_prompt(persona: dict) -> str:
    campos = {
        "nombre": "Nombre", "edad": "Edad", "sexo": "Sexo",
        "peso": "Peso (kg)", "altura": "Altura (cm)",
        "objetivo": "Objetivo", "actividad": "Actividad física",
        "intolerancias": "Intolerancias", "condicion_medica": "Condición médica",
        "preferencias": "Preferencias dietéticas"
    }
    lineas = ["PERFIL:"]
    for campo, etiqueta in campos.items():
        valor = persona.get(campo)
        if valor:
            if isinstance(valor, list):
                valor = ", ".join(valor)
            lineas.append(f"{etiqueta}: {valor}")
    return "\n".join(lineas)

def generar_dieta(persona: dict, dias: int = 7, historial: str = "") -> dict:
    """Genera la dieta y devuelve un dict estructurado."""
    client = get_client()
    perfil_texto = persona_a_prompt(persona)
    contexto = f"\n\nHISTORIAL PREVIO:\n{historial}" if historial else ""

    nombres_dias = ["Lunes", "Martes", "Miércoles", "Jueves",
                    "Viernes", "Sábado", "Domingo",
                    "Día 8", "Día 9", "Día 10", "Día 11", "Día 12",
                    "Día 13", "Día 14", "Día 15", "Día 16", "Día 17",
                    "Día 18", "Día 19", "Día 20", "Día 21", "Día 22",
                    "Día 23", "Día 24", "Día 25", "Día 26", "Día 27",
                    "Día 28", "Día 29", "Día 30"]
    lista_dias = ", ".join(nombres_dias[:dias])

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": f"""Eres un nutricionista clínico experto. Genera un plan de alimentación para {dias} días.

Responde ÚNICAMENTE con un JSON válido, sin texto adicional ni backticks. Estructura exacta:
{{
  "calorias_diarias": 2350,
  "macros": {{"proteinas_g": 150, "carbohidratos_g": 280, "grasas_g": 80}},
  "dias": [
    {{
      "dia": "Lunes",
      "calorias": 2350,
      "desayuno": "descripción con cantidad y kcal",
      "almuerzo": "descripción con cantidad y kcal",
      "cena": "descripción con cantidad y kcal",
      "snack": "descripción con cantidad y kcal"
    }}
  ],
  "alimentos_recomendados": ["alimento1", "alimento2", "alimento3", "alimento4", "alimento5"],
  "consejos": ["consejo personalizado 1", "consejo personalizado 2", "consejo personalizado 3"],
  "advertencia": "texto de advertencia médica breve"
}}

Los días deben ser exactamente: {lista_dias}.
Adapta TODO a las intolerancias y condiciones médicas del perfil.
No dejes ningún campo vacío. Sé específico con cantidades."""
            },
            {
                "role": "user",
                "content": f"Genera el plan de {dias} días:\n\n{perfil_texto}{contexto}"
            }
        ],
        max_tokens=4000
    )

    texto = respuesta.choices[0].message.content.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

def evaluar_perfil_ia(persona: dict) -> dict:
    client = get_client()
    perfil_texto = persona_a_prompt(persona)

    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": """Evalúa si tienes suficiente información para generar un plan nutricional seguro.
Responde SOLO con JSON sin backticks:
{"suficiente": true, "preguntas_adicionales": []}
Si faltan datos críticos pon suficiente: false y lista máximo 2 preguntas."""
            },
            {"role": "user", "content": f"Evalúa:\n{perfil_texto}"}
        ],
        max_tokens=200
    )
    texto = respuesta.choices[0].message.content.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)

def ajustar_dieta(dieta_dict: dict, instruccion: str) -> dict:
    client = get_client()
    respuesta = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "Eres nutricionista. Modifica el plan JSON según las instrucciones. Devuelve SOLO el JSON actualizado con la misma estructura, sin backticks ni texto adicional."
            },
            {
                "role": "user",
                "content": f"Plan actual:\n{json.dumps(dieta_dict, ensure_ascii=False)}\n\nCambio: {instruccion}"
            }
        ],
        max_tokens=4000
    )
    texto = respuesta.choices[0].message.content.strip()
    texto = texto.replace("```json", "").replace("```", "").strip()
    return json.loads(texto)