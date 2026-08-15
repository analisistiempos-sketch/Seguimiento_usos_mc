import sys
import time
from pathlib import Path

import config
import data_loader
import resumen_image

RUTA_IMAGEN = Path(__file__).resolve().parent / "resumen_usos.jpg"
SESSION = Path(__file__).resolve().parent / "whatsapp_edge_session"


def generar_imagen():
    actualizacion = data_loader.fecha_actualizacion()
    titulo = f"Datos actualizados al: {actualizacion.strftime('%d/%m/%Y %I:%M %p')}" if actualizacion else "Resumen de usos"
    resumen_image.exportar_jpeg(RUTA_IMAGEN, titulo)
    return RUTA_IMAGEN


def setup_edge():
    from selenium import webdriver
    from selenium.webdriver.edge.options import Options

    options = Options()
    options.add_argument(f"user-data-dir={SESSION}")
    options.add_argument("--profile-directory=Default")
    options.add_argument("--log-level=3")
    options.add_argument("--silent")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    return webdriver.Edge(options=options)


def enviar(numero, ruta_imagen):
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    if not numero:
        raise RuntimeError("Falta USOS_WHATSAPP_NUMERO (número en formato internacional, ej: 573504809507).")

    driver = setup_edge()
    wait = WebDriverWait(driver, 120)
    try:
        driver.get("https://web.whatsapp.com")
        try:
            wait.until(EC.presence_of_element_located((By.ID, "side")))
            print("Sesión detectada.")
        except Exception:
            raise RuntimeError("No hay sesión de WhatsApp Web. Abre el navegador, escanea el QR y reintenta.")
        time.sleep(4)

        driver.get(f"https://web.whatsapp.com/send?phone={numero}")
        wait.until(EC.presence_of_element_located(
            (By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
        ))
        time.sleep(3)

        driver.find_element(By.XPATH, '//button[@aria-label="Adjuntar"]').click()
        time.sleep(2)
        driver.execute_script(
            "Array.from(document.querySelectorAll('*')).find(e => e.innerText && e.innerText.trim()==='Fotos y videos')?.click();"
        )
        time.sleep(2)
        input_media = driver.find_element(
            By.XPATH, '//input[contains(@accept, "video/mp4")]'
        )
        input_media.send_keys(str(ruta_imagen))
        print("Imagen adjuntada (Fotos y videos), esperando vista previa...")

        time.sleep(5)
        enviado = False
        for intento in range(3):
            resultado = driver.execute_script("""
                const el = document.querySelector('*[aria-label*="Enviar"]')
                          || document.querySelector('[data-icon="wds-ic-send-filled"]')
                          || document.querySelector('[data-icon="send"]');
                if (!el) return 'no_elemento';
                const btn = el.closest('button') || el.closest('[role="button"]') || el;
                btn.click();
                return 'click';
            """)
            if resultado == "no_elemento":
                break
            time.sleep(5)
            quedan = driver.execute_script(
                "return document.querySelectorAll('*[aria-label*=\"Enviar\"], [data-icon=\"wds-ic-send-filled\"], [data-icon=\"send\"]').length"
            )
            if quedan == 0:
                enviado = True
                break

        if not enviado:
            try:
                caja = driver.find_element(By.XPATH, '//div[@contenteditable="true"][@data-tab="10"]')
                caja.send_keys(Keys.ENTER)
                time.sleep(5)
                quedan = driver.execute_script(
                    "return document.querySelectorAll('*[aria-label*=\"Enviar\"], [data-icon=\"wds-ic-send-filled\"], [data-icon=\"send\"]').length"
                )
                enviado = quedan == 0
            except Exception:
                pass

        if not enviado:
            raise RuntimeError("No se pudo confirmar el envío de la imagen.")

        time.sleep(4)
        print("Enviado OK")
        return True
    finally:
        try:
            driver.quit()
        except Exception:
            pass


def main():
    if not config.WHATSAPP_NUMERO:
        print("[ERROR] Configura USOS_WHATSAPP_NUMERO (número internacional, ej: 573504809507).")
        sys.exit(1)
    ruta = generar_imagen()
    print(f"Imagen: {ruta}")
    enviar(config.WHATSAPP_NUMERO, ruta)


if __name__ == "__main__":
    main()
