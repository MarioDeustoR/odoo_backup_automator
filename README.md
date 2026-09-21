# 📦 Odoo Backup Automator

Una herramienta de automatización robusta escrita en Python para descargar de forma desatendida copias de seguridad desde el portal de suscripciones de Odoo. Diseñada con un enfoque estricto en la resiliencia de ejecución, la seguridad de las credenciales y la limpieza absoluta de la memoria del servidor.

## ✨ Características Principales

* **Evasión Avanzada de Antibots:** Implementa `undetected-chromedriver` para superar las barreras de Cloudflare y la protección nativa del motor de login de Odoo.
* **Gestión Estricta de Memoria (Anti-Zombies):** Previene fugas de memoria (*Memory Leaks*) en sistemas Windows mediante el cierre selectivo de subprocesos por PID, complementado con un barrido dinámico de PowerShell para aniquilar instancias huérfanas de Chrome asociadas al perfil de la tarea.
* **Seguridad Zero-Trust:** Las credenciales de acceso se inyectan en tiempo de ejecución mediante variables de entorno del sistema, eliminando por completo la existencia de contraseñas *hardcodeadas* en el código fuente.
* **Autopsia Forense de Errores:** Si la ejecución falla (ej. caída de red o actualización del DOM de Odoo), el script genera volcados de emergencia: captura de pantalla visual, código HTML de la página, texto renderizado y un *stacktrace* completo para depuración rápida.
* **Mantenimiento Autónomo:** Rotación automática de archivos (7 días de retención de copias) y sistema de protección para evitar la sobreescritura de backups antiguos.

## ⚙️ Requisitos Previos

* **Python 3.10+**
* **Google Chrome** instalado en el sistema.
* Dependencias requeridas:
  ```bash
  pip install undetected-chromedriver selenium
