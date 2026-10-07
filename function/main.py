import hashlib
import hmac
import json
import logging
import os
import time
import urllib.parse
import urllib.request

import functions_framework


# Configuramos el logger para enviar los mensajes a stdout,
# que es capturado automáticamente por Cloud Logging.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    force=True,
)

logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def process_file_upload(cloud_event):
    """
    Procesa el evento generado cuando se carga un archivo
    en Cloud Storage.

    Flujo:
    Cloud Storage
        -> Cloud Function
        -> Webhook seguro HMAC
        -> Google Apps Script
        -> Google Sheets
        -> Gmail
    """

    try:
        data = cloud_event.data

        file_name = data.get("name")
        file_size = data.get("size")
        content_type = data.get("contentType")
        bucket_name = data.get("bucket")

        logger.info(
            "Evento de Cloud Storage recibido | "
            "bucket=%s | nombre=%s | tamaño=%s bytes | tipo=%s",
            bucket_name,
            file_name,
            file_size,
            content_type,
        )

        # Validamos los datos recibidos desde Cloud Storage.
        validar_metadatos(
            file_name,
            file_size,
            content_type,
            bucket_name,
        )

        # Construimos el payload que enviaremos a Apps Script.
        payload = {
            "name": file_name,
            "size": file_size,
            "contentType": content_type,
            "bucket": bucket_name,
        }

        # Enviamos los metadatos mediante el webhook seguro.
        respuesta = enviar_metadatos_apps_script(payload)

        logger.info(
            "Archivo procesado correctamente | "
            "nombre=%s | respuesta_webhook=%s",
            file_name,
            respuesta,
        )

        return {
            "status": "success",
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "bucket": bucket_name,
            "webhook_response": respuesta,
        }

    except Exception:
        logger.exception(
            "Error al procesar el evento de carga del archivo."
        )
        raise


def validar_metadatos(
    file_name,
    file_size,
    content_type,
    bucket_name,
):
    """
    Valida los metadatos mínimos recibidos desde Cloud Storage.
    """

    if not file_name:
        raise ValueError(
            "El evento no contiene el nombre del archivo."
        )

    if not bucket_name:
        raise ValueError(
            "El evento no contiene el nombre del bucket."
        )

    if file_size is None or file_size == "":
        raise ValueError(
            "El evento no contiene el tamaño del archivo."
        )

    if not content_type:
        raise ValueError(
            "El evento no contiene el tipo MIME del archivo."
        )

    try:
        size = int(file_size)
    except (TypeError, ValueError):
        raise ValueError(
            "El tamaño del archivo no es válido."
        )

    if size < 0:
        raise ValueError(
            "El tamaño del archivo no puede ser negativo."
        )


def generar_firma(payload):
    """
    Genera una firma HMAC-SHA256 utilizando el secreto
    almacenado en Google Secret Manager.

    El secreto se obtiene mediante la variable de entorno
    WEBHOOK_SECRET.
    """

    secreto = os.environ.get("WEBHOOK_SECRET")

    if not secreto:
        raise RuntimeError(
            "No está configurado el secreto WEBHOOK_SECRET."
        )

    firma = hmac.new(
        secreto.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return firma


def enviar_metadatos_apps_script(datos):
    """
    Envía los metadatos del archivo al Web App de Apps Script.

    La comunicación utiliza HTTPS y una firma HMAC-SHA256
    para validar la autenticidad e integridad del mensaje.
    """

    webhook_url = os.environ.get(
        "APPS_SCRIPT_WEBHOOK_URL"
    )

    if not webhook_url:
        raise RuntimeError(
            "No está configurada la variable "
            "APPS_SCRIPT_WEBHOOK_URL."
        )

    # Convertimos el objeto a JSON.
    payload = json.dumps(
        datos,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    # Generamos la firma sobre el payload exacto.
    firma = generar_firma(payload)

    # Apps Script recibe la firma mediante el parámetro
    # "signature".
    parametros = urllib.parse.urlencode(
        {
            "signature": firma
        }
    )

    url = f"{webhook_url}?{parametros}"

    request = urllib.request.Request(
        url,
        data=payload.encode("utf-8"),
        headers={
            "Content-Type": "application/json",
        },
        method="POST",
    )

    inicio = time.perf_counter()

    try:
        with urllib.request.urlopen(
            request,
            timeout=30,
        ) as response:

            response_body = response.read().decode(
                "utf-8"
            )

            status_code = response.status

    except Exception:
        tiempo_ms = (
            time.perf_counter() - inicio
        ) * 1000

        logger.exception(
            "Error al comunicarse con Apps Script | "
            "tiempo_ms=%.2f",
            tiempo_ms,
        )

        raise

    tiempo_ms = (
        time.perf_counter() - inicio
    ) * 1000

    logger.info(
        "Webhook Apps Script respondido | "
        "status=%s | tiempo_ms=%.2f",
        status_code,
        tiempo_ms,
    )

    if status_code < 200 or status_code >= 300:
        raise RuntimeError(
            "Apps Script respondió con código HTTP "
            f"{status_code}."
        )

    try:
        respuesta = json.loads(response_body)
    except json.JSONDecodeError:
        raise RuntimeError(
            "Apps Script devolvió una respuesta que "
            "no es JSON válido."
        )

    if respuesta.get("status") != "success":
        raise RuntimeError(
            "Apps Script rechazó los metadatos: "
            f"{respuesta.get('message', 'Error desconocido')}."
        )

    return respuesta

