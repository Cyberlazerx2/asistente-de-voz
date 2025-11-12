import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import datetime
import json
import os
from pathlib import Path
import speech_recognition as sr
import pyttsx3
import re
import time

class AgenteVozApp:
    """
    Aplicación principal del Agente de Voz Automatizado para Academia Sin Fronteras.
    Esta clase maneja la interfaz gráfica, reconocimiento de voz, síntesis de voz,
    calificación de leads y sistema de agendamiento.
    """
    
    def __init__(self, root):
        """
        Inicializa la aplicación con todos sus componentes.
        
        Args:
            root: Ventana principal de tkinter
        """
        self.root = root
        self.root.title("Agente de Voz - Academia Sin Fronteras")
        self.root.geometry("900x700")
        self.root.configure(bg='#f0f8ff')
        
        # Variables de estado
        self.agente_activo = False
        self.historial_llamadas = []
        self.leads_calificados = []
        self.citas_agendadas = []
        self.conversacion_actual = []
        
        # Configuración de archivos de datos
        self.directorio_datos = Path("datos_academia")
        self.directorio_datos.mkdir(exist_ok=True)
        
        # Configuración de voz
        self.engine_voz = pyttsx3.init()
        self.configurar_voz_femenina()
        
        # Configuración de reconocimiento de voz
        self.reconocedor = sr.Recognizer()
        self.microfono = sr.Microphone()
        
        # Cola para comunicación entre hilos
        self.cola_mensajes = queue.Queue()
        
        # Configurar interfaz
        self.configurar_interfaz()
        
        # Iniciar procesamiento de mensajes en cola
        self.procesar_cola()
        
        # Ajustar el micrófono para ruido ambiental
        self.ajustar_microfono()
        
        # Cargar datos existentes
        self.cargar_datos()
    
    def configurar_voz_femenina(self):
        """
        Configura la voz femenina en español para la síntesis de voz.
        Intenta encontrar la voz más apropiada disponible en el sistema.
        """
        try:
            # Obtener voces disponibles
            voces = self.engine_voz.getProperty('voices')
            
            # Buscar voz femenina en español
            voz_seleccionada = None
            for voz in voces:
                if any(palabra in voz.name.lower() for palabra in ['spanish', 'español', 'espanol']):
                    if any(palabra in voz.name.lower() for palabra in ['female', 'mujer', 'femenina']):
                        voz_seleccionada = voz.id
                        break
            
            # Si no encuentra voz femenina en español, usar cualquier voz en español
            if not voz_seleccionada:
                for voz in voces:
                    if any(palabra in voz.name.lower() for palabra in ['spanish', 'español', 'espanol']):
                        voz_seleccionada = voz.id
                        break
            
            if voz_seleccionada:
                self.engine_voz.setProperty('voice', voz_seleccionada)
            
            # Configurar propiedades de voz
            self.engine_voz.setProperty('rate', 160)  # Velocidad de habla
            self.engine_voz.setProperty('volume', 0.9)  # Volumen (0.0 a 1.0)
            
        except Exception as e:
            self.agregar_log(f"Error configurando voz: {e}")
    
    def ajustar_microfono(self):
        """
        Ajusta el micrófono para el ruido ambiental.
        Esto mejora la precisión del reconocimiento de voz.
        """
        try:
            with self.microfono as source:
                self.reconocedor.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            self.agregar_log(f"Error ajustando micrófono: {e}")
    
    def configurar_interfaz(self):
        """
        Configura la interfaz gráfica de usuario con todos los elementos necesarios.
        """
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar grid para expansión
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        
        # Título
        titulo = ttk.Label(main_frame, text="🎓 Agente de Voz - Academia Sin Fronteras", 
                          font=("Arial", 18, "bold"), foreground="#2c3e50")
        titulo.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Estado del agente
        self.estado_agente = ttk.Label(main_frame, text="Estado: INACTIVO", 
                                      font=("Arial", 12), foreground="#e74c3c")
        self.estado_agente.grid(row=1, column=0, columnspan=3, pady=(0, 10))
        
        # Botones de control
        botones_frame = ttk.Frame(main_frame)
        botones_frame.grid(row=2, column=0, columnspan=3, pady=(0, 15))
        
        self.btn_iniciar = ttk.Button(botones_frame, text="▶ Iniciar Agente", 
                                     command=self.iniciar_agente, width=15)
        self.btn_iniciar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_detener = ttk.Button(botones_frame, text="⏹ Detener Agente", 
                                     command=self.detener_agente, state=tk.DISABLED, width=15)
        self.btn_detener.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_limpiar = ttk.Button(botones_frame, text="🗑 Limpiar Log", 
                                     command=self.limpiar_log, width=15)
        self.btn_limpiar.pack(side=tk.LEFT)
        
        # Panel de pestañas
        notebook = ttk.Notebook(main_frame)
        notebook.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Pestaña de conversación
        frame_conversacion = ttk.Frame(notebook, padding="5")
        notebook.add(frame_conversacion, text="Conversación")
        
        # Área de log de conversación
        self.texto_log = scrolledtext.ScrolledText(frame_conversacion, height=20, width=80,
                                                  font=("Arial", 10), wrap=tk.WORD)
        self.texto_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.texto_log.config(state=tk.DISABLED)
        
        frame_conversacion.columnconfigure(0, weight=1)
        frame_conversacion.rowconfigure(0, weight=1)
        
        # Pestaña de leads calificados
        frame_leads = ttk.Frame(notebook, padding="5")
        notebook.add(frame_leads, text="Leads Calificados")
        
        # Treeview para leads
        columnas_leads = ('nombre', 'telefono', 'interes', 'calificacion', 'fecha')
        self.tree_leads = ttk.Treeview(frame_leads, columns=columnas_leads, show='headings', height=15)
        
        # Definir encabezados
        self.tree_leads.heading('nombre', text='Nombre')
        self.tree_leads.heading('telefono', text='Teléfono')
        self.tree_leads.heading('interes', text='Interés Principal')
        self.tree_leads.heading('calificacion', text='Calificación')
        self.tree_leads.heading('fecha', text='Fecha')
        
        # Configurar columnas
        self.tree_leads.column('nombre', width=150)
        self.tree_leads.column('telefono', width=120)
        self.tree_leads.column('interes', width=200)
        self.tree_leads.column('calificacion', width=100)
        self.tree_leads.column('fecha', width=120)
        
        self.tree_leads.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para treeview
        scrollbar_leads = ttk.Scrollbar(frame_leads, orient=tk.VERTICAL, command=self.tree_leads.yview)
        scrollbar_leads.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree_leads.configure(yscrollcommand=scrollbar_leads.set)
        
        frame_leads.columnconfigure(0, weight=1)
        frame_leads.rowconfigure(0, weight=1)
        
        # Pestaña de citas agendadas
        frame_citas = ttk.Frame(notebook, padding="5")
        notebook.add(frame_citas, text="Citas Agendadas")
        
        # Treeview para citas
        columnas_citas = ('nombre', 'telefono', 'fecha_cita', 'hora', 'tipo', 'estado')
        self.tree_citas = ttk.Treeview(frame_citas, columns=columnas_citas, show='headings', height=15)
        
        # Definir encabezados
        self.tree_citas.heading('nombre', text='Nombre')
        self.tree_citas.heading('telefono', text='Teléfono')
        self.tree_citas.heading('fecha_cita', text='Fecha Cita')
        self.tree_citas.heading('hora', text='Hora')
        self.tree_citas.heading('tipo', text='Tipo Consulta')
        self.tree_citas.heading('estado', text='Estado')
        
        # Configurar columnas
        self.tree_citas.column('nombre', width=150)
        self.tree_citas.column('telefono', width=120)
        self.tree_citas.column('fecha_cita', width=120)
        self.tree_citas.column('hora', width=100)
        self.tree_citas.column('tipo', width=150)
        self.tree_citas.column('estado', width=100)
        
        self.tree_citas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar para treeview de citas
        scrollbar_citas = ttk.Scrollbar(frame_citas, orient=tk.VERTICAL, command=self.tree_citas.yview)
        scrollbar_citas.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree_citas.configure(yscrollcommand=scrollbar_citas.set)
        
        frame_citas.columnconfigure(0, weight=1)
        frame_citas.rowconfigure(0, weight=1)
        
        # Estadísticas
        stats_frame = ttk.Frame(main_frame)
        stats_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        
        self.lbl_estadisticas = ttk.Label(stats_frame, 
                                         text="Llamadas hoy: 0 | Leads calificados: 0 | Citas agendadas: 0",
                                         font=("Arial", 10))
        self.lbl_estadisticas.pack()
        
        # Inicializar treeviews
        self.actualizar_treeview_leads()
        self.actualizar_treeview_citas()
        self.actualizar_estadisticas()
    
    def agregar_log(self, mensaje, tipo="info"):
        """
        Agrega un mensaje al área de log con formato y timestamp.
        
        Args:
            mensaje (str): Mensaje a mostrar en el log
            tipo (str): Tipo de mensaje (info, agente, cliente, error)
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Colores según el tipo de mensaje
        colores = {
            "info": "#2c3e50",
            "agente": "#2980b9", 
            "cliente": "#27ae60",
            "error": "#e74c3c",
            "sistema": "#8e44ad"
        }
        
        color = colores.get(tipo, "#2c3e50")
        mensaje_formateado = f"[{timestamp}] {mensaje}"
        
        self.texto_log.config(state=tk.NORMAL)
        self.texto_log.insert(tk.END, mensaje_formateado + "\n", tipo)
        self.texto_log.tag_configure(tipo, foreground=color)
        self.texto_log.see(tk.END)
        self.texto_log.config(state=tk.DISABLED)
        
        # Guardar en conversación actual
        self.conversacion_actual.append({"timestamp": timestamp, "tipo": tipo, "mensaje": mensaje})
    
    def procesar_cola(self):
        """
        Procesa los mensajes en la cola de manera asíncrona.
        """
        try:
            while True:
                mensaje = self.cola_mensajes.get_nowait()
                if mensaje["tipo"] == "log":
                    self.agregar_log(mensaje["contenido"], mensaje["subtipo"])
                elif mensaje["tipo"] == "actualizar_ui":
                    if hasattr(self, mensaje["metodo"]):
                        getattr(self, mensaje["metodo"])()
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.procesar_cola)
    
    def hablar(self, texto):
        """
        Reproduce texto mediante síntesis de voz.
        
        Args:
            texto (str): Texto a convertir a voz
        """
        try:
            self.agregar_log(f"Agente: {texto}", "agente")
            self.engine_voz.say(texto)
            self.engine_voz.runAndWait()
        except Exception as e:
            self.agregar_log(f"Error en síntesis de voz: {e}", "error")
    
    def escuchar(self):
        """
        Escucha y reconoce voz del usuario.
        
        Returns:
            str: Texto reconocido o None si hay error
        """
        try:
            with self.microfono as source:
                self.agregar_log("Escuchando...", "info")
                audio = self.reconocedor.listen(source, timeout=10, phrase_time_limit=15)
            
            texto = self.reconocedor.recognize_google(audio, language="es-ES")
            self.agregar_log(f"Cliente: {texto}", "cliente")
            return texto.lower()
        except sr.WaitTimeoutError:
            self.agregar_log("Tiempo de espera agotado", "error")
            return None
        except sr.UnknownValueError:
            self.agregar_log("No se pudo entender el audio", "error")
            return None
        except sr.RequestError as e:
            self.agregar_log(f"Error en el servicio de reconocimiento: {e}", "error")
            return None
    
    def iniciar_agente(self):
        """Inicia el agente de voz en un hilo separado."""
        if not self.agente_activo:
            self.agente_activo = True
            self.btn_iniciar.config(state=tk.DISABLED)
            self.btn_detener.config(state=tk.NORMAL)
            self.estado_agente.config(text="Estado: ACTIVO", foreground="#27ae60")
            
            # Iniciar hilo para la conversación
            hilo_conversacion = threading.Thread(target=self.ejecutar_conversacion, daemon=True)
            hilo_conversacion.start()
            
            self.agregar_log("Agente iniciado - Esperando llamada...", "sistema")
    
    def detener_agente(self):
        """Detiene el agente de voz."""
        self.agente_activo = False
        self.btn_iniciar.config(state=tk.NORMAL)
        self.btn_detener.config(state=tk.DISABLED)
        self.estado_agente.config(text="Estado: INACTIVO", foreground="#e74c3c")
        self.agregar_log("Agente detenido", "sistema")
    
    def limpiar_log(self):
        """Limpia el área de log."""
        self.texto_log.config(state=tk.NORMAL)
        self.texto_log.delete(1.0, tk.END)
        self.texto_log.config(state=tk.DISABLED)
        self.conversacion_actual = []
    
    def ejecutar_conversacion(self):
        """
        Ejecuta el flujo principal de conversación con el cliente.
        Maneja la bienvenida, preguntas, calificación y agendamiento.
        """
        while self.agente_activo:
            try:
                # Simular llamada entrante
                self.agregar_log("📞 Llamada entrante detectada...", "sistema")
                time.sleep(2)
                
                # Mensaje de bienvenida
                self.hablar("¡Bienvenido a Academia Sin Fronteras! Soy su asistente virtual. ¿En qué puedo ayudarle hoy?")
                
                # Obtener información del cliente
                nombre = self.obtener_nombre()
                if not nombre:
                    continue
                
                telefono = self.obtener_telefono()
                if not telefono:
                    continue
                
                interes = self.obtener_interes()
                if not interes:
                    continue
                
                # Calificar lead
                calificacion = self.calificar_lead(interes)
                
                # Intentar agendar cita
                cita_agendada = self.procesar_agendamiento(nombre, telefono, interes)
                
                # Guardar lead
                lead = {
                    "nombre": nombre,
                    "telefono": telefono,
                    "interes": interes,
                    "calificacion": calificacion,
                    "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "cita_agendada": cita_agendada
                }
                
                self.leads_calificados.append(lead)
                self.guardar_datos()
                self.actualizar_treeview_leads()
                self.actualizar_estadisticas()
                
                # Mensaje de despedida
                if cita_agendada:
                    self.hablar("Perfecto, hemos agendado su cita. Recibirá una confirmación por mensaje. ¡Gracias por contactar a Academia Sin Fronteras!")
                else:
                    self.hablar("Gracias por su interés. Le enviaremos más información por mensaje. ¡Que tenga un excelente día!")
                
                self.agregar_log("Llamada finalizada", "sistema")
                time.sleep(5)  # Esperar antes de la siguiente llamada
                
            except Exception as e:
                self.agregar_log(f"Error en conversación: {e}", "error")
                time.sleep(5)
    
    def obtener_nombre(self):
        """
        Obtiene y valida el nombre del cliente.
        
        Returns:
            str: Nombre del cliente o None si no se pudo obtener
        """
        self.hablar("Para poder ayudarle mejor, ¿podría decirme su nombre completo?")
        
        for intento in range(3):
            respuesta = self.escuchar()
            if respuesta:
                # Extraer nombre usando expresiones regulares
                nombre = self.extraer_nombre(respuesta)
                if nombre:
                    self.hablar(f"Mucho gusto {nombre}")
                    return nombre
            
            if intento < 2:
                self.hablar("No logré entender su nombre completo. ¿Podría repetirlo por favor?")
        
        self.hablar("Lo siento, no pude registrar su nombre. Le pedimos que se comunique nuevamente.")
        return None
    
    def obtener_telefono(self):
        """
        Obtiene y valida el teléfono del cliente.
        
        Returns:
            str: Teléfono del cliente o None si no se pudo obtener
        """
        self.hablar("¿Podría proporcionarme un número de teléfono para contactarlo?")
        
        for intento in range(3):
            respuesta = self.escuchar()
            if respuesta:
                telefono = self.extraer_telefono(respuesta)
                if telefono:
                    self.hablar(f"Perfecto, he registrado el número {telefono}")
                    return telefono
            
            if intento < 2:
                self.hablar("No logré entender su número de teléfono. ¿Podría repetirlo por favor?")
        
        self.hablar("Lo siento, no pude registrar su teléfono. Le pedimos que se comunique nuevamente.")
        return None
    
    def obtener_interes(self):
        """
        Obtiene el interés principal del cliente.
        
        Returns:
            str: Interés del cliente o None si no se pudo obtener
        """
        self.hablar("¿En qué área de formación está interesado? Ofrecemos cursos de idiomas, tecnología, negocios y desarrollo personal.")
        
        for intento in range(3):
            respuesta = self.escuchar()
            if respuesta:
                interes = self.clasificar_interes(respuesta)
                if interes:
                    self.hablar(f"Entendido, está interesado en {interes}")
                    return interes
            
            if intento < 2:
                self.hablar("¿Podría especificar en qué área está interesado?")
        
        self.hablar("Le enviaremos información general de nuestros cursos.")
        return "Interés no especificado"
    
    def extraer_nombre(self, texto):
        """
        Extrae un nombre del texto usando expresiones regulares.
        
        Args:
            texto (str): Texto que contiene el nombre
            
        Returns:
            str: Nombre extraído o None si no se encuentra
        """
        # Patrón para nombres (palabras que empiezan con mayúscula)
        patron = r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b'
        coincidencias = re.findall(patron, texto.title())
        
        if coincidencias:
            return coincidencias[0]
        
        # Si no encuentra con el patrón, tomar las primeras 2-3 palabras
        palabras = texto.split()
        if 2 <= len(palabras) <= 3:
            return ' '.join(palabras).title()
        
        return None
    
    def extraer_telefono(self, texto):
        """
        Extrae un número de teléfono del texto.
        
        Args:
            texto (str): Texto que contiene el teléfono
            
        Returns:
            str: Teléfono extraído o None si no es válido
        """
        # Eliminar espacios y caracteres no numéricos
        numeros = re.sub(r'\D', '', texto)
        
        # Validar longitud (8-15 dígitos)
        if 8 <= len(numeros) <= 15:
            return numeros
        
        return None
    
    def clasificar_interes(self, texto):
        """
        Clasifica el interés del cliente en categorías predefinidas.
        
        Args:
            texto (str): Texto que describe el interés
            
        Returns:
            str: Categoría del interés
        """
        categorias = {
            "idiomas": ["inglés", "español", "francés", "alemán", "portugués", "chino", "idioma", "lengua"],
            "tecnologia": ["programación", "python", "java", "web", "desarrollo", "software", "tecnología", "computación"],
            "negocios": ["administración", "contabilidad", "marketing", "ventas", "negocio", "emprendimiento"],
            "desarrollo_personal": ["liderazgo", "comunicación", "coaching", "desarrollo personal", "habilidades"]
        }
        
        texto = texto.lower()
        for categoria, palabras_clave in categorias.items():
            for palabra in palabras_clave:
                if palabra in texto:
                    return categoria.replace("_", " ").title()
        
        return "Otros"
    
    def calificar_lead(self, interes):
        """
        Califica el lead basado en el interés mostrado.
        
        Args:
            interes (str): Interés del cliente
            
        Returns:
            str: Calificación del lead (Alta, Media, Baja)
        """
        # Lógica simple de calificación
        if interes in ["Idiomas", "Tecnologia"]:
            return "Alta"
        elif interes in ["Negocios"]:
            return "Media"
        else:
            return "Baja"
    
    def procesar_agendamiento(self, nombre, telefono, interes):
        """
        Procesa el agendamiento de una cita.
        
        Args:
            nombre (str): Nombre del cliente
            telefono (str): Teléfono del cliente
            interes (str): Interés del cliente
            
        Returns:
            bool: True si se agendó la cita, False en caso contrario
        """
        self.hablar("¿Le gustaría agendar una cita con uno de nuestros asesores para recibir información más detallada?")
        
        respuesta = self.escuchar()
        if respuesta and any(palabra in respuesta for palabra in ["sí", "si", "claro", "por supuesto", "ok"]):
            
            # Proponer fecha
            fecha = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%d de %B")
            self.hablar(f"Perfecto, tenemos disponibilidad para el {fecha}. ¿Le parece bien?")
            
            confirmacion = self.escuchar()
            if confirmacion and any(palabra in confirmacion for palabra in ["sí", "si", "ok", "bien", "perfecto"]):
                
                # Crear cita
                cita = {
                    "nombre": nombre,
                    "telefono": telefono,
                    "fecha_cita": (datetime.datetime.now() + datetime.timedelta(days=1)).strftime("%Y-%m-%d"),
                    "hora": "10:00 AM",
                    "tipo": interes,
                    "estado": "Confirmada",
                    "fecha_agendamiento": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.citas_agendadas.append(cita)
                self.guardar_datos()
                self.actualizar_treeview_citas()
                self.actualizar_estadisticas()
                
                self.agregar_log(f"Cita agendada para {nombre}", "sistema")
                return True
        
        return False
    
    def actualizar_treeview_leads(self):
        """Actualiza el treeview con los leads calificados."""
        for item in self.tree_leads.get_children():
            self.tree_leads.delete(item)
        
        for lead in self.leads_calificados:
            self.tree_leads.insert('', tk.END, values=(
                lead['nombre'],
                lead['telefono'],
                lead['interes'],
                lead['calificacion'],
                lead['fecha']
            ))
    
    def actualizar_treeview_citas(self):
        """Actualiza el treeview con las citas agendadas."""
        for item in self.tree_citas.get_children():
            self.tree_citas.delete(item)
        
        for cita in self.citas_agendadas:
            self.tree_citas.insert('', tk.END, values=(
                cita['nombre'],
                cita['telefono'],
                cita['fecha_cita'],
                cita['hora'],
                cita['tipo'],
                cita['estado']
            ))
    
    def actualizar_estadisticas(self):
        """Actualiza las estadísticas en la interfaz."""
        llamadas_hoy = len([lead for lead in self.leads_calificados 
                           if lead['fecha'].startswith(datetime.datetime.now().strftime("%Y-%m-%d"))])
        leads_totales = len(self.leads_calificados)
        citas_totales = len(self.citas_agendadas)
        
        self.lbl_estadisticas.config(
            text=f"Llamadas hoy: {llamadas_hoy} | Leads calificados: {leads_totales} | Citas agendadas: {citas_totales}"
        )
    
    def guardar_datos(self):
        """Guarda los datos en archivos JSON."""
        try:
            with open(self.directorio_datos / "leads.json", "w", encoding="utf-8") as f:
                json.dump(self.leads_calificados, f, ensure_ascii=False, indent=2)
            
            with open(self.directorio_datos / "citas.json", "w", encoding="utf-8") as f:
                json.dump(self.citas_agendadas, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.agregar_log(f"Error guardando datos: {e}", "error")
    
    def cargar_datos(self):
        """Carga los datos desde archivos JSON."""
        try:
            if (self.directorio_datos / "leads.json").exists():
                with open(self.directorio_datos / "leads.json", "r", encoding="utf-8") as f:
                    self.leads_calificados = json.load(f)
            
            if (self.directorio_datos / "citas.json").exists():
                with open(self.directorio_datos / "citas.json", "r", encoding="utf-8") as f:
                    self.citas_agendadas = json.load(f)
                    
        except Exception as e:
            self.agregar_log(f"Error cargando datos: {e}", "error")

def main():
    """
    Función principal que inicia la aplicación.
    """
    try:
        root = tk.Tk()
        app = AgenteVozApp(root)
        root.mainloop()
    except Exception as e:
        print(f"Error iniciando aplicación: {e}")

if __name__ == "__main__":
    main()
