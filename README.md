## Sistema de detección facial

A veces, los tutores no saben a qué hora sus hijos entran o salen de la escuela.
Este sistema resuelve este problema detectando los rostros

#### ¿Cómo funciona?

Primero, el archivo entrenar.py lee las imágenes de la carpeta rostros, obteniendo los datos biométricos por separado de cada alumno. Estos datos se almacenan en un archivo .pickle para aumentar la velocidad de lectura por el sistema en vivo.
El archivo reconocer.py detecta en vivo lo que recibe en la cámara y lo compara con el archivo.pickle: ¿la persona existe en estos datos? Envía un mensaje al número asociado a esa persona en la base de datos, dependiendo de si va entrando o saliendo manda un mensaje u otro. ¿La persona no existe en esos datos? La marca como desconocida.