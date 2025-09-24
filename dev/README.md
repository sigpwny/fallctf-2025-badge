# Badge software architecture

## Overview

The main architecture is cooperative multitasking with asyncio.

Tasks (may not be comprehensive):
- Display: draws to screen
- MainController: handles main menu interaction
- Wireless: handles ESP-Now communication
- Settings: manages defaults and user-adjustable settings
- GamePlay: manages gameplay
- peripheral tasks:
    - Joystick
    - PushButtons
    - Accelerometer
    - Buzzer
    
The `View` object is used by the MainController to communicate to the Display what to show on the screen.

Example flow:
> User moves the joystick down, which scrolls to the next menu item"
- joystick task detects motion
    - waits until enough motion triggers a "down" detection
    - publishes messages
- MainController task receives message (already subscribed to it from the start)
  - updates internal model of selection to move down
  - calls Display with new updated View

Another example flow:
> User pushes button to select an upgrade item
- button detections motion and publishes msg
- MainController (sub'ed) receives msg
    - tells GamePlay to update with the upgrade data
    - then updates Display with new View

The tasks are all bundled together in an `Environment`. There are two Environments currently (dev and test). The test environment does not have access to peripherals, wireless, and screens. Those classes will be simulated instead. This is to test the core functionality.

Instead of using `print` debugging, please use the internal `log` method.
