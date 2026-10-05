import logging

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

    El evento contiene directamente los metadatos principales
    del objeto, por lo que no es necesario realizar otra
    consulta a Cloud Storage únicamente para obtenerlos.
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

        if not file_name:
            raise ValueError(
                "El evento no contiene el nombre del archivo."
            )

        logger.info(
            "Archivo procesado correctamente | nombre=%s",
            file_name,
        )

        return {
            "status": "success",
            "file_name": file_name,
            "file_size": file_size,
            "content_type": content_type,
            "bucket": bucket_name,
        }

    except Exception:
        logger.exception(
            "Error al procesar el evento de carga del archivo."
        )
        raise