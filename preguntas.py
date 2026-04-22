# preguntas.py
# Banco de preguntas nutricionales para la Fase 1
# Cada pregunta tiene: id, texto, tipo de respuesta, y opciones (si aplica)

PREGUNTAS = [
    {
        "id": "edad",
        "texto": "¿Cuántos años tienes?",
        "tipo": "numero",
        "min": 10,
        "max": 100,
        "requerida": True
    },
    {
        "id": "sexo",
        "texto": "¿Cuál es tu sexo biológico?",
        "tipo": "opciones",
        "opciones": ["Masculino", "Femenino"],
        "requerida": True
    },
    {
        "id": "peso",
        "texto": "¿Cuánto pesas aproximadamente? (en kg)",
        "tipo": "numero",
        "min": 30,
        "max": 250,
        "requerida": True
    },
    {
        "id": "altura",
        "texto": "¿Cuánto mides? (en cm)",
        "tipo": "numero",
        "min": 100,
        "max": 220,
        "requerida": True
    },
    {
        "id": "objetivo",
        "texto": "¿Cuál es tu objetivo principal?",
        "tipo": "opciones",
        "opciones": [
            "Perder peso",
            "Ganar masa muscular",
            "Mantener mi peso actual",
            "Mejorar mi salud general",
            "Controlar una condición médica"
        ],
        "requerida": True
    },
    {
        "id": "actividad",
        "texto": "¿Cómo describirías tu nivel de actividad física?",
        "tipo": "opciones",
        "opciones": [
            "Sedentario (trabajo de escritorio, poco ejercicio)",
            "Ligeramente activo (camino bastante o hago ejercicio 1-2 días/semana)",
            "Moderadamente activo (ejercicio 3-4 días/semana)",
            "Muy activo (ejercicio intenso 5+ días/semana)",
            "Atleta o trabajo físico intenso"
        ],
        "requerida": True
    },
    {
        "id": "intolerancias",
        "texto": "¿Tienes alergias o intolerancias alimentarias?",
        "tipo": "texto_libre",
        "placeholder": "Ej: intolerancia a la lactosa, alergia al gluten, alergia a los frutos secos... o escribe 'ninguna'",
        "requerida": True
    },
    {
        "id": "condicion_medica",
        "texto": "¿Tienes alguna condición médica relevante para la nutrición?",
        "tipo": "texto_libre",
        "placeholder": "Ej: diabetes tipo 2, hipertensión, hipotiroidismo, colesterol alto... o escribe 'ninguna'",
        "requerida": True
    },
    {
        "id": "comidas_dia",
        "texto": "¿Cuántas comidas haces al día normalmente?",
        "tipo": "opciones",
        "opciones": ["1-2 comidas", "3 comidas", "4-5 comidas", "Más de 5 comidas / picoteo frecuente"],
        "requerida": False
    },
    {
        "id": "preferencias",
        "texto": "¿Tienes preferencias o restricciones dietéticas?",
        "tipo": "opciones_multiple",
        "opciones": [
            "Vegetariano",
            "Vegano",
            "Sin gluten",
            "Sin lácteos",
            "Halal",
            "Kosher",
            "Ninguna restricción especial"
        ],
        "requerida": False
    }
]

PREGUNTAS_CONDICIONALES = [
    {
        "id": "diabetes_tipo",
        "texto": "¿Qué tipo de diabetes tienes y cómo la controlas?",
        "tipo": "texto_libre",
        "placeholder": "Ej: Diabetes tipo 2, controlada con metformina...",
        "condicion": lambda r: "diabetes" in r.get("condicion_medica", "").lower(),
        "requerida": True
    },
    {
        "id": "entrenamiento_detalle",
        "texto": "¿Qué tipo de entrenamiento haces y cuántas horas a la semana?",
        "tipo": "texto_libre",
        "placeholder": "Ej: Pesas 4 días/semana + cardio 2 días, unas 6h en total",
        "condicion": lambda r: r.get("actividad", "") in [
            "Muy activo (ejercicio intenso 5+ días/semana)",
            "Atleta o trabajo físico intenso"
        ],
        "requerida": True
    },
    {
        "id": "meta_peso",
        "texto": "¿Cuántos kg quieres perder y en qué plazo aproximado?",
        "tipo": "texto_libre",
        "placeholder": "Ej: Quiero perder unos 10 kg en 4-6 meses",
        "condicion": lambda r: r.get("objetivo", "") == "Perder peso",
        "requerida": True
    },
    {
        "id": "meta_musculo",
        "texto": "¿Cuánto tiempo llevas entrenando y cuál es tu nivel actual?",
        "tipo": "texto_libre",
        "placeholder": "Ej: Llevo 1 año entrenando, nivel intermedio",
        "condicion": lambda r: r.get("objetivo", "") == "Ganar masa muscular",
        "requerida": True
    },
    {
        "id": "detalle_intolerancia",
        "texto": "¿Qué síntomas tienes con esa intolerancia y qué alimentos evitas?",
        "tipo": "texto_libre",
        "placeholder": "Ej: Con el sorbitol tengo hinchazón, evito manzanas, peras y chicles",
        "condicion": lambda r: r.get("intolerancias", "").lower() not in ["ninguna", "no", ""],
        "requerida": True
    }
]


def obtener_preguntas_activas(respuestas: dict) -> list:
    """
    Devuelve la lista de preguntas que deben mostrarse: las base
    siempre, más las condicionales que apliquen según las respuestas.
    """
    activas = list(PREGUNTAS)  # Empieza con todas las preguntas base

    for pregunta_cond in PREGUNTAS_CONDICIONALES:
        try:
            if pregunta_cond["condicion"](respuestas):
                # Solo añadirla si no está ya en la lista
                ids_actuales = [p["id"] for p in activas]
                if pregunta_cond["id"] not in ids_actuales:
                    activas.append({k: v for k, v in pregunta_cond.items() if k != "condicion"})
        except Exception:
            pass

    return activas