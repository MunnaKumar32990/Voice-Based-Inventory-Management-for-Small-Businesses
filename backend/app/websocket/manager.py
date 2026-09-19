from fastapi import WebSocket
from typing import Dict, Set
import json

class ConnectionManager:
    """Shop-scoped WebSocket registry. Safe for multi-client use.

    Connections are grouped by shop_id so one shop's stock updates never
    leak to another shop. Broadcast never fails the whole fan-out because
    of a single dead socket.
    """

    def __init__(self):
        self._by_shop: Dict[str, Set[WebSocket]] = {}

    async def connect(self, shop_id: str, websocket: WebSocket):
        await websocket.accept()
        self._by_shop.setdefault(shop_id, set()).add(websocket)

    def disconnect(self, shop_id: str, websocket: WebSocket):
        conns = self._by_shop.get(shop_id)
        if not conns:
            return
        conns.discard(websocket)
        if not conns:
            self._by_shop.pop(shop_id, None)

    async def send_to_shop(self, shop_id: str, payload: dict):
        conns = list(self._by_shop.get(shop_id, set()))
        dead = []
        text = json.dumps(payload, default=str)
        for ws in conns:
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(shop_id, ws)

    async def broadcast(self, message: str):
        """Legacy broadcast (all shops). Prefer send_to_shop for tenant safety."""
        for shop_id in list(self._by_shop.keys()):
            await self.send_to_shop(shop_id, {"message": message})

manager = ConnectionManager()
