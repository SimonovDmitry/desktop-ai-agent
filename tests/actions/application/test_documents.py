import pytest

from deskagent.actions.application.documents import (
    OpenDocument,
    OpenMultipleDocuments,
    OpenURLWithApplication,
    RevealApplicationExecutable,
    RevealApplicationInFileManager,
)
from tests.application.conftest import assert_error, assert_success


def test_open_document(application_context):
    path = "/Users/me/document.pdf"
    application_context.services.application.open_document.return_value = None

    result = OpenDocument().execute(application_context, {"path": path})

    assert_success(result, {"opened": True, "path": path})
    application_context.services.application.open_document.assert_called_once_with(path)


def test_open_multiple_documents(application_context):
    paths = ["/Users/me/a.pdf", "/Users/me/b.pdf"]
    application_context.services.application.open_documents.return_value = None

    result = OpenMultipleDocuments().execute(
        application_context, {"paths": paths}
    )

    assert_success(
        result,
        {"opened": paths, "count": 2},
    )
    application_context.services.application.open_documents.assert_called_once_with(paths)


def test_open_multiple_documents_empty_list_is_rejected(application_context):
    result = OpenMultipleDocuments().execute(
        application_context, {"paths": []}
    )

    assert_error(result, "INVALID_INPUT")
    application_context.services.application.open_documents.assert_not_called()


def test_open_url_with_application(application_context):
    url = "https://youtube.com"
    application = "Google Chrome"
    application_context.services.application.open_url_with_application.return_value = None

    result = OpenURLWithApplication().execute(
        application_context,
        {"url": url, "application": application},
    )

    assert_success(
        result,
        {"opened": True, "url": url, "application": application},
    )
    application_context.services.application.open_url_with_application.assert_called_once_with(
        url, application
    )


@pytest.mark.parametrize(
    "action_cls, method, expected",
    [
        (
            RevealApplicationInFileManager,
            "reveal_application",
            {"revealed": True, "path": "/Applications/Safari.app"},
        ),
        (
            RevealApplicationExecutable,
            "reveal_application_executable",
            {
                "revealed": True,
                "path": "/Applications/Safari.app/Contents/MacOS/Safari",
            },
        ),
    ],
)
def test_reveal_application_actions(
    application_context, action_cls, method, expected
):
    getattr(application_context.services.application, method).return_value = expected["path"]

    result = action_cls().execute(
        application_context, {"application": "Safari"}
    )

    assert_success(result, expected)
    getattr(application_context.services.application, method).assert_called_once_with(
        "Safari"
    )


@pytest.mark.parametrize(
    "action_cls, method, params",
    [
        (OpenDocument, "open_document", {}),
        (OpenMultipleDocuments, "open_documents", {}),
        (OpenURLWithApplication, "open_url_with_application", {}),
        (RevealApplicationInFileManager, "reveal_application", {}),
        (RevealApplicationExecutable, "reveal_application_executable", {}),
    ],
)
def test_document_actions_require_parameters(
    application_context, action_cls, method, params
):
    result = action_cls().execute(application_context, params)

    assert_error(result, "MISSING_PARAM")
    getattr(application_context.services.application, method).assert_not_called()


@pytest.mark.parametrize(
    "method, action_cls, params",
    [
        ("open_document", OpenDocument, {"path": "/tmp/a.pdf"}),
        ("open_documents", OpenMultipleDocuments, {"paths": ["/tmp/a.pdf"]}),
        (
            "open_url_with_application",
            OpenURLWithApplication,
            {"url": "https://example.com", "application": "Safari"},
        ),
        ("reveal_application", RevealApplicationInFileManager, {"application": "Safari"}),
        (
            "reveal_application_executable",
            RevealApplicationExecutable,
            {"application": "Safari"},
        ),
    ],
)
def test_document_service_errors_are_wrapped(
    application_context, method, action_cls, params
):
    getattr(application_context.services.application, method).side_effect = RuntimeError("document failed")

    result = action_cls().execute(application_context, params)

    assert_error(result, "SYSTEM_ERROR")
    assert result.error == "document failed"
