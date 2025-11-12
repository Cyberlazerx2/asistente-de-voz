"""
app.routes
Rutas HTTP para la aplicación del Agente de Voz.
Provee la página principal y endpoints REST para lead/agendamiento.
"""
from flask import render_template, request, jsonify, current_app
from . import db as db_module
from . import agent as agent_module
import os
from datetime import datetime


def init_app(app):
    @app.before_first_request
    def setup_database():
        db_path = app.config['DATABASE']
        # Inicializar DB si es necesario
        conn = db_module.init_db(db_path)
        # Guardar conexión en app para uso posterior
        app.config['DB_CONN'] = conn

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/lead', methods=['POST'])
    def api_lead():
        """Recibe un lead, lo califica y opcionalmente agenda.
        JSON esperado: {name, phone, interest_text, schedule (bool)}
        """
        data = request.get_json(force=True)
        name = data.get('name')
        phone = data.get('phone')
        interest_text = data.get('interest_text', '')
        wants_schedule = bool(data.get('schedule', False))

        if not name or not phone:
            return jsonify({'error': 'Faltan campos name o phone'}), 400

        # Crear payload y guardar lead
        lead_payload = agent_module.crear_lead_payload(name, phone, interest_text)
        conn = current_app.config.get('DB_CONN')
        lead_id = db_module.insert_lead(conn, lead_payload)

        response = {'lead_id': lead_id, 'qualification': lead_payload['qualification'], 'interest': lead_payload['interest']}

        if wants_schedule:
            cita = agent_module.proponer_cita()
            appt_payload = {
                'lead_id': lead_id,
                'date': cita['date'],
                'time': cita['time'],
                'type': lead_payload['interest'],
                'status': 'Confirmada',
                'created_at': datetime.now().isoformat()
            }
            appt_id = db_module.insert_appointment(conn, appt_payload)
            response['appointment'] = {'id': appt_id, 'date': appt_payload['date'], 'time': appt_payload['time']}

        return jsonify(response)

    @app.route('/api/stats', methods=['GET'])
    def api_stats():
        conn = current_app.config.get('DB_CONN')
        stats = db_module.get_stats(conn)
        return jsonify(stats)
