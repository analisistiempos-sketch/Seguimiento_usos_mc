import sys

import config
import enviar_correo
import enviar_whatsapp


def main():
    ruta = enviar_whatsapp.generar_imagen()
    asunto = "Resumen de usos"
    cuerpo = (
        "Resumen de usos del sistema de transporte.\n"
        "Se adjunta la imagen del tablero (comparación horaria y últimos 21 días)."
    )

    enviado = []
    if config.WHATSAPP_NUMERO:
        enviar_whatsapp.enviar(config.WHATSAPP_NUMERO, ruta)
        enviado.append("WhatsApp")
    else:
        print("[AVISO] Sin USOS_WHATSAPP_NUMERO; no se envía por WhatsApp.")

    try:
        enviar_correo.enviar_correo(asunto, cuerpo, adjunto=ruta)
        enviado.append("Correo")
    except Exception as e:
        print(f"[ERROR] Correo: {e}")

    print("Enviado por: " + (", ".join(enviado) if enviado else "nada"))
    if not enviado:
        sys.exit(1)


if __name__ == "__main__":
    main()
