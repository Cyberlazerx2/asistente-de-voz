/*
 static/js/agent.js
 Lógica frontend para controlar el flujo conversacional usando Web Speech API.
 El navegador hace STT y TTS (mejor compatibilidad en Chrome/Edge).
*/

const btnStart = document.getElementById('btnStart');
const btnStop = document.getElementById('btnStop');
const logEl = document.getElementById('log');
const statusEl = document.getElementById('status');
const optSchedule = document.getElementById('optSchedule');

let recognition = null;
let recognizing = false;

function appendLog(text, cls='info'){
  const p = document.createElement('div');
  p.className = 'log-item ' + cls;
  p.innerText = text;
  logEl.appendChild(p);
  logEl.scrollTop = logEl.scrollHeight;
}

function speak(text){
  return new Promise((resolve) => {
    const synth = window.speechSynthesis;
    let voices = synth.getVoices();
    // Filtrar voces españolas y preferir femenina si existe
    let voice = voices.find(v=>v.lang && v.lang.startsWith('es') && /female|mujer|femenina/i.test(v.name)) || voices.find(v=>v.lang && v.lang.startsWith('es')) || voices[0];
    const u = new SpeechSynthesisUtterance(text);
    if(voice) u.voice = voice;
    u.lang = 'es-ES';
    u.rate = 1;
    u.onend = () => resolve();
    synth.speak(u);
  });
}

function startRecognition(){
  if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)){
    appendLog('Reconocimiento de voz no soportado en este navegador. Use Chrome/Edge.', 'error');
    return null;
  }
  const Rec = window.SpeechRecognition || window.webkitSpeechRecognition;
  const rec = new Rec();
  rec.lang = 'es-ES';
  rec.interimResults = false;
  rec.maxAlternatives = 1;
  rec.onstart = () => { recognizing = true; statusEl.innerText = 'Escuchando...'; };
  rec.onerror = (e) => { appendLog('Error reconocimiento: ' + e.error, 'error'); };
  rec.onend = () => { recognizing = false; statusEl.innerText = 'Esperando'; };
  return rec;
}

function listenOnce(){
  return new Promise((resolve) => {
    if(!recognition){ recognition = startRecognition(); }
    if(!recognition){ resolve(null); return; }
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript;
      appendLog('Cliente: ' + text, 'cliente');
      resolve(text);
    };
    recognition.onerror = (e) => { appendLog('No entendí: ' + e.error, 'error'); resolve(null); };
    recognition.onend = () => { /* fin */ };
    recognition.start();
  });
}

async function conversationalFlow(){
  appendLog('Iniciando agente...', 'sistema');
  await speak('Bienvenido a Academia Sin Fronteras. Soy su asistente virtual. ¿En qué puedo ayudarle hoy?');

  // Pedir nombre
  await speak('Para comenzar, ¿podría decirme su nombre completo?');
  let nombre = await listenOnce();
  if(!nombre){ await speak('No recibí su nombre. Por favor escriba su nombre en el formulario.'); return; }

  // Pedir teléfono
  await speak('Gracias. ¿Podría proporcionarme un número de teléfono para contactarlo?');
  let telefono = await listenOnce();
  if(!telefono){ await speak('No escuché su teléfono. Por favor escríbalo en el formulario.'); }

  // Pedir interés
  await speak('¿En qué área de formación está interesado?');
  let interes = await listenOnce();
  if(!interes){ interes = document.getElementById('interest').value || '' }

  // Rellenar campos del formulario para que el usuario pueda ver y editar
  document.getElementById('name').value = nombre || document.getElementById('name').value;
  document.getElementById('phone').value = telefono || document.getElementById('phone').value;
  document.getElementById('interest').value = interes || document.getElementById('interest').value;

  appendLog('Enviando lead al servidor...', 'sistema');

  const payload = {
    name: document.getElementById('name').value,
    phone: document.getElementById('phone').value,
    interest_text: document.getElementById('interest').value,
    schedule: optSchedule.checked
  };

  try{
    const res = await fetch('/api/lead', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    if(res.ok){
      appendLog('Servidor: ' + JSON.stringify(data), 'sistema');
      if(data.appointment){
        await speak('Perfecto. He agendado su cita para el día ' + data.appointment.date + ' a las ' + data.appointment.time);
      } else {
        await speak('Gracias por su interés. Le enviaremos más información por mensaje.');
      }
    } else {
      appendLog('Error servidor: ' + JSON.stringify(data), 'error');
      await speak('Ocurrió un error al procesar su solicitud. Por favor intente de nuevo o use el formulario.');
    }
  } catch(e){
    appendLog('Error conectando al servidor: ' + e.message, 'error');
    await speak('No pude conectar con el servidor. Por favor verifique la aplicación.');
  }
}

btnStart.addEventListener('click', async () => {
  btnStart.disabled = true; btnStop.disabled = false; statusEl.innerText = 'Activo';
  appendLog('Agente activo', 'sistema');
  await conversationalFlow();
});

btnStop.addEventListener('click', () => {
  btnStart.disabled = false; btnStop.disabled = true; statusEl.innerText = 'Inactivo';
  appendLog('Agente detenido', 'sistema');
  if(recognition && recognizing){ recognition.stop(); }
});

// Envío manual desde el formulario
document.getElementById('btnSend').addEventListener('click', async () => {
  const payload = {
    name: document.getElementById('name').value,
    phone: document.getElementById('phone').value,
    interest_text: document.getElementById('interest').value,
    schedule: optSchedule.checked
  };
  appendLog('Enviando manualmente: ' + JSON.stringify(payload), 'sistema');
  try{
    const res = await fetch('/api/lead', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json();
    if(res.ok){ appendLog('Guardado: ' + JSON.stringify(data), 'sistema'); alert('Lead guardado. Calificación: ' + data.qualification); }
    else { appendLog('Error: ' + JSON.stringify(data), 'error'); alert('Error al guardar lead'); }
  }catch(e){ appendLog('Error: ' + e.message, 'error'); alert('Error de conexión'); }
});
