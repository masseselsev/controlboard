# Configure SSH Port in Mass Flasher

## User Review Required
>
> [!NOTE]
> The default SSH port will be changed to `2222`. This is different from the standard `22`.

## Proposed Changes

### `mass_flasher`

#### [MODIFY] [ssh_utils.py](file:///d:/PROG/GitHub/controlboard/mass_flasher/ssh_utils.py)

- Update `FlashWorker.__init__` to accept `port` (default 22).
- Update `client.connect` call to use `port=self.port`.

#### [MODIFY] [app.py](file:///d:/PROG/GitHub/controlboard/mass_flasher/app.py)

- Update `flash_devices` route to extract `port` from request JSON (default 2222).
- Pass `port` to `FlashWorker`.

#### [MODIFY] [index.html](file:///d:/PROG/GitHub/controlboard/mass_flasher/templates/index.html)

- Add an input field for `SSH Port` with default value `2222`.
- Update `startFlash()` function to send `port` in the JSON payload.

## Verification Plan

### Automated Tests

- None (UI interaction required).

### Manual Verification

- Open the web UI.
- Verify "SSH Port" input exists and defaults to `2222`.
- Check that `FlashWorker` receives the correct port.
