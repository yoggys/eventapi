import json
from typing import Any, Optional, Self, Union


class DotDict(dict):
    __getattr__ = dict.get


class WebsocketMessageType(DotDict):
    DISPATCH = 0
    HELLO = 1
    HEARTBEAT = 2
    RECONNECT = 4
    ACK = 5
    ERROR = 6
    END_OF_STREAM = 7
    IDENTIFY = 33
    RESUME = 34
    SUBSCRIBE = 35
    UNSUBSCRIBE = 36
    SIGNAL = 37


class ServerCloseCodes(DotDict):
    SERVER_ERROR = 4000
    UNKNOWN_OPERATION = 4001
    INVALID_PAYLOAD = 4002
    AUTH_FAILURE = 4003
    ALREADY_IDENTIFIED = 4004
    RATE_LIMITED = 4005
    RESTART = 4006
    MAINTENANCE = 4007
    TIMEOUT = 4008
    ALREADY_SUBSCRIBED = 4009
    NOT_SUBSCRIBED = 4010
    INSUFFICIENT_PRIVILEGE = 4011

    RECONNECT_CODES = [4000, 4006, 4007, 4008]


class EventType(DotDict):
    SYSTEM_ANNOUNCEMENT = "system.announcement"
    SYSTEM_ALL = "system.*"
    EMOTE_CREATE = "emote.create"
    EMOTE_UPDATE = "emote.update"
    EMOTE_DELETE = "emote.delete"
    EMOTE_ALL = "emote.*"
    EMOTE_SET_CREATE = "emote_set.create"
    EMOTE_SET_UPDATE = "emote_set.update"
    EMOTE_SET_DELETE = "emote_set.delete"
    EMOTE_SET_ALL = "emote_set.*"
    USER_CREATE = "user.create"
    USER_UPDATE = "user.update"
    USER_DELETE = "user.delete"
    USER_ADD_CONNECTION = "user.add_connection"
    USER_UPDATE_CONNECTION = "user.update_connection"
    USER_DELETE_CONNECTION = "user.delete_connection"
    USER_ALL = "user.*"
    COSMETIC_CREATE = "cosmetic.create"
    COSMETIC_UPDATE = "cosmetic.update"
    COSMETIC_DELETE = "cosmetic.delete"
    COSMETIC_ALL = "cosmetic.*"
    ENTITLEMENT_CREATE = "entitlement.create"
    ENTITLEMENT_UPDATE = "entitlement.update"
    ENTITLEMENT_DELETE = "entitlement.delete"
    ENTITLEMENT_ALL = "entitlement.*"


class UserConnection:
    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id")
        self.username: str = data.get("username")
        self.display_name: str = data.get("display_name")
        self.platform: str = data.get("platform")
        self.linked_at: int = data.get("linked_at")
        self.emote_capacity: int = data.get("emote_capacity")
        self.emote_set_id: str = data.get("emote_set_id")


class User:
    def __init__(self, data: dict[str, Any]):
        self.id: str = data.get("id")
        self.username: str = data.get("username")
        self.display_name: str = data.get("display_name")
        self.avatar_url: str = data.get("avatar_url")
        self.style: Optional[dict[str, Any]] = data.get("style")
        self.roles: Optional[list[str]] = data.get("roles")
        self.connections: Optional[list[UserConnection]] = data.get("connections")


class ChangeField:
    def __init__(self, data: dict[str, Any]) -> None:
        self.key: str = data.get("key")
        self.index: int = data.get("index")
        self.nested: bool = data.get("nested")
        self.old_value: Optional[dict[str, Any]] = data.get("nested")

        value: Optional[Union[list[Self], dict[str, Any]]] = data.get("value")
        self.value: Optional[Union[list[Self], dict[str, Any]]] = (
            value
            if not value or isinstance(value, dict)
            else [ChangeField(c) for c in value]
        )


class ChangeMap:
    def __init__(self, data: dict[str, Any]) -> None:
        self.id: str = data.get("id")
        self.kind: int = data.get("kind")
        self.contextual: Optional[bool] = data.get("contextual")
        self.actor: User = User(data.get("actor"))
        self.added: Optional[list[ChangeField]] = [
            ChangeField(d) for d in data.get("added", [])
        ]
        self.updated: Optional[list[ChangeField]] = [
            ChangeField(d) for d in data.get("updated", [])
        ]
        self.removed: Optional[list[ChangeField]] = [
            ChangeField(d) for d in data.get("removed", [])
        ]
        self.pushed: Optional[list[ChangeField]] = [
            ChangeField(d) for d in data.get("pushed", [])
        ]
        self.pulled: Optional[list[ChangeField]] = [
            ChangeField(d) for d in data.get("pulled", [])
        ]


class SubscriptionCondition:
    def __init__(
        self,
        object_id: Optional[str] = None,
        connection_id: Optional[str] = None,
        host_id: Optional[str] = None,
    ) -> None:
        self.data = {}
        if object_id:
            self.data["object_id"] = object_id
        if connection_id:
            self.data["connection_id"] = connection_id
        if host_id:
            self.data["host_id"] = host_id


class SubscriptionData:
    def __init__(
        self,
        subscription_type: Union[EventType, str],
        condition: Optional[SubscriptionCondition] = None,
    ) -> None:
        self.data = {
            "type": subscription_type,
            "condition": condition.data if condition else None,
        }


class WebsocketMessage:
    def __init__(self, data: dict[str, Any]) -> None:
        self.raw_data = data


class Dispatch(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        self.type: EventType = data.get("type")
        self.body: ChangeMap = ChangeMap(data.get("body"))
        super().__init__(data)


class Hello(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        self.session_id: str = data.get("session_id")
        self.heartbeat_interval: int = data.get("heartbeat_interval")
        self.subscription_limit: int = data.get("subscription_limit")
        super().__init__(data)


class Heartbeat(WebsocketMessage):
    def __init__(self, data: dict[str, int]) -> None:
        self.count: int = data.get("count")
        super().__init__(data)


class Ack(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        self.command: str = data.get("command")
        self.data: Any = data.get("data")
        super().__init__(data)


class Reconnect(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        super().__init__(data)


class Error(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        self.message: str = data.get("message")
        self.fields: dict[str, str] = data.get("fields")
        super().__init__(data)


class EndOfStream(WebsocketMessage):
    def __init__(self, data: dict[str, Any]) -> None:
        self.code: ServerCloseCodes = data.get("code")
        self.should_reconnect: bool = self.code in ServerCloseCodes.RECONNECT_CODES
        self.message: Optional[str] = data.get("message")
        super().__init__(data)


ResponseTypes = Union[Dispatch, Hello, Heartbeat, Ack, Reconnect, Error, EndOfStream]
