# Notify Actions for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/akentner/notify_actions.svg)](https://github.com/akentner/notify_actions/releases)
[![License](https://img.shields.io/github/license/akentner/notify_actions.svg)](LICENSE)

A Home Assistant custom component that creates custom notification services which fire events instead of sending actual notifications. Perfect for advanced automations where you want to intercept and handle notification calls programmatically.

## Features

- **Dual API Support**: Works with both legacy `notify.<action_id>` service calls and modern `notify.send_message` entity calls
- **Event-Driven**: Fires `notify_actions.message` events with all notification data
- **Optional Action Sequences**: Execute Home Assistant actions after firing the event
- **Template Support**: Use templates in action sequences with full access to notification data
- **Default Data**: Define default data that gets merged with notification calls
- **UI Configuration**: Complete UI-based setup via Config Flow and Options Flow
- **Multi-Language**: Includes English and German translations

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to "Integrations"
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add `https://github.com/akentner/notify_actions` as an integration
6. Click "Install"
7. Restart Home Assistant

### Manual Installation

1. Download the latest release from [GitHub](https://github.com/akentner/notify_actions/releases)
2. Extract the `custom_components/notify_actions` directory to your Home Assistant `custom_components` directory
3. Restart Home Assistant

## Configuration

### Adding a Notification Action

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for **"Notify Actions"**
4. Enter:
   - **Action ID**: Unique identifier (e.g., `my_notification`)
   - **Friendly Name**: Display name in the UI
   - **Action Sequence** (optional): Actions to execute after the event
   - **Default Data** (optional): Default data object for templates

### Configuring Action Sequences

After creating a notification action, you can configure optional action sequences via the **Configure** button:

- Use the visual ActionSelector (same as in automations)
- Add service calls, delays, conditions, etc.
- Use templates with these variables:
  - `message` - Notification message
  - `title` - Notification title
  - `target` - Notification target
  - `data` - Data object (merged with default_data)
  - `action_id` - The action ID
  - `friendly_name` - The friendly name

## Usage

### Calling the Notification Service

**Legacy API** (supports all parameters):
```yaml
service: notify.my_notification
data:
  message: "Hello World"
  title: "Test"
  data:
    custom_field: "value"
```

**Modern Entity API** (message + title only):
```yaml
service: notify.send_message
target:
  entity_id: notify.notify_actions_my_notification
data:
  message: "Hello World"
  title: "Test"
```

### Listening to Events

Create an automation that listens to the `notify_actions.message` event:

```yaml
trigger:
  - platform: event
    event_type: notify_actions.message
    event_data:
      action_id: my_notification
action:
  - service: persistent_notification.create
    data:
      title: "{{ trigger.event.data.title }}"
      message: "{{ trigger.event.data.message }}"
```

## Example Use Cases

### Custom Alert System with Default Data

Create a notification action with predefined defaults that get merged with call-time data:

1. Create action with ID `custom_alert`
2. Configure default data:
```yaml
priority: high
category: system
timeout: 30
custom_field: default_value
```

3. When you call the service, the default data is merged with your provided data:
```yaml
service: notify.custom_alert
data:
  message: "Alert!"
  data:
    priority: critical  # Overrides default "high"
    extra_field: "value"  # Added to defaults
    # timeout: 30 (inherited from defaults)
    # category: system (inherited from defaults)
```

4. The event will contain the merged data object accessible via the `data` template variable

### Notification Interceptor

Intercept all notification calls and route them through your own logic:

1. Create actions for different notification types
2. Use automations to handle the events
3. Apply custom filtering, throttling, or routing logic

## Architecture

### Dual API Implementation

- **Legacy Service** (`CustomNotifyActionService`): Supports all notification parameters
- **Modern Entity** (`CustomNotifyActionEntity`): Limited to message + title (Home Assistant constraint)

### Event Flow

1. Service/Entity receives notification call
2. Fire `notify_actions.message` event with all data
3. Execute optional action sequence (if configured)
4. Templates are pre-rendered before script execution

## Development

This component is designed to be simple and maintainable:

- Event-based architecture (no actual notifications)
- Template rendering via Home Assistant's Script helper
- UI-based configuration (no YAML needed)
- Both APIs share common code paths

## Troubleshooting

### Integration doesn't appear in UI
- Restart Home Assistant after installation
- Clear browser cache (Ctrl+Shift+R)

### Action sequence not executing
- Check Home Assistant logs: **Settings** → **System** → **Logs**
- Verify action sequence syntax via Options Flow
- Test templates in Developer Tools → Template

### Events not firing
- Listen to `notify_actions.message` in Developer Tools → Events
- Verify action_id matches your configuration
- Check that service call is reaching the integration

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Created by [Alexander Kentner](https://github.com/akentner)
