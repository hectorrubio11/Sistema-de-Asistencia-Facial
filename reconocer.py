import cv2
import numpy as np
import face_recognition
import pickle
import os
import mysql.connector
from twilio.rest import Client

# --- CONFIGURACIÓN BASE DE RUTAS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RUTA_PICKLE = os.path.join(BASE_DIR, "rostros_entrenados.pickle")

# --- 1. CONEXIÓN A MYSQL  ---
def obtener_contactos_mysql():
    try:
        conexion = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="sistema_facial"
        )
        cursor = conexion.cursor()
        cursor.execute("SELECT nombre, telefono FROM usuarios")
        agenda = {nombre: tel for (nombre, tel) in cursor.fetchall()}
        conexion.close()
        return agenda
    except Exception as e:
        print(f"[ERROR MySQL] No se pudo conectar a la base de datos: {e}")
        return {}

# --- 2. CONFIGURACIÓN DE TWILIO (Se ponen las credenciales propias) ---
#TWILIO_SID = "XXXXXXXXXXXXX"
#TWILIO_TOKEN = "XXXXXXXXXXXXXXX" 
#NUMERO_TWILIO_WA = "whatsapp:+14155238886"  

try:
    client = Client(TWILIO_SID, TWILIO_TOKEN)
except Exception as e:
    print(f"[WARN] No se pudo inicializar el cliente de Twilio: {e}")
    client = None

agenda_whatsapp = obtener_contactos_mysql()
notificados = set()

# --- 3. CARGAR ROSTROS ENTRENADOS DESDE EL ARCHIVO PICKLE---
try:
    with open(RUTA_PICKLE, "rb") as f:
        datos_recuperados = pickle.load(f)
    encodings_conocidos = datos_recuperados["encodings"]
    nombres_conocidos = datos_recuperados["nombres"]
except FileNotFoundError:
    print(f"[ERROR] No se encontró el archivo '{RUTA_PICKLE}'.")
    quit()

# --- 4. INICIALIZAR WEBCAM ---
cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret: break

    frame_pequeno = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
    rgb_frame_pequeno = cv2.cvtColor(frame_pequeno, cv2.COLOR_BGR2RGB)

    coordenadas_rostros = face_recognition.face_locations(rgb_frame_pequeno, model="hog")
    encodings_rostros_actuales = face_recognition.face_encodings(rgb_frame_pequeno, coordenadas_rostros)

    etiquetas_pantalla = []

    for encoding_rostro in encodings_rostros_actuales:
        # Calculamos distancias en lugar de solo comparar
        distancias = face_recognition.face_distance(encodings_conocidos, encoding_rostro)
        
        # Buscamos la distancia más corta (el mejor match)
        indice_mejor_match = np.argmin(distancias)
        distancia_minima = distancias[indice_mejor_match]

        # Umbral de tolerancia
        if distancia_minima < 0.45:
            nombre = nombres_conocidos[indice_mejor_match]
            # Cálculo de precisión inversa
            precision = (1 - distancia_minima) * 100
            texto_pantalla = f"{nombre} {precision:.1f}%"

            # --- LÓGICA DE ALERTA ---
            if nombre in agenda_whatsapp and nombre not in notificados:
                if client is not None:
                    try:
                        num_destino = agenda_whatsapp[nombre]
                        if not num_destino.startswith("whatsapp:"):
                            num_destino = f"whatsapp:{num_destino}"
                        
                        client.messages.create(
                            body=f"{nombre} ha llegado a la escuela. (Confianza: {precision:.1f}%)",
                            from_=NUMERO_TWILIO_WA,
                            to=num_destino
                        )
                        print(f"[WhatsApp] Mensaje enviado a {nombre}")
                        notificados.add(nombre)
                    except Exception as e:
                        print(f"[ERROR WhatsApp] {e}")
        else:
            nombre = "Desconocido"
            texto_pantalla = nombre

        etiquetas_pantalla.append(texto_pantalla)

    # Dibujar resultados con la etiqueta de precisión
    for (top, right, bottom, left), etiqueta in zip(coordenadas_rostros, etiquetas_pantalla):
        top *= 4; right *= 4; bottom *= 4; left *= 4
        
        color = (0, 255, 0) if "Desconocido" not in etiqueta else (0, 0, 255)
        cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
        cv2.rectangle(frame, (left, bottom - 35), (right, bottom), color, cv2.FILLED)
        cv2.putText(frame, etiqueta, (left + 6, bottom - 6), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1)

    cv2.imshow('Sistema de Reconocimiento Facial', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'): break

cap.release()
cv2.destroyAllWindows()