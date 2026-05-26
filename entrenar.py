import cv2
import face_recognition
import os
import pickle

# Ruta de la carpeta principal de imágenes
DIR_ROSTROS = "rostros"

encodings_conocidos = []
nombres_conocidos = []

print("[INFO] Leyendo imágenes y extrayendo características...")

# Recorrer las carpetas de cada persona
for nombre_persona in os.listdir(DIR_ROSTROS):
    ruta_persona = os.path.join(DIR_ROSTROS, nombre_persona)
    
    # Asegurarnos de que sea una carpeta y no un archivo suelto
    if not os.path.isdir(ruta_persona):
        continue

    print(f"Procesando a: {nombre_persona}")

    for nombre_archivo in os.listdir(ruta_persona):
        ruta_imagen = os.path.join(ruta_persona, nombre_archivo)
        
        # Leer la foto y convertirla a RGB
        imagen = cv2.imread(ruta_imagen)
        if imagen is None:
            continue
            
        imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
        
        # Detectar la ubicación del rostro en la foto
        cajas_rostros = face_recognition.face_locations(imagen_rgb, model="hog")
        
        # Si encuentra un rostro, extrae sus características (encoding)
        if len(cajas_rostros) > 0:
            encodings = face_recognition.face_encodings(imagen_rgb, cajas_rostros)
            encodings_conocidos.append(encodings[0])
            nombres_conocidos.append(nombre_persona)

# Guardar los encodings y nombres en el archivo .pickle
print("[INFO] Guardando encodings en el disco...")
datos = {"encodings": encodings_conocidos, "nombres": nombres_conocidos}

with open("rostros_entrenados.pickle", "wb") as f:
    f.write(pickle.dumps(datos))

print("[INFO] ¡Archivo 'rostros_entrenados.pickle' creado con éxito!")