# Enhance Tabbed Logging in Mass Flasher

## User Review Required
>
> [!NOTE]
> Client-side update for better tab management.

## Proposed Changes

### `mass_flasher`

#### [MODIFY] [templates/index.html](file:///d:/PROG/GitHub/controlboard/mass_flasher/templates/index.html)

- **CSS**:
  - Add styles for a `.close-tab` button inside `.tab-btn`.
  - Style it as a small `x` or `&times;` that is subtle but clickable.
- **JavaScript**:
  - Update `createTab`:
    - Append a `<span>` or `<button>` for closing inside the tab.
    - Add `onclick` event to this close button to call `closeTab(ip, event)`.
    - `event.stopPropagation()` is needed to prevent switching to the tab when closing it.
  - Implement `closeTab(ip, event)`:
    - Remove the button element.
    - Remove the content container.
    - Remove from `knownIps`.
    - Switch to 'all' or another tab if the closed one was active.
  - Add "Close All" button next to "Clear".
  - Implement `closeAllTabs()`:
    - Clear `knownIps`.
    - Remove all dynamic buttons and containers.
    - Switch to 'all'.

## Verification Plan

### Manual Verification

- Open UI.
- Generate some logs (or simulate).
- Click "x" on a tab -> Tab disappears.
- Click "Close All" -> All individual tabs disappear, only "All" remains.
