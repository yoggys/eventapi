import asyncio
import atexit
import json
import logging
import signal
import socket
from typing import Any, Callable, Coroutine, Dict, List, Optional

import websockets
from typing_extensions import Self

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

        self.queue: Optional[asyncio.Queue] = None
        self.session_id: Optional[str] = None
        self.subscription_limit: int = 500
        self.subscriptions: List[SubscriptionData] = []
        self.callback = callback

        atexit.register(self._close_sync)
        signal.signal(signal.SIGINT, self._handle_exit)
        signal.signal(signal.SIGTERM, self._handle_exit)

    async def __aenter__(self) -> Self:
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    def __aiter__(self):
        if not self.closed:
            self.queue = asyncio.Queue()
            return self
        else:
            raise StopAsyncIteration

    async def __anext__(self):
        if self.queue is None:
            raise StopAsyncIteration
        return await self.queue.get()

    def __str__(self) -> str:
        return f"<EventApi session_id='{self.session_id}' subscription_limit={self.subscription_limit} closed={self.closed}>"

    @property
    def closed(self) -> bool:
        return self.ws is None or self.ws.closed

    def _close_sync(self) -> None:
        if not self.closed:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self.close())
            else:
                asyncio.run(self.close())

    def _handle_exit(self, signum, frame) -> None:
        if not self.closed:
            asyncio.run(self.close())

    async def connect(self) -> None:
        try:
            self.ws = await websockets.connect(self.WS_URL)
            self.handler = asyncio.create_task(self.message_handler())
        except (websockets.exceptions.WebSocketException, socket.gaierror):
            raise ConnectionException()

    async def reconnect(self) -> None:
        await self.close()
        await self.connect()

    async def close(self) -> None:
        if self.handler:
            try:
                self.handler.cancel()
                await self.handler
            except asyncio.CancelledError:
                pass
            self.handler = None
        if self.ws and not self.closed:
            await self.ws.close()
        self.ws = None

    async def message_handler(self) -> None:
        try:
            while True:
                message = await self.ws.recv()
                if isinstance(message, bytes):
                    message = message.decode("utf-8")
                logging.debug(f"Received message: {message}")
                asyncio.create_task(self.on_message(message))
        except Exception as e:
            logging.error(f"Error in message handler: {e}")
            await self.reconnect()

    async def on_message(self, message: str) -> None:
        message = json.loads(message)
        parsed_message = await self.parse_message(message)
        if self.queue:
            await self.queue.put(parsed_message)
        if self.callback and parsed_message:
            try:
                await self.callback(parsed_message)
            except Exception as e:
                logging.error(f"Error in callback: {e}")

    async def parse_message(self, message: Dict[str, Any]) -> Optional[ResponseTypes]:
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
        if self.closed:
            raise NoActiveConnectionException()
        if len(self.subscriptions) + 1 > self.subscription_limit:
            raise SubscriptionException(limit=self.subscription_limit)
        if subscription_data not in self.subscriptions:
            self.subscriptions.append(subscription_data)
            await self.ws.send(json.dumps({"op": 35, "d": subscription_data.data}))
        else:
            logging.warning("Attempted to subscribe to already existing subscription.")

    async def unsubscribe(self, subscription_data: SubscriptionData) -> None:
        if self.closed:
            raise NoActiveConnectionException()
        if len(self.subscriptions) == 0:
            raise NoActiveSubscriptionsException()
        if subscription_data in self.subscriptions:
            self.subscriptions.remove(subscription_data)
            await self.ws.send(json.dumps({"op": 36, "d": subscription_data.data}))
        else:
            logging.warning("Attempted to unsubscribe from non-existent subscription.")
