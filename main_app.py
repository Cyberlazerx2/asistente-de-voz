import tkinter as tk
"""
main_app.py
Ahora este archivo arranca la versión web del Agente de Voz (Flask).
"""
from app import create_app

app = create_app()

if __name__ == '__main__':
    # En desarrollo usamos debug=True; en producción usar un servidor WSGI
    app.run(host='127.0.0.1', port=5000, debug=True)