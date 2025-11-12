"""
main_app_web.py
Entry point para la versión web del Agente de Voz - Academia Sin Fronteras.
Levanta una aplicación Flask que sirve la interfaz web (frontend usa Web Speech API)

Uso:
    python main_app_web.py

El proyecto usa el navegador para reconocimiento y síntesis de voz (voz femenina en español).
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # En desarrollo usamos debug=True; en producción usar un servidor WSGI
    app.run(host='127.0.0.1', port=5000, debug=True)
