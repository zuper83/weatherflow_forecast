"""Support for WeatherFlow sensor data."""
from __future__ import annotations

import logging

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
    DEGREE,
    EntityCategory,
    LIGHT_LUX,
    PERCENTAGE,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
    UnitOfVolumetricFlux,
    UV_INDEX,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util.dt import utc_from_timestamp

from . import WeatherFlowForecastDataUpdateCoordinator
from .const import (
    ATTR_ATTRIBUTION,
    CONCENTRATION_GRAMS_PER_CUBIC_METER,
    CONF_STATION_ID,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    TIMESTAMP_SENSORS,
)

@dataclass
class WeatherFlowSensorEntityDescription(SensorEntityDescription):
    """Describes WeatherFlow sensor entity."""


SENSOR_TYPES: tuple[WeatherFlowSensorEntityDescription, ...] = (
    WeatherFlowSensorEntityDescription(
        key="absolute_humidity",
        name="Absolute Humidity",
        native_unit_of_measurement=CONCENTRATION_GRAMS_PER_CUBIC_METER,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
        icon="mdi:water",
    ),
    WeatherFlowSensorEntityDescription(
        key="air_density",
        name="Air Density",
        native_unit_of_measurement=CONCENTRATION_MICROGRAMS_PER_CUBIC_METER,
        device_class=SensorDeviceClass.VOLATILE_ORGANIC_COMPOUNDS,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0,
    ),
    WeatherFlowSensorEntityDescription(
        key="air_temperature",
        name="Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="barometric_pressure",
        name="Barometric Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="beaufort",
        name="Beaufort",
        icon="mdi:windsock",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="brightness",
        name="Illuminance",
        native_unit_of_measurement=LIGHT_LUX,
        device_class=SensorDeviceClass.ILLUMINANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="cloud_base",
        name="Cloud Base",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:arrow-expand-vertical",
        suggested_display_precision=0
    ),
    WeatherFlowSensorEntityDescription(
        key="delta_t",
        name="Delta T",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,

    ),
    WeatherFlowSensorEntityDescription(
        key="dew_point",
        name="Dew Point",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="feels_like",
        name="Apparent Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="freezing_altitude",
        name="Freezing Altitude",
        native_unit_of_measurement=UnitOfLength.METERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0
    ),
    WeatherFlowSensorEntityDescription(
        key="heat_index",
        name="Heat Index",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="lightning_strike_count",
        name="Lightnings Strikes",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.TOTAL,
    ),
    WeatherFlowSensorEntityDescription(
        key="lightning_strike_count_last_1hr",
        name="Lightning Strikes last hour",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="lightning_strike_count_last_3hr",
        name="Lightning Strikes last 3 hours",
        icon="mdi:lightning-bolt",
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="lightning_strike_last_distance",
        name="Distance last lightning strike",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="lightning_strike_last_epoch",
        name="Time of last lightning strike",
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_rate",
        name="Precipitation Rate",
        native_unit_of_measurement=UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        device_class=SensorDeviceClass.PRECIPITATION_INTENSITY,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_accum_last_1hr",
        name="Precipitation last hour",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_accum_local_day",
        name="Precipitation today",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_accum_local_yesterday",
        name="Precipitation yesterday",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_minutes_local_day",
        name="Precipitation duration today",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_minutes_local_yesterday",
        name="Precipitation duration yesterday",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_accum_local_day_final",
        name="Precipitation today Checked",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_accum_local_yesterday_final",
        name="Precipitation yesterday Checked",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_minutes_local_day_final",
        name="Precipitation duration today Checked",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="precip_minutes_local_yesterday_final",
        name="Precipitation duration yesterday Checked",
        native_unit_of_measurement=UnitOfTime.MINUTES,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="pressure_trend",
        name="Pressure Trend",
        translation_key="pressure_trend",
        icon="mdi:trending-up",
    ),
    WeatherFlowSensorEntityDescription(
        key="relative_humidity",
        name="Humidity",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="sea_level_pressure",
        name="Sea Level Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    WeatherFlowSensorEntityDescription(
        key="solar_radiation",
        name="Solar Radiation",
        native_unit_of_measurement=UnitOfIrradiance.WATTS_PER_SQUARE_METER,
        device_class=SensorDeviceClass.IRRADIANCE,
        state_class=SensorStateClass.MEASUREMENT
    ),
    WeatherFlowSensorEntityDescription(
        key="station_pressure",
        name="Station Pressure",
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.ATMOSPHERIC_PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=1,
    ),
    WeatherFlowSensorEntityDescription(
        key="timestamp",
        name="Data Updated",
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
    ),
    WeatherFlowSensorEntityDescription(
        key="uv",
        name="UV Index",
        native_unit_of_measurement=UV_INDEX,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:sun-wireless",
        suggested_display_precision=1,
    ),
    WeatherFlowSensorEntityDescription(
        key="visibility",
        name="Visibility",
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
        device_class=SensorDeviceClass.DISTANCE,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=0
    ),
    WeatherFlowSensorEntityDescription(
        key="wet_bulb_globe_temperature",
        name="Wet Bulb Globe Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="wet_bulb_temperature",
        name="Wet Bulb Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_avg",
        name="Wind Speed",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_cardinal",
        name="Wind Cardinal",
        icon="mdi:compass",
        translation_key="wind_cardinal",
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_chill",
        name="Wind Chill",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_direction",
        name="Wind Direction",
        native_unit_of_measurement=DEGREE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:compass",
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_gust",
        name="Wind Gust",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    WeatherFlowSensorEntityDescription(
        key="wind_lull",
        name="Wind Lull",
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """WeatherFlow sensor platform."""
    coordinator: WeatherFlowForecastDataUpdateCoordinator = hass.data[DOMAIN][config_entry.entry_id]

    if coordinator.data.sensor_data == {}:
        return

    entities: list[WeatherFlowSensor[Any]] = [
        WeatherFlowSensor(coordinator, description, config_entry)
        for description in SENSOR_TYPES if getattr(coordinator.data.sensor_data, description.key) is not None
    ]

    async_add_entities(entities, False)

class WeatherFlowSensor(CoordinatorEntity[DataUpdateCoordinator], SensorEntity):
    """A WeatherFlow sensor."""

    entity_description: WeatherFlowSensorEntityDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: WeatherFlowForecastDataUpdateCoordinator,
        description: WeatherFlowSensorEntityDescription,
        config: MappingProxyType[str, Any]
    ) -> None:
        """Initialize a WeatherFlow sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._config = config

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._config.data[CONF_STATION_ID])},
            entry_type=DeviceEntryType.SERVICE,
            manufacturer=MANUFACTURER,
            model=MODEL,
            name=f"{self._config.data[CONF_NAME]} Sensors",
            configuration_url=f"https://tempestwx.com/station/{self._config.data[CONF_STATION_ID]}/grid",
        )
        self._attr_attribution = ATTR_ATTRIBUTION
        self._attr_unique_id = f"{config.data[CONF_STATION_ID]} {description.key}"

    @property
    def native_value(self) -> StateType:
        """Return state of the sensor."""

        if self.entity_description.key in TIMESTAMP_SENSORS:
            raw_data = getattr(self.coordinator.data.sensor_data,
                               self.entity_description.key) if self.coordinator.data.sensor_data else None
            return utc_from_timestamp(raw_data) if raw_data else None

        return (
            getattr(self.coordinator.data.sensor_data, self.entity_description.key)
            if self.coordinator.data.sensor_data else None
        )

    async def async_added_to_hass(self):
        """When entity is added to hass."""
        self.async_on_remove(
            self.coordinator.async_add_listener(self.async_write_ha_state)
        )
