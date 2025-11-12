"""
app.__init__
Inicializador del paquete Flask.
"""
import os
from flask import Flask


def create_app(config=None):
    app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'), static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(os.path.dirname(__file__), '..', 'datos_academia', 'data.db')
    )

    # Crear carpeta de datos si no existe
    datos_dir = os.path.join(os.path.dirname(__file__), '..', 'datos_academia')
    os.makedirs(datos_dir, exist_ok=True)

    # Importar y registrar rutas
    from . import routes
    routes.init_app(app)

    return app
