import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import time
import os
import re
import glob
import sys
import datetime
import traceback
import subprocess
import winreg

# --- INTERCEPTOR DE CONSOLA Y LOG ---
class DobleSalida:
    def __init__(self, ruta_log):
        self.consola = sys.stdout
        self.archivo_log = open(ruta_log, "a", encoding="utf-8")

    def write(self, mensaje):
        self.consola.write(mensaje)
        self.archivo_log.write(mensaje)
        self.archivo_log.flush()

    def flush(self):
        self.consola.flush()

fecha_actual = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
ruta_txt_log = rf"S:\CopiaSeg\Odoo\log_odoo_{fecha_actual}.txt"

sys.stdout = DobleSalida(ruta_txt_log)
sys.stderr = sys.stdout
# -------------------------------------------

# 1. Credenciales por variable de entorno (ya NO en texto plano en el script).
CORREO = os.environ.get("ODOO_BACKUP_USER")
PASSWORD = os.environ.get("ODOO_BACKUP_PASS")
RUTA_LOCAL = r"S:\CopiaSeg\Odoo"
PERFIL_CHROME = rf"{RUTA_LOCAL}\PerfilChrome"

if not CORREO or not PASSWORD:
    print("[!] Faltan las variables de entorno ODOO_BACKUP_USER / ODOO_BACKUP_PASS.")
    print("    Configuralas UNA VEZ, como administrador, con:")
    print('      setx ODOO_BACKUP_USER "tu_correo" /M')
    print('      setx ODOO_BACKUP_PASS "tu_contraseña" /M')
    print("    y vuelve a lanzar el script (o el Programador de tareas) para que las recoja.")
    sys.exit(1)


def limpiar_chrome_residual(filtro_ruta):
    """Busca y mata cualquier chrome.exe que siga vivo usando ESTE perfil en
    concreto (lo identifica por su --user-data-dir en la linea de comandos),
    sin tocar otras ventanas de Chrome del servidor."""
    try:
        ruta_script = os.path.join(os.environ.get("TEMP", RUTA_LOCAL), "limpiar_chrome_odoo.ps1")
        contenido_ps1 = (
            "$procesos = @(Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" "
            "| Where-Object { $_.CommandLine -like '*RUTA_FILTRO*' })\n"
            "$procesos | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }\n"
            "Write-Output $procesos.Count\n"
        ).replace("RUTA_FILTRO", filtro_ruta)

        with open(ruta_script, "w", encoding="utf-8") as f:
            f.write(contenido_ps1)

        resultado = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ruta_script],
            capture_output=True, text=True, timeout=30
        )
        n = resultado.stdout.strip() or "0"
        print(f"    -> Barrido de Chrome: {n} proceso(s) chrome.exe de este perfil eliminado(s).")
        return n
    except Exception as e:
        print(f"    -> No se pudo hacer el barrido de Chrome: {e}")
        return None


def detectar_version_chrome():
    """Detecta la version MAYOR de Chrome instalada AHORA MISMO en el
    servidor. Prueba varias estrategias porque las rutas fijas de Program
    Files no encontraron nada en este servidor (probablemente Chrome esta
    instalado a nivel de usuario, no de maquina):
      1. Registro: HKCU/HKLM ...\\Google\\Chrome\\BLBeacon\\version (Chrome
         mantiene ahi su version actual, sin necesitar saber la ruta del .exe)
      2. Registro: App Paths\\chrome.exe (da la ruta real al ejecutable,
         la registra el propio instalador este donde este)
      3. Rutas habituales, incluida la instalacion por-usuario en
         %LOCALAPPDATA% (la mas probable si no esta en Program Files)
    """
    # Estrategia 1: version directa desde el registro
    claves_version = [
        (winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Google\Chrome\BLBeacon"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Google\Chrome\BLBeacon"),
    ]
    for hive, subkey in claves_version:
        try:
            with winreg.OpenKey(hive, subkey) as clave:
                version_str, _ = winreg.QueryValueEx(clave, "version")
                m = re.match(r"(\d+)\.", version_str)
                if m:
                    return int(m.group(1))
        except Exception:
            pass

    # Estrategia 2: ruta del ejecutable via App Paths
    rutas_candidatas = []
    claves_apppaths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
    ]
    for hive, subkey in claves_apppaths:
        try:
            with winreg.OpenKey(hive, subkey) as clave:
                ruta, _ = winreg.QueryValueEx(clave, "")
                if ruta:
                    rutas_candidatas.append(ruta)
        except Exception:
            pass

    # Estrategia 3: rutas habituales, incluida la instalacion por-usuario
    rutas_candidatas += [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
    ]

    for ruta in rutas_candidatas:
        if ruta and os.path.exists(ruta):
            try:
                salida = subprocess.check_output([ruta, "--version"], text=True, timeout=10)
                m = re.search(r"(\d+)\.", salida)
                if m:
                    return int(m.group(1))
            except Exception:
                pass

    return None  # si nada funciono, undetected_chromedriver decide solo


opciones = uc.ChromeOptions()
opciones.add_argument("--window-size=1920,1080")

prefs = {
    "download.default_directory": RUTA_LOCAL,
    "download.prompt_for_download": False,
    "download.directory_upgrade": True,
    "safebrowsing.enabled": False,
    "safebrowsing.disable_download_protection": True,
    "credentials_enable_service": False,
    "profile.password_manager_enabled": False
}
opciones.add_experimental_option("prefs", prefs)

VERSION_CHROME = detectar_version_chrome()
if VERSION_CHROME:
    print(f"[Info] Chrome instalado detectado: versión {VERSION_CHROME}")
else:
    print("[Info] No se pudo detectar la versión de Chrome instalada; se deja la autodetección de undetected_chromedriver.")

# Limpieza PREVENTIVA, antes de intentar arrancar nada: si una ejecucion
# anterior fallo justo al crear el driver (como el desajuste de version del
# 23/09), puede quedar un chrome.exe a medias bloqueando el perfil, y Chrome
# se niega a arrancar con "Lock file can not be created / Aborting now to
# avoid profile corruption". Limpiamos ANTES de intentarlo, no solo despues.
print("[Info] Comprobando que no haya procesos de una ejecución anterior...")
limpiar_chrome_residual(PERFIL_CHROME)

driver = None
chromedriver_pid = None
hubo_error = False

try:
    # uc.Chrome() va DENTRO del try (antes estaba fuera): si fallaba aqui
    # -- como con el desajuste de version del 23/09 -- el finally nunca se
    # ejecutaba, y el chrome.exe que UC ya habia lanzado internamente se
    # quedaba huerfano, bloqueando el perfil en el siguiente intento. Ahora
    # cualquier fallo aqui pasa por la misma limpieza que todo lo demas.
    driver = uc.Chrome(
        options=opciones,
        user_data_dir=PERFIL_CHROME,
        version_main=VERSION_CHROME
    )

    try:
        chromedriver_pid = driver.service.process.pid
    except Exception:
        chromedriver_pid = None

    # 0. Proteger backups anteriores (Evitar sobreescritura)
    print("[0/6] Preparando el directorio y protegiendo copias anteriores...")
    for archivo in glob.glob(os.path.join(RUTA_LOCAL, "*.zip")):
        timestamp = os.path.getmtime(archivo)
        fecha_str = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d_%H-%M-%S')

        if fecha_str not in archivo:
            nombre_base, ext = os.path.splitext(archivo)
            nuevo_nombre = f"{nombre_base}_{fecha_str}{ext}"
            try:
                os.rename(archivo, nuevo_nombre)
                print(f"    -> Archivo anterior asegurado como: {os.path.basename(nuevo_nombre)}")
            except:
                pass

    zips_previos = set(glob.glob(os.path.join(RUTA_LOCAL, "*.zip")))

    print("[1/6] Accediendo al portal de Odoo...")
    driver.get("https://alarca-group.odoo.com/web")

    # 2. Login optimizado
    try:
        caja_email = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "login")))
        print("    Formulario detectado. Introduciendo credenciales...")
        caja_email.send_keys(CORREO)

        caja_password = driver.find_element(By.ID, "password")
        caja_password.send_keys(PASSWORD)
        time.sleep(1)
        caja_password.send_keys(Keys.ENTER)

        WebDriverWait(driver, 20).until(lambda d: "/web/login" not in d.current_url)
    except TimeoutException:
        if "/web/login" in driver.current_url:
            raise Exception(
                "No aparecio el formulario de login y seguimos en /web/login: "
                "fallo real de inicio de sesion, no sesion guardada."
            )
        print("    Sesión guardada detectada. Saltando el inicio de sesión...")

    # NUEVO PASO MEJORADO: Navegamos a la suscripción con JS para no romper Odoo
    print("    -> Redirigiendo a la gestión de copias de seguridad...")
    try:
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, "header, .o_main_navbar, nav")))
    except:
        pass

    driver.execute_script("window.location.assign('https://alarca-group.odoo.com/odoo/my-subscription');")
    time.sleep(8)

    # 3. Entrando al iframe (con DOS reintentos si no aparece)
    try:
        WebDriverWait(driver, 30).until(
            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='Mi suscripción']"))
        )
    except TimeoutException:
        intentos_iframe = [
            ("refrescar la página", lambda: driver.refresh()),
            ("renavegar desde cero", lambda: driver.execute_script(
                "window.location.assign('https://alarca-group.odoo.com/odoo/my-subscription');"
            )),
        ]
        exito_iframe = False
        for nombre_intento, accion in intentos_iframe:
            print(f"    [!] La interfaz de Odoo no ha cargado. Intentando: {nombre_intento}...")
            try:
                accion()
                time.sleep(10)
                WebDriverWait(driver, 30).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe[title='Mi suscripción']"))
                )
                exito_iframe = True
                break
            except TimeoutException:
                continue
        if not exito_iframe:
            raise TimeoutException(
                "El iframe 'Mi suscripción' no aparecio tras refrescar y renavegar desde cero."
            )

    time.sleep(6)

    # 4. Scroll progresivo (con limite de seguridad para evitar un bucle sin fin)
    print("[4/6] Forzando la carga de la interfaz inferior...")
    alto_total = driver.execute_script("return document.body.scrollHeight")
    posicion = 0
    pasos = 0
    while posicion < alto_total:
        posicion += 400
        driver.execute_script(f"window.scrollTo(0, {posicion});")
        time.sleep(0.3)
        alto_total = driver.execute_script("return document.body.scrollHeight")
        pasos += 1
        if pasos > 50:
            print("    Aviso: se corto el scroll tras 50 pasos (limite de seguridad).")
            break
    time.sleep(2)

    # 5. Localizar el botón y hacer un CLIC ROBUSTO
    print("[5/6] Disparando la orden de volcado al servidor...")

    xpath_boton = "//a[contains(normalize-space(.), 'Descargar copia')] | //button[contains(normalize-space(.), 'Descargar copia')]"

    try:
        boton_backup = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.XPATH, xpath_boton))
        )

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton_backup)
        time.sleep(2)

        print("    -> Ejecutando clic seguro sobre el botón...")
        try:
            boton_backup.click()
        except Exception:
            boton_backup.send_keys(Keys.ENTER)

    except Exception as error_boton:
        print(f"    -> [!] Fallo al localizar el botón principal.")
        raise error_boton

    print("\n¡Petición enviada! Monitorizando la carpeta...")

    try:
        driver.switch_to.default_content()
    except:
        pass

    tiempo_inicio = time.time()
    limite_espera = 2700  # 45 minutos máximos
    descarga_completada = False
    pico_maximo_mb = 0

    while (time.time() - tiempo_inicio) < limite_espera:
        descargas_activas = glob.glob(os.path.join(RUTA_LOCAL, "*.crdownload")) + glob.glob(os.path.join(RUTA_LOCAL, "*.tmp"))
        zips_actuales = set(glob.glob(os.path.join(RUTA_LOCAL, "*.zip")))
        nuevos_zips = zips_actuales - zips_previos

        if nuevos_zips and not descargas_activas:
            archivo_final = list(nuevos_zips)[0]
            print(f"\n[OK] ¡Descarga completada y verificada con éxito!")
            print(f"     Archivo guardado en: {archivo_final}")
            descarga_completada = True
            break

        if descargas_activas:
            try:
                tamano_mb = os.path.getsize(descargas_activas[0]) / (1024 * 1024)
                if tamano_mb > pico_maximo_mb:
                    pico_maximo_mb = tamano_mb
                print(f"    -> [Descargando] Archivo recibiendo datos. Tamaño actual: {tamano_mb:.2f} MB")
            except Exception:
                pass

        elif not descargas_activas and not nuevos_zips:
            print(f"    -> [Esperando] Odoo está comprimiendo el ZIP en su servidor. Aún no hay descarga...")

        if pico_maximo_mb > 0 and not descargas_activas and not nuevos_zips:
            print(f"\n[!] ERROR CRÍTICO: La descarga se cortó abruptamente tras alcanzar {pico_maximo_mb:.2f} MB.")
            print("    Causa probable: Microcorte de red local o el servidor de Odoo cerró la conexión.")
            raise Exception("Descarga interrumpida por caída de red.")

        time.sleep(10)

    if not descarga_completada:
        if (time.time() - tiempo_inicio) >= limite_espera:
            print("\n[!] ALERTA: Se agotaron los 45 minutos de espera máxima.")
        else:
            print("\n[!] ALERTA: La monitorización se interrumpió de forma anormal.")

    # 6. Limpieza automática (7 días) — solo si el backup de hoy salió bien
    if descarga_completada:
        print("\n[6/6] Tareas de mantenimiento: Limpiando copias antiguas...")
        limite_tiempo = time.time() - (7 * 86400)

        for archivo_zip in glob.glob(os.path.join(RUTA_LOCAL, "*.zip")):
            if os.path.getmtime(archivo_zip) < limite_tiempo:
                try:
                    os.remove(archivo_zip)
                    print(f"    -> Eliminado backup antiguo: {os.path.basename(archivo_zip)}")
                except Exception as e:
                    print(f"    -> [!] No se pudo borrar {os.path.basename(archivo_zip)}: {e}")

        print("\n=== PROCESO FINALIZADO CON ÉXITO ===")
    else:
        hubo_error = True

except Exception as e:
    hubo_error = True
    print(f"\n[!] ERROR CRÍTICO: {e}")
    traceback.print_exc()

    if driver is not None:
        try:
            ruta_foto = rf"{RUTA_LOCAL}\error_vision_bot.png"
            driver.save_screenshot(ruta_foto)
            print(f"    Captura de pantalla guardada en: {ruta_foto}")
        except:
            pass

        try:
            ruta_html = rf"{RUTA_LOCAL}\error_pagina.html"
            with open(ruta_html, "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print(f"    HTML de la página guardado en: {ruta_html}")
        except:
            pass

        try:
            ruta_txt = rf"{RUTA_LOCAL}\error_texto_visible.txt"
            texto_visible = driver.find_element(By.TAG_NAME, "body").text
            with open(ruta_txt, "w", encoding="utf-8") as f:
                f.write(texto_visible)
            print(f"    Texto visible guardado en: {ruta_txt}")
        except:
            pass
    else:
        print("    (el driver nunca llego a crearse, no hay pagina que capturar)")

finally:
    print("\n[Mantenimiento] Cerrando el navegador y liberando memoria...")

    if driver is not None:
        try:
            driver.quit()
        except:
            pass

    try:
        if chromedriver_pid:
            os.system(f"taskkill /F /T /PID {chromedriver_pid} >nul 2>&1")
            print(f"    -> Proceso Chrome (PID {chromedriver_pid}) eliminado.")
    except:
        pass

    # Esto se ejecuta SIEMPRE, incluso si uc.Chrome() nunca llego a crear
    # 'driver' -- es la red que faltaba para el caso del 23/09.
    limpiar_chrome_residual(PERFIL_CHROME)

    print("    -> Finalizando proceso de Python...")
    os._exit(1 if hubo_error else 0)
