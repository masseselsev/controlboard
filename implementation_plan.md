# Implementation Plan - Dev Cleanup & Documentation

## Goal Description
Create a robust cleanup mechanism for the `controlboard` project to facilitate testing on clean environments. Document the project structure, usage, and development workflows.

## User Review Required
> [!IMPORTANT]
> **Installation Command**: The `setup.sh` script requires the script URL to be passed as an argument to `bash` (e.g., `bash -s "$url"`) for dynamic repository configuration. This is documented in `README.md`.

> [!NOTE]
> **Versioning**: All shell scripts must maintain a `SCRIPT_VERSION` variable that is incremented on every change.

> [!NOTE]
> **Documentation Sync**: `README.md` must be updated immediately to reflect any functional changes.

## Proposed Changes

### UI/UX Standardization
#### [MODIFY] [setup.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/setup.sh)
- [x] Standardize Headers: Double line `====`, centered text.
- [x] Standardize Logs: Use `[INFO]`, `[OK]`, `[WARN]`, `[ERROR]` prefixes.
- [x] Standardize Menu:
    - `1) ...`
    - `2) ...`
    - `3) Перезагрузка`
    - `0) Выход`
    - `00) Очистка` (Red)
- [x] Display firmware version in menu header: `МЕНЮ УПРАВЛЕНИЯ (VSM2 v.X.Y.Z)`.
- [ ] List available `Update*.hex` files under option 2.
- [ ] Remove `(app.py)` and `(autoflash.sh)` from menu text.

#### [MODIFY] [autoflash.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/autoflash.sh)
- [x] Standardize Headers.
- [x] Standardize File Menu: Change `[1]` to `1)`.
- [x] Standardize Exit Option: `0) Отмена/Выход`.
- [x] Filter files: Only show `Update*.hex`.

#### [MODIFY] [dev_cleanup.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/dev_cleanup.sh)
- [x] Standardize Headers and Logs.

### Logging & State Tracking
#### [MODIFY] [setup.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/setup.sh)
- [x] Implement `log_msg` function (targets `~/controlboard.log`).
- [x] Implement `track_change` function (targets `dev_init.txt`).
- [x] Track package installations (`python3-venv`).
- [x] Track user group additions (`dialout`).
- [x] Track directory creation.
- [x] Move `dev_init.txt` to `$INSTALL_DIR` at the end of execution.
- [x] Increment `SCRIPT_VERSION`.
- [x] Add "00" cleanup option to menu (Red color).

#### [MODIFY] [autoflash.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/autoflash.sh)
- [x] Implement `log_msg` and `track_change` (consistent with `setup.sh`).
- [x] Track package installations.
- [x] Log success/failure of flashing process.
- [x] Increment `SCRIPT_VERSION`.
- [x] Display current firmware version from `~/smalledge_fw_version`.

### Cleanup Mechanism
#### [NEW] [dev_cleanup.sh](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/dist/dev_cleanup.sh)
- [x] Read `dev_init.txt`.
- [x] Revert changes in reverse order (LIFO).
- [x] Remove installed packages.
- [x] Remove user from groups.
- [x] Delete `$INSTALL_DIR`.
- [x] Preserve `~/controlboard.log`.
- [x] Initialize `SCRIPT_VERSION`.

### Documentation
#### [NEW] [README.md](file:///c:/Users/masse/OneDrive/%D0%94%D0%BE%D0%BA%D1%83%D0%BC%D0%B5%D0%BD%D1%82%D1%8B/GitHub/controlboard/README.md)
- [x] Project Overview.
- [x] Installation Instructions (with correct `bash -s` command).
- [x] Usage Guide (`app.py`, `controlboard.py`).
- [x] Firmware Update Guide.
- [x] Development/Cleanup Guide.

## Verification Plan
### Manual Verification
- [x] Verify `dev_cleanup.sh` logic (dry run/code review).
- [x] Verify `README.md` instructions match script requirements.
