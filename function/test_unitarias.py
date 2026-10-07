import hashlib
import hmac
import logging

import pytest

from main import (
    generar_firma,
    process_file_upload,
)


class MockCloudEvent:
    def __init__(self, data):
        self.data = data


def test_process_file_upload_success(caplog, monkeypatch):
    """Verifica que un archivo válido sea procesado correctamente."""

    def mock_enviar_metadatos(datos):
        return {
            "status": "success",
            "message": "Metadatos recibidos correctamente.",
            "file_name": datos["name"],
        }

    monkeypatch.setattr(
        "main.enviar_metadatos_apps_script",
        mock_enviar_metadatos,
    )

    event = MockCloudEvent(
        {
            "name": "documento.pdf",
            "size": "2048",
            "contentType": "application/pdf",
            "bucket": "test-bucket",
        }
    )

    with caplog.at_level(logging.INFO):
        result = process_file_upload(event)

    assert result["status"] == "success"
    assert result["file_name"] == "documento.pdf"
    assert result["file_size"] == "2048"
    assert result["content_type"] == "application/pdf"
    assert result["bucket"] == "test-bucket"

    assert result["webhook_response"]["status"] == "success"

    assert "Evento de Cloud Storage recibido" in caplog.text
    assert "Archivo procesado correctamente" in caplog.text


def test_process_file_upload_missing_file_name():
    """Verifica que se genere un error si falta el nombre del archivo."""

    event = MockCloudEvent(
        {
            "size": "2048",
            "contentType": "application/pdf",
            "bucket": "test-bucket",
        }
    )

    with pytest.raises(
        ValueError,
        match="El evento no contiene el nombre del archivo.",
    ):
        process_file_upload(event)


def test_process_file_upload_empty_event():
    """Verifica que un evento vacío sea rechazado correctamente."""

    event = MockCloudEvent({})

    with pytest.raises(
        ValueError,
        match="El evento no contiene el nombre del archivo.",
    ):
        process_file_upload(event)


def test_generar_firma_hmac(monkeypatch):
    """Verifica que la firma HMAC-SHA256 se genere correctamente."""

    secreto = "secreto-de-prueba"
    payload = '{"name":"documento.pdf","size":"2048"}'

    monkeypatch.setenv(
        "WEBHOOK_SECRET",
        secreto,
    )

    resultado = generar_firma(payload)

    esperado = hmac.new(
        secreto.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert resultado == esperado


def test_generar_firma_sin_secreto(monkeypatch):
    """Verifica que falle si no existe WEBHOOK_SECRET."""

    monkeypatch.delenv(
        "WEBHOOK_SECRET",
        raising=False,
    )

    with pytest.raises(
        RuntimeError,
        match="No está configurado el secreto WEBHOOK_SECRET.",
    ):
        generar_firma("payload-de-prueba")