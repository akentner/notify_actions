# Custom Notify Actions

Create custom notification services that fire events instead of sending actual notifications.

## Why Use This?

Perfect for advanced Home Assistant automations where you want to:
- Intercept notification calls programmatically
- Apply custom logic before showing notifications
- Route notifications through your own systems
- Build notification throttling or filtering
- Create custom alert systems with dynamic behavior

## Key Features

✅ **Dual API Support** - Works with both legacy and modern notification APIs
✅ **Event-Driven** - Fires `notify_actions.message` events with full data
✅ **Action Sequences** - Execute actions after firing the event
✅ **Template Support** - Full template access to notification data
✅ **Default Data** - Pre-configure data that gets merged with calls
✅ **UI Configuration** - No YAML editing needed
✅ **Multi-Language** - English and German included

## Quick Start

1. Install via HACS
2. Add the **Notify Actions** integration
3. Create a notification action with a unique ID
4. Use `notify.<your_id>` in your automations
5. Listen to `notify_actions.message` events

## Example

**Call the service:**
```yaml
service: notify.my_alert
data:
  message: "Temperature too high!"
  title: "Warning"
```

**Handle the event:**
```yaml
trigger:
  platform: event
  event_type: notify_actions.message
  event_data:
    action_id: my_alert
action:
  - service: light.turn_on
    target:
      entity_id: light.status
    data:
      color_name: red
```

## Documentation

Full documentation available in the [GitHub repository](https://github.com/akentner/notify_actions).
