from attrs import define

from core.models import ConfigItem, ConfigItemValue


@define
class ConfigTableRow:
    item: ConfigItem
    values: list[ConfigItemValue]


@define
class ConfigTable:
    headers: list[str]
    rows: list[ConfigTableRow]
