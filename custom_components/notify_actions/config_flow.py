from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.selector import ActionSelector, ObjectSelector

from . import DOMAIN

_LOGGER = logging.getLogger(__name__)

CONF_ACTION_ID = "action_id"
CONF_FRIENDLY_NAME = "friendly_name"
CONF_ACTION_SEQUENCE = "action_sequence"
CONF_DEFAULT_DATA = "default_data"


class CustomNotifyActionsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Custom Notify Actions."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            action_id = user_input[CONF_ACTION_ID]

            # Prüfe ob die Action ID bereits existiert
            await self.async_set_unique_id(action_id)
            self._abort_if_unique_id_configured()

            # ActionSelector returns a list directly (or empty list)
            action_sequence = user_input.get(CONF_ACTION_SEQUENCE, [])
            # ObjectSelector returns a dict (or empty dict)
            default_data = user_input.get(CONF_DEFAULT_DATA, {})

            # Validate if sequence is provided
            if action_sequence:
                try:
                    # Validate each action in the sequence
                    cv.SCRIPT_SCHEMA(action_sequence)
                except vol.Invalid as err:
                    _LOGGER.error(f"Invalid action sequence: {err}")
                    errors[CONF_ACTION_SEQUENCE] = "invalid_action"

            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_FRIENDLY_NAME],
                    data={
                        CONF_ACTION_ID: action_id,
                        CONF_FRIENDLY_NAME: user_input[CONF_FRIENDLY_NAME],
                    },
                    options={
                        CONF_ACTION_SEQUENCE: action_sequence,
                        CONF_DEFAULT_DATA: default_data,
                    },
                )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_ACTION_ID): str,
                vol.Required(CONF_FRIENDLY_NAME): str,
                vol.Optional(CONF_ACTION_SEQUENCE, default=[]): ActionSelector({}),
                vol.Optional(CONF_DEFAULT_DATA, default={}): ObjectSelector({}),
            }
        )

        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return OptionsFlowHandler()


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Custom Notify Actions."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        errors = {}

        if user_input is not None:
            friendly_name = user_input.get(CONF_FRIENDLY_NAME)
            # ActionSelector returns a list directly (or empty list)
            action_sequence = user_input.get(CONF_ACTION_SEQUENCE, [])
            # ObjectSelector returns a dict (or empty dict)
            default_data = user_input.get(CONF_DEFAULT_DATA, {})

            # Validate if sequence is provided
            if action_sequence:
                try:
                    # Validate each action in the sequence
                    cv.SCRIPT_SCHEMA(action_sequence)
                except vol.Invalid as err:
                    _LOGGER.error(f"Invalid action sequence: {err}")
                    errors[CONF_ACTION_SEQUENCE] = "invalid_action"

            if not errors:
                # Update title if friendly_name changed
                new_title = friendly_name if friendly_name else self.config_entry.title
                self.hass.config_entries.async_update_entry(
                    self.config_entry,
                    title=new_title,
                )

                return self.async_create_entry(
                    title="",
                    data={
                        CONF_FRIENDLY_NAME: friendly_name,
                        CONF_ACTION_SEQUENCE: action_sequence,
                        CONF_DEFAULT_DATA: default_data,
                    },
                )

        # Get current values from options (or data as fallback)
        current_friendly_name = self.config_entry.options.get(
            CONF_FRIENDLY_NAME,
            self.config_entry.data.get(CONF_FRIENDLY_NAME, "")
        )
        current_sequence = self.config_entry.options.get(CONF_ACTION_SEQUENCE, [])
        current_default_data = self.config_entry.options.get(CONF_DEFAULT_DATA, {})

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_FRIENDLY_NAME,
                    default=current_friendly_name,
                ): str,
                vol.Optional(
                    CONF_ACTION_SEQUENCE,
                    default=current_sequence,
                ): ActionSelector({}),
                vol.Optional(
                    CONF_DEFAULT_DATA,
                    default=current_default_data,
                ): ObjectSelector({}),
            }
        )

        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            errors=errors,
        )