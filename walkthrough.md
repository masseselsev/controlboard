# Walkthrough - Refined Version Parsing

I have updated `setup.sh` and `autoflash.sh` to ensure consistent version formatting (`V01.01.00`).

## Changes

### `dist/setup.sh` (v29)

- **Parsing Logic**: Updated to handle `>>> Update Version: 1.1.0`.
  - Extracts `1.1.0`.
  - Formats as `V01.01.00` (pad with zeros, prepend V).
- **Fallback Logic**: When reading from `smalledge_fw_version`, automatically adds `V` prefix if missing.

### `dist/autoflash.sh` (v23)

- **Logging**: Now writes the version with `V` prefix to `smalledge_fw_version` (e.g., `Was installed: V01.01.00`).

## Verification

### Manual Verification
>
> [!IMPORTANT]
> Please verify on the device:
>
> 1. Run `./setup.sh`.
> 2. Expect `[OK] (V01.01.00)`.
> 3. Menu header: `VSM2 V01.01.00`.
> 4. (Optional) Run a flash cycle or check `smalledge_fw_version` after flashing to see the new format.
