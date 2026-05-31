import cv2
import numpy as np
import face_recognition
from datetime import datetime, timedelta
import pickle
import os
import mysql.connector
from twilio.rest import Client

# --- CONFIGURACIÓN BASE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_PICKLE = os.path.join(BASE_DIR, "rostros_entrenados.pickle")

# --- 1. CONEXIÓN A MYSQL ---
def conectar_bd():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="sistema_facial"
    )

# --- 2. CONFIGURACIÓN DE TWILIO ---
TWILIO_SID = "tu id de twilio"
TWILIO_TOKEN = "tu token de twilio" 
NUMERO_TWILIO_WA = "whatsapp:+14155238886"  

try:
    client = Client(TWILIO_SID, TWILIO_TOKEN)
except Exception as e:
    print(f"[WARN] No se pudo inicializar Twilio: {e}")
    client = None

# Inicialización de variables de control
conexion = conectar_bd()
ultimos_registros = {} 
TIEMPO_ESPERA = 20  # Tiempo para evitar duplicados

# --- 3. CARGAR ROSTROS ---
try:
    with open(RUTA_PICKLE, "rb") as f:
        datos_recuperados = pickle.load(f)
    encodings_conocidos = datos_recuperados["encodings"]
    nombres_conocidos = datos_recuperados["nombres"]
except Exception as e:
    print(f"[ERROR] Archivo pickle no encontrado: {e}")
    quit()

cap = cv2.VideoCapture(0)
print("[INFO] Sistema de Control Escolar iniciado...")

while True:
    ret, frame = cap.read()
    if not ret: break

    # Reducimos el frame para procesar más rápido
    frame_pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_frame_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

    coordenadas_rostros = face_recognition.face_locations(rgb_frame_pequeno, model="hog")
    encodings_rostros_actuales = face_recognition.face_encodings(rgb_frame_pequeno, coordenadas_rostros)

    etiquetas_pantalla = []

    for encoding_rostro in encodings_rostros_actuales:
        distancias = face_recognition.face_distance(encodings_conocidos, encoding_rostro)
        indice_mejor_match = np.argmin(distancias)
        distancia_minima = distancias[indice_mejor_match]

        nombre = "Desconocido"
        texto_pantalla = "Desconocido"

        # Umbral de reconocimiento
        if distancia_minima < 0.45:
            nombre = nombres_conocidos[indice_mejor_match]
            precision = (1 - distancia_minima) * 100
            texto_pantalla = f"{nombre} {precision:.1f}%"

            # --- LÓGICA DE PERSISTENCIA Y ESTADOS ---
            ahora = datetime.now()
            hacer_registro = False

            if nombre not in ultimos_registros:
                hacer_registro = True
            else:
                diferencia = ahora - ultimos_registros[nombre]
                if diferencia > timedelta(seconds=TIEMPO_ESPERA):
                    hacer_registro = True

            if hacer_registro:
                try:
                    if not conexion.is_connected():
                        conexion = conectar_bd()
                    
                    cursor = conexion.cursor()
                    # Consultamos el estado actual y el teléfono del alumno
                    cursor.execute("SELECT estado, telefono FROM usuarios WHERE nombre = %s", (nombre,))
                    fila = cursor.fetchone()
                    
                    if fila:
                        estado_actual, telefono = fila
                        # Alternamos: si estaba 'entrada', ahora es 'salida' y viceversa
                        nuevo_estado = 'salida' if estado_actual == 'entrada' else 'entrada'
                        accion_msj = "ha INGRESADO a" if nuevo_estado == 'entrada' else "ha SALIDO de"

                        # Actualizamos la base de datos inmediatamente
                        cursor.execute("UPDATE usuarios SET estado = %s WHERE nombre = %s", (nuevo_estado, nombre))
                        conexion.commit()
                        
                        # Actualizamos el tiempo del último registro en memoria
                        ultimos_registros[nombre] = ahora
                        print(f"[REGISTRO] {nombre} detectado. Cambio de estado: {estado_actual} -> {nuevo_estado}")

                        # Envío de notificación por Twilio
                        if client and telefono:
                            try:
                                # Formatear número para WhatsApp
                                num_destino = f"whatsapp:{telefono}" if "whatsapp:" not in str(telefono) else telefono
                                mensaje = client.messages.create(
                                    body=f"Aviso Escolar: {nombre} {accion_msj} el plantel a las {ahora.strftime('%H:%M')}.",
                                    from_=NUMERO_TWILIO_WA,
                                    to=num_destino
                                )
                                print(f"[TWILIO] Notificación enviada. Status: {mensaje.status}")
                            except Exception as e:
                                print(f"[ERROR TWILIO] No se pudo enviar el mensaje: {e}")

                except Exception as e:
                    print(f"[ERROR BD] Fallo en la actualización: {e}")

        etiquetas_pantalla.append(texto_pantalla)

    # --- DIBUJAR RECUADROS ---
    for (top, right, bottom, left), etiqueta in zip(coordenadas_rostros, etiquetas_pantalla):
        # Re-escalamos las coordenadas (porque procesamos al 25%)
        top *= 4; right *= 4; bottom *= 4; left *= 4
        color = (0, 255, 0) if "Desconocido" not in etiqueta else (0, 0, 255)
        
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, etiqueta, (left + 6, bottom - 6), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    cv2.imshow('Control de Acceso Facial - Universidad', frame)
    
    # 'q' para salir
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
if conexion.is_connected():
    conexion.close()
print("[INFO] Sistema cerrado correctamente.")