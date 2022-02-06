"""Sensor component."""

from __future__ import annotations

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    PRESSURE_HPA,
    PRESSURE_MMHG,
    SPEED_METERS_PER_SECOND,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType

from .const import (
    ATTR_API_CONDITION,
    ATTR_API_FEELS_LIKE_TEMPERATURE,
    ATTR_API_HUMIDITY,
    ATTR_API_PRESSURE,
    ATTR_API_PRESSURE_MMHG,
    ATTR_API_TEMPERATURE,
    ATTR_API_WEATHER_TIME,
    ATTR_API_WIND_BEARING,
    ATTR_API_WIND_SPEED,
    ATTR_API_YA_CONDITION,
    ATTRIBUTION,
    DEFAULT_NAME,
    DOMAIN,
    ENTRY_NAME,
    MANUFACTURER,
    UPDATER,
)
from .updater import WeatherUpdater

WEATHER_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key=ATTR_API_TEMPERATURE,
        name="Temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_FEELS_LIKE_TEMPERATURE,
        name="Feels like temperature",
        native_unit_of_measurement=TEMP_CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_SPEED,
        name="Wind speed",
        native_unit_of_measurement=SPEED_METERS_PER_SECOND,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_WIND_BEARING,
        name="Wind bearing",
        native_unit_of_measurement="",
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_HUMIDITY,
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_PRESSURE,
        name="Pressure",
        native_unit_of_measurement=PRESSURE_HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_API_CONDITION, name="Condition", entity_registry_enabled_default=False
    ),
    SensorEntityDescription(
        key=ATTR_API_WEATHER_TIME,
        name="Data update time",
        device_class=SensorDeviceClass.TIMESTAMP,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
        entity_category="diagnostic",
    ),
    SensorEntityDescription(
        key=ATTR_API_YA_CONDITION,
        name="Condition",
        entity_registry_enabled_default=True,
    ),
    SensorEntityDescription(
        key=ATTR_API_PRESSURE_MMHG,
        name="Pressure mmHg",
        native_unit_of_measurement=PRESSURE_MMHG,
        icon="mdi:gauge",
        # should not define device_class, because HA will try to convert pressure to system units.
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=True,
    ),
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up weather "Yandex.Weather" sensor entry."""
    domain_data = hass.data[DOMAIN][config_entry.entry_id]
    name = domain_data[ENTRY_NAME]
    updater = domain_data[UPDATER]

    entities: list[YandexWeatherSensor] = [
        YandexWeatherSensor(
            name,
            f"{config_entry.unique_id}-{description.key}",
            description,
            updater,
        )
        for description in WEATHER_SENSORS
    ]
    async_add_entities(entities)


class YandexWeatherSensor(SensorEntity):
    """Yandex.Weather sensor entry."""

    _attr_should_poll = False
    _attr_attribution = ATTRIBUTION

    def __init__(
        self,
        name: str,
        unique_id: str,
        description: SensorEntityDescription,
        updater: WeatherUpdater,
    ) -> None:
        """Initialize sensor."""
        self.entity_description = description
        self._updater = updater

        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = unique_id
        split_unique_id = unique_id.split("-")
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, f"{split_unique_id[0]}-{split_unique_id[1]}")},
            manufacturer=MANUFACTURER,
            name=DEFAULT_NAME,
        )

    @property
    def available(self) -> bool:
        """Is entity available."""
        return self._updater.last_update_success

    async def async_added_to_hass(self) -> None:
        """Connect to dispatcher listening for entity data notifications."""
        self.async_on_remove(
            self._updater.async_add_listener(self.async_write_ha_state)
        )

    async def async_update(self) -> None:
        """Update sensor data."""
        await self._updater.async_request_refresh()

    @property
    def native_value(self) -> StateType:
        """Sensor state in native units of measurement."""

        return self._updater.weather_data["fact"].get(self.entity_description.key, None)

    @property
    def icon(self):
        """Sensor icon."""
        if self.entity_description.key == ATTR_API_YA_CONDITION:
            return self._updater.weather_data["fact"].get(
                f"{ATTR_API_YA_CONDITION}_icon", None
            )
        else:
            return super().icon
