# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Home Assistant Custom Component** called "Custom Notify Actions" that creates custom notification services which fire events instead of sending actual notifications. It's designed for advanced Home Assistant automations where users want to intercept and handle notification calls programmatically.

## Architecture

### Dual API Support
The component implements **two parallel notification APIs**:

1. **Legacy Service API** (`notify.<action_id>`): Implemented via `CustomNotifyActionService` (BaseNotificationService)
   - Supports all notification parameters: message, title, target, data, and arbitrary kwargs
   - Registered as `notify.<action_id>` service in notify.py:114-119

2. **Modern Entity API** (`notify.send_message`): Implemented via `CustomNotifyActionEntity` (NotifyEntity)
   - Supports only message and title parameters (Home Assistant limitation)
   - Creates a device in the UI with entity `notify.custom_notify_actions_<action_id>`

### Event Flow & Action Sequence
Both APIs follow this execution pattern:
1. Fire event `custom_notify_action.message` (defined in __init__.py:14)
   - Event data includes: `action_id`, `message`, `friendly_name`, plus any additional parameters
2. Execute optional action sequence (if configured via Options Flow)
   - Sequence is executed sequentially after the event
   - Templates are **pre-rendered** before script execution (notify.py:34-51 `_render_templates()`)
   - Uses Home Assistant's Script helper for execution with rendered values
   - Template variables available: `{{ message }}`, `{{ title }}`, `{{ target }}`, `{{ data }}`, `{{ action_id }}`, `{{ friendly_name }}`
   - Templates are rendered recursively through the entire action sequence structure

### Config Flow & Options Flow
- **Initial Setup** (config_flow.py): Creates a new notification action
  - Requires: `action_id` (unique identifier) and `friendly_name` (display name)
  - Prevents duplicate action_ids via unique_id validation (config_flow.py:35-36)

- **Options Flow** (config_flow.py:66-117): Configure action sequence (optional)
  - Accessible via "Configure" button in Integration UI
  - Uses ActionSelector for visual action configuration (like in automations/blueprints)
  - Validates action schema with cv.SCRIPT_SCHEMA
  - Changes trigger automatic integration reload

## Key Files

- `__init__.py`: Component setup, defines DOMAIN and EVENT_NAME constant
- `notify.py`: Core implementation with both service and entity classes
- `config_flow.py`: UI-based configuration for creating notification actions
- `manifest.json`: Component metadata (version, dependencies, etc.)
- `strings.json`: UI translations for config flow

## Development Notes

### Testing Changes
Since this is a Home Assistant custom component located in the config directory:
1. Restart Home Assistant after code changes
2. Check logs at Home Assistant → Settings → System → Logs
3. Test both APIs:
   - Legacy: Call `notify.<action_id>` service
   - Modern: Call `notify.send_message` with `entity_id: notify.custom_notify_actions_<action_id>`
4. Verify event fires using Developer Tools → Events → Listen to `custom_notify_action.message`
5. Test action sequences:
   - Configure via Integration → Configure button
   - Add YAML sequence (e.g., `- service: light.turn_on`)
   - Verify sequence executes after event fires
   - Check logs for execution errors

### Testing Action Sequences
Configure actions via Integration → Configure button using the visual ActionSelector UI.

Example templates you can use in action data fields:
- `{{ message }}` - The notification message
- `{{ title }}` - The notification title
- `{{ action_id }}` - The action ID
- `{{ data }}` - Additional data dict
- Mixed: `Received: {{ message }} from {{ action_id }}`

**Important**: Templates are pre-rendered before script execution via `_render_templates()` helper function (notify.py:34-51). This recursively processes all strings in the action sequence.

### Important Constraints
- This component is event-based and intentionally does NOT send actual notifications
- The entity implementation is limited to message + title only (Home Assistant's NotifyEntity constraint)
- The legacy service supports full parameter passthrough including data and target fields
- Each action_id must be unique across all configured instances
- Action sequences are optional and stored in config_entry.options
- Action sequences execute AFTER the event is fired (sequential, not parallel)
- Options changes trigger automatic integration reload
