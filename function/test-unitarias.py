import logging

import pytest

from main import process_file_upload


class MockCloudEvent:
    def __init__(self, data):
        self.data = data


def test_process_file_upload_success(caplog):
    """Verifica que un archivo válido sea procesado correctamente."""

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