import re
from app import agent


def test_clasificar_interes_idiomas():
    assert agent.clasificar_interes('Quiero aprender inglés y francés') == 'Idiomas'


def test_clasificar_interes_tecnologia():
    assert agent.clasificar_interes('Me interesa programación en Python') == 'Tecnologia'


def test_clasificar_interes_negocios():
    assert agent.clasificar_interes('Estoy buscando cursos de marketing y ventas') == 'Negocios'


def test_calificar_lead():
    assert agent.calificar_lead('Idiomas') == 'Alta'
    assert agent.calificar_lead('Tecnologia') == 'Alta'
    assert agent.calificar_lead('Negocios') == 'Media'
    assert agent.calificar_lead('Otros') == 'Baja'


def test_proponer_cita_format():
    cita = agent.proponer_cita()
    # date should match YYYY-MM-DD
    assert re.match(r"\d{4}-\d{2}-\d{2}", cita['date'])
    assert cita['time'] == '10:00'


def test_crear_lead_payload_contents():
    payload = agent.crear_lead_payload('María Pérez', '57300111222', 'Cursos de Python')
    assert payload['name'] == 'María Pérez'
    assert payload['phone'] == '57300111222'
    assert 'interest' in payload
    assert 'qualification' in payload
    assert 'created_at' in payload
