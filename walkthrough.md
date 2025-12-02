# Dev Cleanup & Documentation

I have implemented a mechanism to track system changes made by the installation scripts and a cleanup script to revert them. I also added comprehensive documentation.

## Changes

### 1. State Tracking (`setup.sh`, `autoflash.sh`)
- **Global Log**: All scripts now write to `~/controlboard.log` with timestamps.
- **State File**: Revertible actions (installing packages, adding user to groups) are recorded in `controlboard/dev_init.txt` in the format `TYPE:VALUE`.
    - `PACKAGE:name`
    - `GROUP_USER:group:user`
    - `DIR:path`

### 2. Cleanup Script (`dist/dev_cleanup.sh`)
- Reads `dev_init.txt`.
- Reverts actions in reverse order (LIFO):
    - Removes packages (`apt remove`).
    - Removes user from groups (`deluser`).
- Deletes the project directory (`~/controlboard`).
- **Preserves**: `~/controlboard.log` and `~/smalledge_fw_version`.

### 3. Documentation (`README.md`)
- Created a root `README.md` describing:
    - Project overview.
    - Installation via `setup.sh`.
    - Usage of `app.py` and `controlboard.py`.
    - Firmware updating.
    - Developer mode (cleanup).

### 4. Interactive Menu (`setup.sh`)
- Added a hidden/developer option **00) Полная очистка** (displayed in red) to the main menu.
- This option executes `dev_cleanup.sh` directly from the menu interface.

## Critical Implementation Details

> [!IMPORTANT]
> **setup.sh Argument Passing**
> The `setup.sh` script relies on receiving its own URL as the first argument (`$1`) to correctly parse the GitHub user, repository, and branch.
>
> **Correct Installation Command:**
> `url=".../setup.sh"; wget -O - "$url" | bash -s "$url"`
>
> If `bash -s "$url"` is omitted, the script will default to hardcoded values, which may break installations from forks or non-main branches.

> [!NOTE]
> **Versioning Rule**
> All scripts (`setup.sh`, `autoflash.sh`, `dev_cleanup.sh`) MUST have a `SCRIPT_VERSION` variable. This version should be incremented with every modification to the file. If creating a new script, implement this versioning pattern immediately.

> [!NOTE]
> **Documentation Sync Rule**
> Any functional change to the scripts (e.g., new menu options, new arguments) MUST be immediately reflected in `README.md`.

## Verification
- **Manual Review**: Checked `dev_cleanup.sh` logic to ensure it handles the state file correctly and uses `sudo_smart`.
- **Safety**: Confirmed that `dev_cleanup.sh` checks for the existence of the directory before attempting removal.
