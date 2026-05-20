import argparse
import getpass
import json
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_BASE_URL = "http://127.0.0.1:8000"
API_PREFIX = "/api/v1"


class ApiClientError(Exception):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class FastApiClient:
    base_url: str = DEFAULT_BASE_URL
    access_token: str | None = None
    api_key: str | None = None

    def __post_init__(self) -> None:
        self.base_url = self.base_url.rstrip("/")

    def login(self, username: str, password: str) -> dict[str, Any]:
        response = self._request(
            "POST",
            f"{API_PREFIX}/auth/login",
            body={
                "username": username,
                "password": password,
            },
            authenticated=False,
        )
        self.access_token = response["access_token"]
        self.api_key = None
        return response

    def use_api_key(self, api_key: str) -> None:
        self.api_key = api_key.strip()
        self.access_token = None

    def me(self) -> dict[str, Any]:
        return self._request("GET", f"{API_PREFIX}/auth/me")

    def health(self) -> dict[str, Any]:
        return self._request("GET", "/health", authenticated=False)

    def api_health(self) -> dict[str, Any]:
        return self._request("GET", f"{API_PREFIX}/health", authenticated=False)

    def db_health(self) -> dict[str, Any]:
        return self._request("GET", f"{API_PREFIX}/health/db", authenticated=False)

    def create_service_account(
        self,
        name: str,
        expires_at: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if expires_at:
            payload["expires_at"] = expires_at

        return self._request("POST", f"{API_PREFIX}/service-accounts", body=payload)

    def _request(
        self,
        method: str,
        path: str,
        body: dict[str, Any] | None = None,
        authenticated: bool = True,
    ) -> dict[str, Any]:
        data = None
        headers = {
            "Accept": "application/json",
        }

        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"

        if authenticated:
            if self.access_token:
                headers["Authorization"] = f"Bearer {self.access_token}"
            elif self.api_key:
                headers["X-API-Key"] = self.api_key
            else:
                raise ApiClientError("Сначала выполните авторизацию.")

        request = Request(
            url=f"{self.base_url}{path}",
            data=data,
            headers=headers,
            method=method,
        )

        try:
            with urlopen(request, timeout=10) as response:
                response_body = response.read().decode("utf-8")
        except HTTPError as exc:
            response_body = exc.read().decode("utf-8", errors="replace")
            detail = _extract_error_detail(response_body)
            raise ApiClientError(detail, status_code=exc.code) from exc
        except URLError as exc:
            raise ApiClientError(f"Не удалось подключиться к API: {exc.reason}") from exc

        if not response_body:
            return {}

        return json.loads(response_body)


def main() -> None:
    configure_stdio()

    parser = argparse.ArgumentParser(description="Menu client for secret-manage-service API")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"FastAPI URL, default: {DEFAULT_BASE_URL}",
    )
    args = parser.parse_args()

    client = FastApiClient(base_url=args.base_url)

    while True:
        print_menu(client)
        choice = input("Выберите действие: ").strip()

        try:
            if choice == "1":
                login_menu(client)
            elif choice == "2":
                api_key_menu(client)
            elif choice == "3":
                print_json(client.me())
            elif choice == "4":
                health_menu(client)
            elif choice == "5":
                create_service_account_menu(client)
            elif choice == "6":
                change_base_url_menu(client)
            elif choice == "0":
                print("Выход.")
                return
            else:
                print("Неизвестный пункт меню.")
        except ApiClientError as exc:
            prefix = f"HTTP {exc.status_code}: " if exc.status_code else ""
            print(f"Ошибка: {prefix}{exc}")
        except json.JSONDecodeError:
            print("Ошибка: сервер вернул не JSON-ответ.")
        except KeyboardInterrupt:
            print("\nОперация отменена.")


def print_menu(client: FastApiClient) -> None:
    auth_state = "нет"
    if client.access_token:
        auth_state = "Bearer token"
    elif client.api_key:
        auth_state = "X-API-Key"

    print()
    print("=== Secret Manage Service API Client ===")
    print(f"API: {client.base_url}")
    print(f"Авторизация: {auth_state}")
    print("1. Авторизация по логину и паролю")
    print("2. Авторизация по API-ключу")
    print("3. О себе (/auth/me)")
    print("4. Состояние сервиса (/health)")
    print("5. Создать клиента / API-ключ (service account)")
    print("6. Изменить адрес API")
    print("0. Выход")
    print()


def login_menu(client: FastApiClient) -> None:
    username = input("Username: ").strip()
    password = getpass.getpass("Password: ")
    response = client.login(username=username, password=password)
    print("Авторизация успешна.")
    print(f"Тип токена: {response.get('token_type')}")
    print(f"Истекает через минут: {response.get('expires_in_minutes')}")


def api_key_menu(client: FastApiClient) -> None:
    api_key = getpass.getpass("API key: ")
    if not api_key.strip():
        raise ApiClientError("API-ключ не может быть пустым.")

    client.use_api_key(api_key)
    print("API-ключ сохранен в памяти клиента.")


def health_menu(client: FastApiClient) -> None:
    print("Основной health:")
    print_json(client.health())
    print("API health:")
    print_json(client.api_health())
    print("DB health:")
    print_json(client.db_health())


def create_service_account_menu(client: FastApiClient) -> None:
    print("Создание service account доступно пользователю с ролью admin.")
    name = input("Название клиента/service account: ").strip()
    if len(name) < 3:
        raise ApiClientError("Название должно быть не короче 3 символов.")

    expires_at = input(
        "Дата окончания в ISO-формате, например 2026-12-31T23:59:59, или Enter: "
    ).strip()

    if expires_at:
        expires_at = normalize_datetime(expires_at)
    else:
        expires_at = None

    response = client.create_service_account(name=name, expires_at=expires_at)
    print("Клиент/API-ключ создан. Сохраните ключ сейчас, потом он не будет показан.")
    print_json(response)


def change_base_url_menu(client: FastApiClient) -> None:
    base_url = input(f"Новый адрес API [{client.base_url}]: ").strip()
    if not base_url:
        return

    client.base_url = base_url.rstrip("/")
    print(f"Адрес API изменен: {client.base_url}")


def normalize_datetime(value: str) -> str:
    try:
        return datetime.fromisoformat(value).isoformat()
    except ValueError as exc:
        raise ApiClientError(
            "Дата должна быть в ISO-формате, например 2026-12-31T23:59:59."
        ) from exc


def print_json(value: dict[str, Any]) -> None:
    print(json.dumps(value, ensure_ascii=False, indent=2))


def _extract_error_detail(response_body: str) -> str:
    try:
        data = json.loads(response_body)
    except json.JSONDecodeError:
        return response_body or "HTTP request failed"

    detail = data.get("detail")
    if isinstance(detail, str):
        return detail

    return json.dumps(data, ensure_ascii=False)


def configure_stdio() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name)
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")


if __name__ == "__main__":
    main()
