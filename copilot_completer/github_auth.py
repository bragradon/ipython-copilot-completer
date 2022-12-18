from __future__ import annotations

import webbrowser
from contextlib import suppress
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Optional

import requests
from requests import HTTPError, Response


OAUTH_CLIENT_ID = "01ab8ac9400c4e429b23"  # GitHub's VSCode auth client ID
OAUTH_SCOPE = "read:user"
OAUTH_GRANT_TYPE = "urn:ietf:params:oauth:grant-type:device_code"
REQUEST_HEADERS = {
    "content-type": "application/json",
    "accept": "application/json",
}


@dataclass
class LoginSession:
    device_code: str
    user_code: str
    verification_uri: str
    expires_in: int
    interval: int


@dataclass
class AccessToken:
    access_token: str
    token_type: str
    scope: str


def get_github_access_token() -> Optional[AccessToken]:
    print("Initializing a login session with GitHub")
    login_session = get_login_session()
    print(
        f"Please visit {login_session.verification_uri} and enter the following code:",
    )
    print(f"\t{login_session.user_code}")

    with suppress(Exception):
        webbrowser.open(login_session.verification_uri)

    if access_token := wait_for_access_token(login_session):
        return access_token
    else:
        print("Failed to log in")


def get_login_session() -> LoginSession:
    response = requests.post(
        "https://github.com/login/device/code",
        json={
            "client_id": OAUTH_CLIENT_ID,
            "scope": OAUTH_SCOPE,
        },
        headers=REQUEST_HEADERS,
    )
    try:
        response.raise_for_status()
        return LoginSession(**response.json())
    except HTTPError:
        log_failure_response(response)
        raise


def wait_for_access_token(session: LoginSession) -> Optional[AccessToken]:
    expiry = datetime.now(tz=timezone.utc) + timedelta(seconds=session.expires_in)
    has_expired = False
    access_token: Optional[AccessToken] = None

    print(f"Polling for login session status until {expiry.isoformat()}")
    while access_token is None and not has_expired:
        sleep(session.interval)
        response = requests.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": OAUTH_CLIENT_ID,
                "device_code": session.device_code,
                "grant_type": OAUTH_GRANT_TYPE,
            },
            headers=REQUEST_HEADERS,
        )
        try:
            response.raise_for_status()
            response_data = response.json()
            if "error" in response_data:
                print(
                    f"Polling for login session status: {response_data['error']}",
                )
            else:
                access_token = AccessToken(**response.json())
        except HTTPError:
            log_failure_response(response)
            raise
        else:
            has_expired = datetime.now(tz=timezone.utc) >= expiry

    return access_token


def log_failure_response(response: Response) -> None:
    print("Unhandled error occurred")
    print(f"Response status code: {response.status_code}")
    print(f"Response content:\n\n{response.content}\n")
