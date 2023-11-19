import asyncio
import json
import socket
from typing import Any, Callable, Coroutine, Optional

import websockets

from eventapi.Exceptions import (
    ConnectionException,
    NoActiveConnectionException,
    NoActiveSubscriptionsException,
    SubscriptionException,
)
from eventapi.WebSocket import (
    Ack,
    Dispatch,
    EndOfStream,
    Error,
    Heartbeat,
    Hello,
    Reconnect,
    ResponseTypes,
    SubscriptionData,
    WebsocketMessageType,
)


class EventApi:
    def __init__(
        self,
        callback: Callable[[ResponseTypes], Coroutine] = None,
        websocket_url: Optional[str] = None,
    ) -> None:
        self.WS_URL: str = websocket_url or "wss://events.7tv.io/v3"
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.handler: Optional[asyncio.Task] = None

        self.previous_session_id: Optional[str] = None
        self.session_id: Optional[str] = None
        self.subscription_limit: int = 100
        self.subscriptions: list[SubscriptionData] = []
        self.callback = callback

    async def connect(self) -> None:
        try:
            self.ws = await websockets.connect(self.WS_URL)
            self.handler = asyncio.create_task(self.message_handler())
        except (websockets.exceptions.WebSocketException, socket.gaierror):
            raise ConnectionException()

    async def reconnect(self) -> None:
        self.handler.cancel()
        self.handler = None
        if not self.ws.closed:
            await self.ws.close()
        self.ws = None
        await self.connect()

    async def message_handler(self) -> None:
        try:
            while True:
                message = await self.ws.recv()
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                asyncio.create_task(self.on_message(message))
        except websockets.exceptions.ConnectionClosed:
            asyncio.create_task(self.reconnect())

    async def on_message(self, message: str) -> None:
        message = json.loads(message)
        parsed_message = await self.parse_message(message)
        if self.callback and parsed_message:
            asyncio.create_task(self.callback(parsed_message))

    async def parse_message(self, message: dict[str, Any]) -> Optional[ResponseTypes]:
        message_data = message.get("d")
        message_code = message.get("op")

        if message_code == WebsocketMessageType.DISPATCH:
            return Dispatch(message_data)
        elif message_code == WebsocketMessageType.HELLO:
            parsed_message = Hello(message_data)
            if self.session_id:
                asyncio.create_task(
                    self.ws.send(
                        json.dumps({"op": 34, "d": {"session_id": self.session_id}})
                    )
                )
            self.session_id = parsed_message.session_id
            self.subscription_limit = parsed_message.subscription_limit
            return parsed_message
        elif message_code == WebsocketMessageType.HEARTBEAT:
            return Heartbeat(message_data)
        elif message_code == WebsocketMessageType.RECONNECT:
            asyncio.create_task(self.reconnect())
            return Reconnect(message_data)
        elif message_code == WebsocketMessageType.ACK:
            parsed_message = Ack(message_data)
            if parsed_message.command == "RESUME" and not parsed_message.data.get(
                "success"
            ):
                for s in self.subscriptions:
                    asyncio.create_task(self.subscribe(s))
            return parsed_message
        elif message_code == WebsocketMessageType.ERROR:
            return Error(message_data)
        elif message_code == WebsocketMessageType.END_OF_STREAM:
            parsed_message = EndOfStream(message_data)
            if parsed_message.should_reconnect:
                asyncio.create_task(self.reconnect())
            return parsed_message

    async def subscribe(self, subscription_data: SubscriptionData) -> None:
        if not self.ws or self.ws.closed:
            raise NoActiveConnectionException()
        if len(self.subscriptions) + 1 > self.subscription_limit:
            raise SubscriptionException(limit=self.subscription_limit)
        if subscription_data not in self.subscriptions:
            self.subscriptions.append(subscription_data)
        await self.ws.send(json.dumps({"op": 35, "d": subscription_data.data}))

    async def unsubscribe(self, subscription_data: SubscriptionData) -> None:
        if not self.ws or self.ws.closed:
            raise NoActiveConnectionException()
        if len(self.subscriptions) == 0:
            raise NoActiveSubscriptionsException()
        if subscription_data in self.subscriptions:
            self.subscriptions.remove(subscription_data)
        await self.ws.send(json.dumps({"op": 36, "d": subscription_data.data}))
