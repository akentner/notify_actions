from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.notify import (
    ATTR_DATA,
    ATTR_MESSAGE,
    ATTR_TARGET,
    ATTR_TITLE,
    BaseNotificationService,
    NotifyEntity,
    NotifyEntityFeature,
)
import voluptuous as vol
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.script import Script
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, Context
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.const import CONF_VARIABLES
from homeassistant.helpers.template import Template
import copy

from . import DOMAIN, EVENT_NAME

_LOGGER = logging.getLogger(__name__)

CONF_ACTION_ID = "action_id"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_ACTION_SEQUENCE = "action_sequence"
CONF_DEFAULT_DATA = "default_data"


def _render_templates(data: Any, hass: HomeAssistant, variables: dict[str, Any]) -> Any:
    """Recursively render all templates in data structure."""
    if isinstance(data, str):
        # Check if string contains template syntax
        if "{{" in data or "{%" in data:
            try:
                template = Template(data, hass)
                return template.async_render(variables, parse_result=False)
            except Exception as err:
                _LOGGER.warning(f"Failed to render template '{data}': {err}")
                return data
        return data
    elif isinstance(data, dict):
        return {key: _render_templates(value, hass, variables) for key, value in data.items()}
    elif isinstance(data, list):
        return [_render_templates(item, hass, variables) for item in data]
    else:
        return data

async def async_get_service(
    hass: HomeAssistant,
    config: dict[str, Any],
    discovery_info: dict[str, Any] | None = None,
) -> BaseNotificationService | None:
    """Get the legacy notification service."""
    if discovery_info is None:
        return None

    entry_id = discovery_info.get("entry_id")
    if entry_id is None:
        return None

    config_entry = hass.data[DOMAIN].get(entry_id)
    if config_entry is None:
        return None

    action_id = config_entry.data[CONF_ACTION_ID]

    # Get friendly_name from options (if updated), otherwise from data
    friendly_name = config_entry.options.get(
        CONF_FRIENDLY_NAME,
        config_entry.data.get(CONF_FRIENDLY_NAME, "")
    )

    # Get action sequence and default data from options
    action_sequence = config_entry.options.get(CONF_ACTION_SEQUENCE, [])
    default_data = config_entry.options.get(CONF_DEFAULT_DATA, {})

    return CustomNotifyActionService(
        hass,
        action_id,
        friendly_name,
        action_sequence,
        default_data,
    )

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the notification platform."""
    action_id = config_entry.data[CONF_ACTION_ID]

    # Get friendly_name from options (if updated), otherwise from data
    friendly_name = config_entry.options.get(
        CONF_FRIENDLY_NAME,
        config_entry.data.get(CONF_FRIENDLY_NAME, "")
    )

    # Get action sequence and default data from options (if configured)
    # ActionSelector returns a list directly (no YAML parsing needed)
    action_sequence = config_entry.options.get(CONF_ACTION_SEQUENCE, [])
    default_data = config_entry.options.get(CONF_DEFAULT_DATA, {})

    if action_sequence and isinstance(action_sequence, list):
        _LOGGER.info(
            f"Action sequence loaded for '{action_id}' with {len(action_sequence)} actions"
        )

    if default_data:
        _LOGGER.info(
            f"Default data loaded for '{action_id}': {default_data}"
        )

    # Create NotifyEntity for notify.send_message support
    entity = CustomNotifyActionEntity(
        hass,
        config_entry.entry_id,
        action_id,
        friendly_name,
        action_sequence,
        default_data,
    )

    async_add_entities([entity])

    # Register legacy service for notify.<action_id> support
    service = CustomNotifyActionService(
        hass,
        action_id,
        friendly_name,
        action_sequence,
        default_data,
    )

    # Define service schema to properly extract message and other parameters
    service_schema = vol.Schema(
        {
            vol.Required(ATTR_MESSAGE): cv.string,
            vol.Optional(ATTR_TITLE): cv.string,
            vol.Optional(ATTR_TARGET): vol.All(cv.ensure_list, [cv.string]),
            vol.Optional(ATTR_DATA): dict,
        },
        extra=vol.ALLOW_EXTRA,  # Allow additional parameters
    )

    async def service_handler(call):
        """Handle the service call and extract parameters."""
        message = call.data.get(ATTR_MESSAGE, "")
        kwargs = {k: v for k, v in call.data.items() if k != ATTR_MESSAGE}
        await service.async_send_message(message, **kwargs)

    hass.states.async_set("notify." + action_id, friendly_name)
    hass.services.async_register(
        "notify",
        action_id,
        service_handler,
        schema=service_schema,
    )

    # Register options update listener
    config_entry.async_on_unload(
        config_entry.add_update_listener(async_reload_entry)
    )

    _LOGGER.info(
        f"Notification action '{action_id}' registered with event '{EVENT_NAME}'"
    )


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)


class CustomNotifyActionService(BaseNotificationService):
    """Legacy notification service implementation for notify.<action_id>."""

    def __init__(
        self,
        hass: HomeAssistant,
        action_id: str,
        friendly_name: str,
        action_sequence: list | None = None,
        default_data: dict | None = None,
    ) -> None:
        """Initialize the service."""
        self.hass = hass
        self._action_id = action_id
        self._friendly_name = friendly_name
        self._action_sequence = action_sequence
        self._default_data = default_data or {}

    async def async_send_message(self, message: str = "", **kwargs: Any) -> None:
        """Send a message via event with all parameters, then execute action sequence."""
        # Start with default data (copy to avoid mutation)
        merged_data = copy.deepcopy(self._default_data)

        # Merge with data from kwargs if present
        if ATTR_DATA in kwargs:
            merged_data.update(kwargs[ATTR_DATA])

        event_data = {
            "action_id": self._action_id,
            "message": message,
            "friendly_name": self._friendly_name,
            "data": merged_data,
        }

        # Add title if present
        if ATTR_TITLE in kwargs:
            event_data["title"] = kwargs[ATTR_TITLE]

        # Add target if present
        if ATTR_TARGET in kwargs:
            event_data["target"] = kwargs[ATTR_TARGET]

        # Add all other kwargs
        for key, value in kwargs.items():
            if key not in event_data and key not in [ATTR_TITLE, ATTR_TARGET, ATTR_DATA]:
                event_data[key] = value

        # Fire the event first
        self.hass.bus.async_fire(EVENT_NAME, event_data)

        _LOGGER.debug(
            f"Event '{EVENT_NAME}' fired from legacy service with data: {event_data}"
        )

        # Then execute action sequence if configured
        if self._action_sequence:
            _LOGGER.debug(f"Executing action sequence for '{self._action_id}' with variables: {event_data}")
            try:
                # Validate and transform the action sequence through schema
                # This converts plain dicts to proper objects (e.g., variables blocks)
                validated_sequence = cv.SCRIPT_SCHEMA(self._action_sequence)

                # Create a context for the script execution
                context = Context()

                # Create and run script with variables (let Script handle template rendering)
                script = Script(
                    self.hass,
                    validated_sequence,
                    f"Notify Action: {self._action_id}",
                    DOMAIN,
                    script_mode="queued",
                    max_runs=10,
                )

                await script.async_run(
                    run_variables=event_data,
                    context=context,
                )
            except vol.Invalid as err:
                _LOGGER.error(
                    f"Invalid action sequence for '{self._action_id}': {err}"
                )
            except Exception as err:
                _LOGGER.error(
                    f"Error executing action sequence for '{self._action_id}': {err}"
                )


class CustomNotifyActionEntity(NotifyEntity):
    """NotifyEntity implementation for notify.send_message support."""

    _attr_has_entity_name = True
    _attr_name = None

    def __init__(
        self,
        hass: HomeAssistant,
        entry_id: str,
        action_id: str,
        friendly_name: str,
        action_sequence: list | None = None,
        default_data: dict | None = None,
    ) -> None:
        """Initialize the entity."""
        self.hass = hass
        self._entry_id = entry_id
        self._action_id = action_id
        self._attr_unique_id = f"{DOMAIN}_{action_id}"
        self._friendly_name = friendly_name
        self._attr_supported_features = NotifyEntityFeature(0)
        self._action_sequence = action_sequence
        self._default_data = default_data or {}

    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry_id)},
            "name": self._friendly_name,
            "manufacturer": "Notify Actions",
            "model": "Notify Action Entity",
        }

    async def async_send_message(self, message: str, title: str | None = None) -> None:
        """Send a message via event (notify.send_message only supports message and title), then execute action sequence."""
        # Use default data (copy to avoid mutation)
        # Note: Entity API doesn't support data parameter, so only default_data is used
        event_data = {
            "action_id": self._action_id,
            "message": message,
            "friendly_name": self._friendly_name,
            "data": copy.deepcopy(self._default_data),
        }

        if title:
            event_data["title"] = title

        # Fire the event first
        self.hass.bus.async_fire(EVENT_NAME, event_data)

        _LOGGER.debug(
            f"Event '{EVENT_NAME}' fired from entity with data: {event_data}"
        )

        # Then execute action sequence if configured
        if self._action_sequence:
            _LOGGER.debug(f"Executing action sequence for entity '{self._action_id}' with variables: {event_data}")
            try:
                # Validate and transform the action sequence through schema
                # This converts plain dicts to proper objects (e.g., variables blocks)
                validated_sequence = cv.SCRIPT_SCHEMA(self._action_sequence)

                # Create a context for the script execution
                context = Context()

                # Create and run script with variables (let Script handle template rendering)
                script = Script(
                    self.hass,
                    validated_sequence,
                    f"Notify Action Entity: {self._action_id}",
                    DOMAIN,
                    script_mode="queued",
                    max_runs=10,
                )

                await script.async_run(
                    run_variables=event_data,
                    context=context,
                )
            except vol.Invalid as err:
                _LOGGER.error(
                    f"Invalid action sequence for entity '{self._action_id}': {err}"
                )
            except Exception as err:
                _LOGGER.error(
                    f"Error executing action sequence for entity '{self._action_id}': {err}"
                )