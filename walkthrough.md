# Walkthrough - Refactoring setup.sh

I have refactored the `setup.sh` script to improve performance and maintainability.

## Changes

### `dist/setup.sh`

- **Optimization**: Moved `check_fw_version` function definition outside the `while true` loop. This prevents the function from being redefined on every iteration of the menu.
- **Cleanup**: Removed redundant comments (multiple "Получение версии прошивки").
- **Version Bump**: Updated `SCRIPT_VERSION` to "28".
- **Shebang**: Verified `#!/bin/bash` is present at the top.

## Verification

### Manual Verification

- The user should verify that the script runs correctly: `./setup.sh`.
- Check that the version "28" is displayed on startup.
- Check that the menu still functions correctly with the dynamic version check.
