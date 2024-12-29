from typing import Any

import pluggy
from attrs import define

from core.models import ConfigItem

hookspec = pluggy.HookspecMarker("confiture")
hookimpl = pluggy.HookimplMarker("confiture")


class AdapterError(Exception):
    pass


@define
class AdapterWarning:
    code: str
    message: str


class AdapterSpec:
    """
    An adapter for a particular system (i.e. CapRover) knows how to read and
    write configuration items.
    Every system might need different settings, so the (opaque) settings are also part
    of the Adapter interface.
    """

    Form = None

    @hookspec
    async def pull(self) -> list[ConfigItem]:
        """
        Pull ConfigItem objects from the target.
        """
        return []

    @hookspec
    async def push(self, items: list[ConfigItem]):
        """
        Push ConfigItem objects to the target.
        """

    @hookspec
    async def configure(self, config: dict[str, Any]):
        """
        Configure this adapter.
        """
