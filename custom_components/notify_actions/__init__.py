from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import Platform
from homeassistant.helpers import config_validation as cv

_LOGGER = logging.getLogger(__name__)

DOMAIN = "notify_actions"
PLATFORMS = [Platform.NOTIFY]
EVENT_NAME = "notify_actions.message"

# Integration is configured via UI only (Config Entry)
CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Notify Actions component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Notify Actions from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    # Initialise with the config entry; notify.py will add runtime objects.
    hass.data[DOMAIN][entry.entry_id] = {"config_entry": entry}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    domain_data = hass.data[DOMAIN].get(entry.entry_id, {})

    # Remove the manually registered notify service before the platform unload.
    action_id = domain_data.get("action_id") if isinstance(domain_data, dict) else None
    if action_id and hass.services.has_service("notify", action_id):
        hass.services.async_remove("notify", action_id)

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)

    return unload_ok
