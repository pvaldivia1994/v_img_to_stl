import asyncio
import pytest


@pytest.fixture(autouse=True)
def isolate_live_progress_transport(monkeypatch):
    """API tests must not connect to the user's running ComfyUI websocket."""
    from app import main
    async def offline_watch(comfy_url, record, publish, connected=None):
        if connected:
            connected.set()
        await asyncio.Event().wait()
    monkeypatch.setattr(main, 'watch_progress', offline_watch)
