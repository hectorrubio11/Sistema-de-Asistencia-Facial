<?php
session_start();
$host = "localhost"; $user = "root"; $pass = ""; $db = "sistema_facial";
$conn = new mysqli($host, $user, $pass, $db);
$mensaje = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {
    $nombre = mysqli_real_escape_string($conn, $_POST['nombre']);
    $telefono = mysqli_real_escape_string($conn, $_POST['telefono']);
    $fotos_capturadas = $_POST['fotos_base64']; 

    // Guardamos con el +521 para asegurar compatibilidad con Twilio
    $sql = "INSERT INTO usuarios (nombre, telefono) VALUES ('$nombre', '+521$telefono')";
    
    if ($conn->query($sql) === TRUE) {
        $ruta_carpeta = "rostros/" . $nombre . "/";
        if (!file_exists($ruta_carpeta)) mkdir($ruta_carpeta, 0777, true);

        // 1. Guardar fotos desde el input file (Galería)
        if (isset($_FILES['fotos_archivo'])) {
            foreach ($_FILES['fotos_archivo']['tmp_name'] as $key => $tmp_name) {
                if ($_FILES['fotos_archivo']['name'][$key] != "") {
                    $ext = pathinfo($_FILES['fotos_archivo']['name'][$key], PATHINFO_EXTENSION);
                    move_uploaded_file($tmp_name, $ruta_carpeta . "file_" . time() . "_$key." . $ext);
                }
            }
        }

        // 2. Guardar fotos capturadas con la cámara en vivo
        if (!empty($fotos_capturadas)) {
            $fotos_array = json_decode($fotos_capturadas);
            foreach ($fotos_array as $index => $base64) {
                $base64 = str_replace('data:image/jpeg;base64,', '', $base64);
                $datos = base64_decode($base64);
                file_put_contents($ruta_carpeta . "cam_" . time() . "_$index.jpg", $datos);
            }
        }
        $_SESSION['status'] = "¡Registro exitoso para $nombre!";
        header("Location: index.php");
        exit();
    } else {
        $mensaje = "Error en BD: " . $conn->error;
    }
}
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Registro IA Facial</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f0f2f5; margin: 0; padding: 10px; display: flex; justify-content: center; }
        .card { background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); width: 100%; max-width: 450px; }
        h2 { text-align: center; color: #333; margin-top: 0; }
        
        .video-wrapper { position: relative; width: 100%; background: #000; border-radius: 10px; overflow: hidden; aspect-ratio: 4/3; }
        video { width: 100%; height: 100%; object-fit: cover; transform: scaleX(-1); } /* Efecto espejo para selfies */
        
        .preview-container { display: flex; gap: 8px; overflow-x: auto; padding: 10px 0; min-height: 80px; }
        .preview-container img { width: 70px; height: 70px; object-fit: cover; border-radius: 8px; border: 2px solid #28a745; }
        
        input, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 8px; border: 1px solid #ddd; box-sizing: border-box; font-size: 16px; }
        button { background: #007bff; color: white; border: none; font-weight: bold; cursor: pointer; transition: 0.3s; }
        .btn-capture { background: #28a745; margin-bottom: 15px; }
        .btn-submit { background: #1a1a1a; margin-top: 20px; font-size: 18px; }
        label { font-size: 14px; font-weight: bold; color: #555; display: block; margin-top: 10px; }
        .contador { font-size: 14px; text-align: center; color: #666; font-weight: bold; }
    </style>
</head>
<body>

<div class="card">
    <h2>Registro de Rostro</h2>
    <div class="row" style="display: flex; justify-content: center;">
        <img src="codigo.png" height="300">
    </div>
    <form id="registroForm" method="POST" enctype="multipart/form-data">
        <input type="text" name="nombre" placeholder="Nombre de la persona" required>
        <input type="number" name="telefono" placeholder="WhatsApp (10 dígitos: 669...)" required>
        
        <label>Opción 1: Seleccionar de la Galería</label>
        <input type="file" name="fotos_archivo[]" multiple accept="image/*">

        <hr>
        <label>Opción 2: Tomar fotos en vivo</label>
        <div class="video-wrapper">
            <video id="video" autoplay playsinline muted></video>
        </div>
        <button type="button" class="btn-capture" id="snap">📸 Capturar Rostro</button>
        <div class="contador" id="txtContador">Fotos capturadas: 0</div>
        <div class="preview-container" id="previsualizacion"></div>
        
        <input type="hidden" name="fotos_base64" id="fotos_base64">
        <button type="submit" class="btn-submit">GUARDAR EN SISTEMA</button>
    </form>
    <?php echo $mensaje; ?>
</div>

<!-- El canvas se mantiene oculto -->
<canvas id="canvas" style="display:none;"></canvas>

<script>
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    const snap = document.getElementById('snap');
    const previsualizacion = document.getElementById('previsualizacion');
    const fotosInput = document.getElementById('fotos_base64');
    const txtContador = document.getElementById('txtContador');
    let listaFotos = [];

    // 'facingMode: user' solicita explícitamente la cámara frontal (selfie)
    const constraints = {
        video: { facingMode: "user", width: { ideal: 1280 }, height: { ideal: 720 } }
    };

    navigator.mediaDevices.getUserMedia(constraints)
        .then(stream => { 
            video.srcObject = stream; 
        })
        .catch(err => { 
            console.error(err);
            alert("Error: Para usar la cámara, accede mediante HTTPS o localhost, y acepta los permisos."); 
        });

    snap.addEventListener('click', () => {
        const context = canvas.getContext('2d');
        
        // CORRECCIÓN CLAVE: Ajustamos el canvas al tamaño real del flujo de video actual
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Dibujamos manteniendo la proporción exacta
        context.drawImage(video, 0, 0, canvas.width, canvas.height);
        
        // Extraemos en formato JPEG de buena calidad
        const dataURL = canvas.toDataURL('image/jpeg', 0.85);
        
        listaFotos.push(dataURL);
        
        // Crear elemento visual de previsualización
        const img = document.createElement('img');
        img.src = dataURL;
        previsualizacion.appendChild(img);
        
        // Actualizar contador y el input oculto
        txtContador.innerText = `Fotos capturadas: ${listaFotos.length}`;
        fotosInput.value = JSON.stringify(listaFotos);
    });
</script>

</body>
</html>