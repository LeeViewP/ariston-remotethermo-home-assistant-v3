"""Support for Ariston sensors."""
from __future__ import annotations

import logging

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .entity import AristonEntity
from .const import (
    ARISTON_SELECT_TYPES,
    COORDINATOR,
    DOMAIN,
    ENERGY_COORDINATOR,
    AristonSelectEntityDescription,
)
from .coordinator import DeviceDataUpdateCoordinator, DeviceEnergyUpdateCoordinator
from .ariston import (
    DeviceAttribute,
    DeviceFeatures,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the Ariston binary sensors from config entry."""
    coordinator: DeviceDataUpdateCoordinator = hass.data[DOMAIN][entry.unique_id][
        COORDINATOR
    ]

    ariston_select: list[SelectEntity] = []

    if (
        coordinator.device.features[DeviceFeatures.HAS_METERING]
        and coordinator.device.extra_energy_features
    ):
        energy_coordinator: DeviceEnergyUpdateCoordinator = hass.data[DOMAIN][
            entry.unique_id
        ][ENERGY_COORDINATOR]

        for description in ARISTON_SELECT_TYPES:
            ariston_select.append(
                AristonSelect(
                    energy_coordinator,
                    description,
                )
            )

    async_add_entities(ariston_select)


class AristonSelect(AristonEntity, SelectEntity):
    """Base class for specific ariston binary sensors"""

    def __init__(
        self,
        coordinator: DeviceEnergyUpdateCoordinator,
        description: AristonSelectEntityDescription,
    ) -> None:
        super().__init__(coordinator)

        self.entity_description = description
        self.coordinator = coordinator

    @property
    def unique_id(self):
        """Return the unique id."""
        return (
            f"{self.coordinator.device.attributes[DeviceAttribute.GW_ID]}-{self.name}"
        )

    @property
    def current_option(self):
        """Return current selected option."""
        return self.entity_description.enum_class(
            self.coordinator.device.consumptions_settings[self.entity_description.key]
        ).name

    @property
    def options(self):
        """Return options"""
        return [c.name for c in self.entity_description.enum_class]

    async def async_select_option(self, option: str):
        await self.coordinator.device.async_set_consumptions_settings(
            self.entity_description.key,
            self.entity_description.enum_class[option],
        )
        self.async_write_ha_state()
