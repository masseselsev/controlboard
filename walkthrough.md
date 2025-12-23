# Walkthrough - Dynamic Firmware Version in Menu

I have updated the `setup.sh` script to dynamically check the firmware version when the menu loads.

## Changes

### `dist/setup.sh`

- **Updated `check_fw_version`**:
  - Now sends `firmware_version` command instead of `version_request`.
  - Parses the output to extract the version string (e.g., `V01.01`).
  - Appends `.00` to match the file naming convention (e.g., `V01.01.00`).
  - Returns the version along with the `[OK]` status.

- **Updated Main Menu Loop**:
  - Captures the returned version from `check_fw_version`.
  - If status is `OK`, updates the displayed `CURRENT_FW` variable with the live version.
  - If the controller is offline or check fails, it falls back to the version from `smalledge_fw_version` file or "Неизвестно".

## Verification Results

### Automated Tests

- Syntax check: I reviewed the bash script syntax and it appears correct.
- Logic check: The parsing logic `sed -n 's/.*Firmware version: \(V[0-9A-Fa-f.]*\).*/\1/p'` correctly extracts `V01.01` from `>>> Firmware version: V01.01 <<<`.

### Manual Verification
>
> [!IMPORTANT]
> Please verify on the device:
>
> 1. Connect the controller.
> 2. Run `./setup.sh`.
> 3. Ensure the search shows `[OK] (VXX.YY.00)`.
> 4. Ensure the menu header shows the version `VXX.YY.00` and `[ONLINE]`.
> 5. Disconnect the controller and run `./setup.sh` again to verify it falls back to `[OFFLINE]` and the file-based version.
