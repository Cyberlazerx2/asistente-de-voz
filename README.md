# asistente-de-voz
Creacion de un asistente de voz

Versión web (recomendado):

- El proyecto ahora incluye una versión web del Agente de Voz que usa Flask en el backend y la Web Speech API del navegador para reconocimiento y síntesis de voz (voz femenina en español si el navegador la provee).
- Archivo de entrada para la versión web: `main_app_web.py`.

Requisitos (instalar en un entorno virtual):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Ejecutar la app web (desarrollo):

```powershell
python main_app_web.py
# Abrir http://127.0.0.1:5000 en Chrome o Edge para mejor compatibilidad con Web Speech API
```

Notas importantes:
- La síntesis y el reconocimiento de voz se realizan en el navegador, no en el servidor. Esto evita problemas con bibliotecas nativas como `pyaudio` y `pyttsx3` que suelen generar errores en diferentes sistemas.
 - La síntesis y el reconocimiento de voz se realizan en el navegador, no en el servidor. Esto evita problemas con bibliotecas nativas como `pyaudio` que suelen generar errores en diferentes sistemas. Por esa razón `pyaudio` fue removido de `requirements.txt`. Si necesita la versión de escritorio (Tkinter) tendrá que instalar dependencias de audio adicionales manualmente.
 - `pyttsx3` y `speech_recognition` se mantuvieron en el repositorio para la aplicación de escritorio heredada (`main_app_desktop.py`), pero la experiencia recomendada es la versión web que usa la Web Speech API del navegador.
 - El backend guarda leads y citas en `datos_academia/data.db` (SQLite).

Próximos pasos sugeridos:
- Añadir autenticación y envío real de SMS/WhatsApp para confirmaciones.
- Mejorar manejo de errores y UI para varias llamadas concurrentes.

