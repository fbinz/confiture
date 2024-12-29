import json
from typing import Any

import httpx
from django import forms

from core.models import ConfigItem

from .spec import AdapterError, AdapterWarning, hookimpl


class CapRoverForm(forms.Form):
    url = forms.URLField()


class CapRoverAdapter:
    Form = None

    def __init__(self):
        self.caprover_url = None
        self.caprover_password = None
        self.caprover_app = None

    @hookimpl
    async def pull(self) -> list[ConfigItem]:
        """
        Pull ConfigItem objects from the target.
        """
        return []

    @hookimpl
    async def push(self, items: list[ConfigItem]) -> list[AdapterWarning]:
        """
        Push ConfigItem objects to the target.
        """

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.caprover_url}/api/v2/login",
                json={"password": self.caprover_password},
                headers={
                    "X-Namespace": "captain",
                },
            )
            if response.status_code != 200:
                raise AdapterError("Failed to log in")

            data = response.json()
            token = data["data"]["token"]

            # get app definitions
            response = await client.get(
                f"{self.caprover_url}/api/v2/user/apps/appDefinitions",
                headers={
                    "X-Namespace": "captain",
                    "X-Captain-Auth": token,
                },
            )
            data = response.json()
            app_definitions = data["data"]["appDefinitions"]

            app_definition = None
            for app_definition in app_definitions:
                if app_definition.get("appName") == self.caprover_app:
                    break
            else:
                raise AdapterError(f"No app named {self.caprover_app!r} found")

            if app_definition is None:
                raise AdapterError(
                    f"Failed to get app definition for app named {self.caprover_app!r}"
                )

            env_vars = {
                env_var["key"]: env_var["value"]
                for env_var in app_definition["envVars"]
            }
            env_vars["bla"] = "blub"
            app_definition["envVars"] = [
                {"key": key, "value": value} for key, value in env_vars.items()
            ]

            # Update app definition via POST request to caprover API
            response = await client.post(
                f"{self.caprover_url}/api/v2/user/apps/appDefinitions/update",
                content=json.dumps(app_definition),
                headers={
                    "Content-Type": "application/json",
                    "X-Namespace": "captain",
                    "X-Captain-Auth": token,
                },
            )

            if response.status_code != 200:
                raise AdapterError(
                    f"Failed to update app {self.caprover_app!r}",
                    response.status_code,
                    response.text,
                )

    @hookimpl
    async def configure(self, config: dict[str, Any]):
        """
        Configure this adapter.
        """
        self.caprover_url = config["url"]
        self.caprover_password = config["password"]
        self.caprover_app = config["app"]


if __name__ == "__main__":
    import asyncio

    from core.models import AdapterConfig

    ac = AdapterConfig.objects.first()

    async def main():
        adapter = await CapRoverAdapter().configure(config=ac.config)
        await adapter.push()

    asyncio.run(main())
