<?php
session_start(); // Obligatorio para leer la sesión
?>

<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Control Escolar IA</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            height: 100vh;
            margin: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            color: white;
        }
        .hero {
            text-align: center;
            background: rgba(255, 255, 255, 0.1);
            padding: 30px;
            border-radius: 20px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            max-width: 500px;
            width: 90%;
        }
        .logo-container img {
            max-width: 200px;
            height: auto;
            margin-bottom: 1px;
            border-radius: 15px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        h1 { font-size: 2.5rem; margin-bottom: 5px; }
        p { font-size: 1.1rem; opacity: 0.9; margin-bottom: 20px; }
        
        .btn-start {
            display: inline-block;
            background: #28a745;
            color: white;
            text-decoration: none;
            padding: 15px 40px;
            font-size: 1.2rem;
            font-weight: bold;
            border-radius: 50px;
            transition: transform 0.3s, background 0.3s;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
        }
        .btn-start:hover {
            background: #218838;
            transform: translateY(-3px);
        }
    </style>
</head>
<body>

<div class="hero">
    <?php  
            if (isset($_SESSION['status'])) {
            echo "<div style='background: #d4edda; color: green; padding: 5px; border-radius: 8px; text-align: center; margin: 20px auto; max-width: 450px; font-weight: bold; border: 1px solid #c3e6cb;'>";
            echo $_SESSION['status'];
            echo "</div>";
            
            // 3. Importante: Borrar el mensaje para que no salga siempre
            unset($_SESSION['status']);
        }
    ?>
    <div class="logo-container">
        <img src="codigo.png" alt="Logo Sistema">
    </div>
    <h1>Bienvenido</h1>
    <p>Sistema de Control de Acceso mediante Inteligencia Artificial y Reconocimiento Facial.</p>
    
    <a href="registro.php" class="btn-start">Comenzar Registro</a>
</div>

</body>
</html>