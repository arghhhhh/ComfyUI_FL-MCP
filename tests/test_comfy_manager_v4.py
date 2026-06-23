import asyncio
import json
import sys
from types import SimpleNamespace

import httpx
import pytest

from backend.comfy_manager import ComfyManagerClient, ManagerAPIError, ManagerVersion


class FakeAsyncClient:
    def __init__(self, routes, requests, *args, **kwargs):
        self.routes = routes
        self.requests = requests

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, params=None, json=None):
        key = (method, url)
        self.requests.append({"method": method, "url": url, "params": params, "json": json})
        response = self.routes.get(key)
        if response is None:
            return httpx.Response(404, text="not found")
        if callable(response):
            response = response(params=params, json=json)
        if isinstance(response, httpx.Response):
            return response
        return httpx.Response(200, json=response)


@pytest.fixture
def fake_http(monkeypatch):
    routes = {}
    requests = []

    def factory(*args, **kwargs):
        return FakeAsyncClient(routes, requests, *args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", factory)
    return routes, requests


def test_check_installed_uses_features_manager_v4(fake_http):
    routes, _ = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True, "supports_csrf_post": True}}
    }

    async def run():
        client = ComfyManagerClient("http://comfy")
        return await client.check_installed()

    status = asyncio.run(run())

    assert status == ManagerVersion(version="v4", installed=True, supports_v4=True)


def test_installed_packs_and_node_mappings_use_v2_routes(fake_http):
    routes, requests = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True}}
    }
    routes[("GET", "http://comfy/v2/customnode/installed")] = {
        "ComfyUI_FL-Ren-Agent": {
            "ver": "abc123",
            "cnr_id": "",
            "aux_id": "filliptm/ComfyUI_FL-Ren-Agent",
            "enabled": True,
        }
    }
    routes[("GET", "http://comfy/v2/customnode/getmappings")] = {
        "comfy-core": [["KSampler", "SaveImage"], {"title_aux": "Comfy Core"}]
    }

    async def run():
        client = ComfyManagerClient("http://comfy")
        return await client.list_installed_packs(), await client.get_node_mappings(mode="local")

    installed, mappings = asyncio.run(run())

    assert "ComfyUI_FL-Ren-Agent" in installed
    assert mappings["KSampler"].node_pack_id == "comfy-core"
    assert mappings["KSampler"].node_pack_name == "Comfy Core"
    assert requests[-1]["params"] == {"mode": "local"}


def test_queue_action_posts_manager_v4_task_and_starts_queue(fake_http):
    routes, requests = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True}}
    }
    routes[("POST", "http://comfy/v2/manager/queue/task")] = {"ok": True}
    routes[("POST", "http://comfy/v2/manager/queue/start")] = {"started": True}

    async def run():
        client = ComfyManagerClient("http://comfy")
        return await client.queue_action(
            "disable",
            {"node_name": "example-pack", "is_unknown": False},
            client_id="test-client",
            ui_id="test-ui",
        )

    result = asyncio.run(run())

    task_request = requests[-2]
    assert task_request["url"] == "http://comfy/v2/manager/queue/task"
    assert task_request["json"] == {
        "ui_id": "test-ui",
        "client_id": "test-client",
        "kind": "disable",
        "params": {"node_name": "example-pack", "is_unknown": False},
    }
    assert result["queued"] is True
    assert result["requires_restart"] is True


def test_queue_action_update_all_uses_query_params(fake_http):
    routes, requests = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True}}
    }
    routes[("POST", "http://comfy/v2/manager/queue/update_all")] = {"ok": True}

    async def run():
        client = ComfyManagerClient("http://comfy")
        return await client.queue_action(
            "update-all",
            {"mode": "cache"},
            client_id="test-client",
            ui_id="update-all",
            start_queue=False,
        )

    result = asyncio.run(run())

    update_request = requests[-1]
    assert update_request["params"] == {
        "client_id": "test-client",
        "ui_id": "update-all",
        "mode": "cache",
    }
    assert result["queue_start"] is None


def test_v2_api_errors_are_reported(fake_http):
    routes, _ = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True}}
    }
    routes[("GET", "http://comfy/v2/manager/queue/status")] = httpx.Response(
        500,
        text="boom",
    )

    async def run():
        client = ComfyManagerClient("http://comfy")
        await client.queue_status()

    with pytest.raises(ManagerAPIError) as exc:
        asyncio.run(run())

    assert "500" in str(exc.value)
    assert "boom" in str(exc.value)


def test_external_models_fall_back_to_packaged_model_db(fake_http, monkeypatch, tmp_path):
    routes, _ = fake_http
    routes[("GET", "http://comfy/features")] = {
        "extension": {"manager": {"supports_v4": True}}
    }
    package_dir = tmp_path / "comfyui_manager"
    package_dir.mkdir()
    (package_dir / "__init__.py").write_text("", encoding="utf-8")
    (package_dir / "model-list.json").write_text(
        json.dumps(
            {
                "models": [
                    {
                        "name": "TAEF1 Decoder",
                        "filename": "taef1_decoder.pth",
                        "type": "TAESD",
                        "base": "FLUX.1",
                        "description": "FLUX preview decoder",
                        "reference": "https://example.test/taesd",
                        "save_path": "vae_approx",
                        "size": "4.71MB",
                        "url": "https://example.test/taef1_decoder.pth",
                    },
                    {
                        "name": "Other Model",
                        "filename": "other.safetensors",
                        "type": "checkpoint",
                        "base": "SDXL",
                        "description": "",
                        "reference": "",
                        "save_path": "checkpoints",
                        "size": "1GB",
                        "url": "https://example.test/other.safetensors",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setitem(
        sys.modules,
        "comfyui_manager",
        SimpleNamespace(__file__=str(package_dir / "__init__.py")),
    )

    async def run():
        client = ComfyManagerClient("http://comfy")
        return await client.search_external_models(query="flux", max_results=5)

    results = asyncio.run(run())

    assert len(results) == 1
    assert results[0].name == "TAEF1 Decoder"
    assert results[0].installed is False
