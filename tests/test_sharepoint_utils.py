import pytest
from unittest.mock import Mock
import requests
from sharepoint_connector.sharepoint_utils import create_folder, upload_file_local

def test_create_folder_retry(mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = requests.exceptions.ConnectionError()

    with pytest.raises(requests.exceptions.ConnectionError):
        create_folder(
            "https://contoso.sharepoint.com",
            "/sites/test",
            {"Authorization": "Bearer token"},
            "digest"
        )
    
    assert mock_post.call_count == 4  # 3 retries + 1 initial attempt

def test_upload_retry_success(mocker):
    mock_post = mocker.patch('requests.post')
    mock_post.side_effect = [
        requests.exceptions.Timeout(),
        Mock(status_code=200, text="Success")
    ]

    response = upload_file_local(
        "https://contoso.sharepoint.com",
        "/sites/test",
        "test.txt",
        {"Authorization": "Bearer token"},
        "digest"
    )

    assert mock_post.call_count == 2
    assert response.status_code == 200