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

> Here's a simple example of how to use wrapper:

```python
import asyncio

from eventapi.EventApi import EventApi
from eventapi.WebSocket import (
    EventType,
    ResponseTypes,
    SubscriptionCondition,
    SubscriptionData,
)


async def callback(data: ResponseTypes):
    print("Message from callback: ", data)


async def main():
    # create instance of EventApi with message callback
    app = EventApi(callback=callback)

    # connect to websocket
    await app.connect()
    print("Connected")

    # create subscription with specified condition
    condition = SubscriptionCondition(object_id="6433b7cec07d26f890dd2d01")
    subscription = SubscriptionData(
        subscription_type=EventType.EMOTE_SET_ALL, condition=condition
    )
    await app.subscribe(subscription_data=subscription)

    # you can also use async iterator without specifying callback
    async for message in app:
        print("Message from async iterator: ", message)

    # run forever if we are not using async for
    await asyncio.Future()


asyncio.run(main())
```

<hr>

> Discord.py / Pycord example:

<img src="https://github.com/yoggys/eventapi/blob/master/assets/example_dc.png" alt="Discord Bot example" height="450px">

```python
from typing import Any, Dict, List

import aiohttp
import discord

from eventapi.EventApi import EventApi
from eventapi.WebSocket import (
    Dispatch,
    EventType,
    ResponseTypes,
    SubscriptionCondition,
    SubscriptionData,
)


async def format_url(data: Dict[str, Any]) -> str:
    base_url = "https://cdn.7tv.app/emote/{}/4x".format(data.get("id"))
    if "animated" not in data:
        async with aiohttp.ClientSession() as cs:
            async with cs.get(base_url + ".gif") as r:
                if r.status == 200:
                    base_url += ".gif"
    else:
        if data.get("animated"):
            base_url += ".gif"
    return base_url


async def callback(data: ResponseTypes) -> None:
    if not isinstance(data, Dispatch):
        return
    if data.type != EventType.EMOTE_SET_UPDATE:
        return

    channel = client.get_channel(927288026000945162)  # your channel id
    changes: List[discord.Embed] = []

    def add_change(description: str, color: discord.Color, image_url: str):
        changes.append(
            discord.Embed(description=description, color=color).set_image(url=image_url)
        )

    if data.body.pulled:
        for pulled in data.body.pulled:
            add_change(
                "**Deleted emote:** `{}`".format(pulled.old_value.get("name")),
                discord.Color.brand_red(),
                await format_url(pulled.old_value),
            )
    if data.body.pushed:
        for pushed in data.body.pushed:
            add_change(
                "**Added emote:** `{}`".format(pushed.value.get("name")),
                discord.Color.brand_green(),
                await format_url(pushed.value.get("data")),
            )
    if data.body.updated:
        for updated in data.body.updated:
            add_change(
                "**Edited emote:** `{}` » `{}`".format(
                    updated.old_value.get("name"), updated.value.get("name")
                ),
                discord.Color.yellow(),
                await format_url(updated.value),
            )

    if len(changes) > 0:
        await channel.send(embeds=changes)


intents = discord.Intents.default()
client = discord.Client(intents=intents)
client.eventapi = EventApi(callback=callback)


@client.listen("on_ready", once=True)
async def on_ready():
    await client.eventapi.connect()
    condition = SubscriptionCondition(
        object_id="6433b7cec07d26f890dd2d01"
    )  # your emote-set id
    subscription = SubscriptionData(
        subscription_type=EventType.EMOTE_SET_ALL, condition=condition
    )
    await client.eventapi.subscribe(subscription_data=subscription)


client.run("your token here")  # your token
```



## Contributing

Contributions are welcome! If you encounter any issues or have suggestions for improvements, please open an issue or
submit a pull request on the [GitHub repository](https://github.com/yoggys/eventapi).

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
