# Implement Dynamic Firmware Version Check in Menu

The goal is to display the live firmware version in the menu when the controller is online, instead of relying solely on the cached file.

## User Review Required
>
> [!NOTE]
> The `check_fw_version` function in `setup.sh` currently uses `version_request` which returns a validation string. I will switch it to use `firmware_version` which returns the actual version strings (e.g., "V01.01").

## Proposed Changes

### `dist/setup.sh`

#### [MODIFY] [setup.sh](file:///d:/PROG/GitHub/controlboard/dist/setup.sh)

- Modify `check_fw_version` function:
  - Change command from `read version_request` to `read firmware_version`.
- Parse the output to extract the version (e.g., "V01.01") and append ".00" to match the file format (e.g., "V01.01.00").
  - Return `OK <VERSION>` (e.g., `OK V01.01.00`) on success.
- Modify the main loop:
  - Parse the result of `check_fw_version`.
  - If status is `OK`, update `CURRENT_FW` with the detected version.
  - If status is `FAIL`, keep `CURRENT_FW` as read from file (or "Неизвестно").

## Verification Plan

### Manual Verification

- The user will verify on the actual device that the menu displays the version correctly in the format `VXX.YY.00`.
- I will verify the script logic via inspection.
