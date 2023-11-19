class EventApiException(Exception):
    """
    Base class for all exceptions defined by EventApi.

    """


class SubscriptionException(EventApiException):
    """
    Thrown when a subscription limit is exceeded.

     Attributes:
        limit (int): The maximum number of subscriptions.

    """

    def __init__(self, limit: int) -> None:
        self.limit = limit


class NoActiveSubscriptionsException(EventApiException):
    """
    Thrown when there are no active subscriptions.

    """


class ConnectionException(EventApiException):
    """
    Thrown when a websocket connection fails.

    """


class NoActiveConnectionException(EventApiException):
    """
    Thrown when a trying to send a data when there is no active WebSocket connection.

    """
