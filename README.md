# 7TV EventAPI Wrapper

[![Discord Server](https://img.shields.io/discord/746360067632136222?label=discord&style=for-the-badge&logo=discord&color=5865F2&logoColor=white)](https://dc.yoggies.dev/)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/downloads/release/python-380/)
[![PyPI Version](https://img.shields.io/pypi/v/eventapi.svg?style=for-the-badge&color=yellowgreen&logo=pypi&logoColor=white)](https://pypi.org/project/eventapi/)
[![PyPI Downloads](https://img.shields.io/pypi/dm/eventapi?style=for-the-badge&color=blueviolet&logo=pypi&logoColor=white)](https://pypi.org/project/eventapi/)

This is a Python wrapper for the 7TV EventAPI, which provides async access to the websocket events on
their [Emote Platform](https://7tv.app).

## Requirements

- Python 3.8 or higher

## Installation

You can install the 7TV EventAPI Wrapper using pip. Open your terminal and run the following command:

```shell
pip install eventapi
```

## Usage

Here's an simple example of how to use wrapper:

```python
import asyncio

from eventapi.EventApi import EventApi
from eventapi.WebSocket import (
    Dispatch,
    EventType,
    ResponseTypes,
    SubscriptionCondition,
    SubscriptionData,
)


async def callback(data: ResponseTypes):
    if isinstance(data, Dispatch):
        print(f"Event data type: {data.type}")
        print(f"Event data body: {data.body}")
    else:
        print(f"Raw event data: {data.raw_data}")


async def main():
    # create instance of EventApi with message callback
    app = EventApi(callback=callback)

    # connect to websocket
    await app.connect()

    # create subscription with specified condition
    condition = SubscriptionCondition(object_id="6433b7cec07d26f890dd2d01")
    subscription = SubscriptionData(
        subscription_type=EventType.EMOTE_SET_ALL, condition=condition
    )
    await app.subscribe(subscription_data=subscription)

    # run forever
    await asyncio.Future()


asyncio.run(main())
```

## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or
submit a pull request on the [GitHub repository](https://github.com/yoggys/7tv_eventapi_wrapper).

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
