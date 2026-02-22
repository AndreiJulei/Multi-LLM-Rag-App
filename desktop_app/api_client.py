import requests
from typing import Optional, Dict


class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        if token:
            return {"Authorization": f"Bearer {token}"}
        return {}

    # Authentification:
    def register(self, email: str, password: str) -> requests.Response:
        url = f"{self.base_url}/users/register"
        payload = {"email": email, "password": password}
        return requests.post(url, json=payload)

    def login(self, email: str, password: str) -> requests.Response:
        url = f"{self.base_url}/users/login"
        payload = {"email": email, "password": password}
        return requests.post(url, json=payload)

    def get_me(self, token: str) -> requests.Response:
        url = f"{self.base_url}/users/me"
        return requests.get(url, headers=self._get_headers(token))

    # Collections:
    def get_collections(self, token: str) -> requests.Response:
        url = f"{self.base_url}/collections/"
        return requests.get(url, headers=self._get_headers(token))

    def create_collection(self, name: str, token: str) -> requests.Response:
        url = f"{self.base_url}/collections/"
        payload = {"name": name}
        return requests.post(url, json=payload, headers=self._get_headers(token))

    def delete_collection(self, collection_id: int, token: str) -> requests.Response:
        url = f"{self.base_url}/collections/{collection_id}"
        return requests.delete(url, headers=self._get_headers(token))

    # Documents:
    def upload_document(
        self,
        file_name: str,
        file_content: bytes,
        collection_id: int,
        token: str,
    ) -> requests.Response:
        url = f"{self.base_url}/documents/upload"
        files = {"file": (file_name, file_content)}
        params = {"collection_id": collection_id}
        return requests.post(
            url, files=files, params=params, headers=self._get_headers(token)
        )

    # Chats:
    def query_counsel(
        self, collection_id: int, query: str, mode: str, token: str
    ) -> requests.Response:
        url = f"{self.base_url}/chat/query"
        payload = {
            "collection_id": collection_id,
            "query": query,
            "mode": mode,
        }
        return requests.post(url, json=payload, headers=self._get_headers(token))

    def cast_vote(
        self, chat_id: int, winner: str, token: str
    ) -> requests.Response:
        url = f"{self.base_url}/chat/vote"
        payload = {"chat_id": chat_id, "winner": winner}
        return requests.post(url, json=payload, headers=self._get_headers(token))

    def blind_vote(self, chat_id: int, token: str) -> requests.Response:
        url = f"{self.base_url}/chat/blind-vote"
        payload = {"chat_id": chat_id}
        return requests.post(url, json=payload, headers=self._get_headers(token))

    def get_chat_history(
        self, collection_id: int, token: str
    ) -> requests.Response:
        url = f"{self.base_url}/chat/history/{collection_id}"
        return requests.get(url, headers=self._get_headers(token))

    # Settings/models aviable
    def get_active_models(self, token: str) -> requests.Response:
        url = f"{self.base_url}/settings/active-models"
        return requests.get(url, headers=self._get_headers(token))

    def get_admin_settings(self, token: str) -> requests.Response:
        url = f"{self.base_url}/admin/settings"
        return requests.get(url, headers=self._get_headers(token))

    def update_admin_settings(
        self,
        token: str,
        api_keys: Optional[Dict[str, str]] = None,
        active_models: Optional[list] = None,
    ) -> requests.Response:
        url = f"{self.base_url}/admin/settings/update"
        payload: Dict = {}
        if api_keys is not None:
            payload["api_keys"] = api_keys
        if active_models is not None:
            payload["active_models"] = active_models
        return requests.post(url, json=payload, headers=self._get_headers(token))

    def get_available_models(self, token: str) -> requests.Response:
        url = f"{self.base_url}/admin/models"
        return requests.get(url, headers=self._get_headers(token))
