import asyncio

from django.core.management.base import BaseCommand

from core.adapters.caprover import CapRoverAdapter
from core.models import AdapterConfig


async def cmd(config):
    adapter = CapRoverAdapter()
    await adapter.configure(config=config)
    await adapter.push(items=[])


class Command(BaseCommand):
    def handle(self, *args, **options):
        ac = AdapterConfig.objects.first()
        asyncio.run(cmd(config=ac.config))
