"""
app.agent
Contiene la lógica para calificar leads y agendar citas.
Mantiene la lógica en español y reglas simples para calificación.
"""
from datetime import datetime, timedelta
from typing import Dict


def clasificar_interes(texto: str) -> str:
    texto = texto.lower() if texto else ''
    categorias = {
        "Idiomas": ["inglés", "español", "francés", "alemán", "portugués", "chino", "idioma", "lengua"],
        "Tecnologia": ["programación", "python", "java", "web", "desarrollo", "software", "tecnología", "computación"],
        "Negocios": ["administración", "contabilidad", "marketing", "ventas", "negocio", "emprendimiento"],
        "Desarrollo personal": ["liderazgo", "comunicación", "coaching", "desarrollo personal", "habilidades"]
    }
    for cat, keys in categorias.items():
        for k in keys:
            if k in texto:
                return cat
    return "Otros"


def calificar_lead(interes_categoria: str) -> str:
    # Regla simple: Idiomas y Tecnologia -> Alta; Negocios -> Media; Otros -> Baja
    if interes_categoria in ["Idiomas", "Tecnologia"]:
        return "Alta"
    if interes_categoria == "Negocios":
        return "Media"
    return "Baja"


def proponer_cita() -> Dict[str, str]:
    # Propone la cita para el día siguiente a las 10:00
    fecha = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
    hora = '10:00'
    return {'date': fecha, 'time': hora}


def crear_lead_payload(name: str, phone: str, interest_text: str) -> Dict:
    categoria = clasificar_interes(interest_text)
    calific = calificar_lead(categoria)
    return {
        'name': name,
        'phone': phone,
        'interest': categoria,
        'qualification': calific,
        'created_at': datetime.now().isoformat()
    }
