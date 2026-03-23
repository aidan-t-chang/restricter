import subprocess
import sys
import winreg
import os

# --------------------------------------------------------------------------- #
#  Helpers
# --------------------------------------------------------------------------- #

IFEO_BASE = "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options"

# Exes already handled by the static menu — excluded from dynamic list
STATIC_EXES = {"msedge.exe", "chrome.exe"}


def r(cmd):
    """Run a PowerShell command, printing errors if any."""
    completed = subprocess.run(
        ["powershell", "-Command", cmd],
        capture_output=True, text=True, shell=True,
    )
    if completed.returncode != 0 and completed.stderr.strip():
        print(f"  [error] {completed.stderr.strip()}")
    return completed


def reg_key_exists(path):
    """Check whether a registry key exists."""
    result = r(f'Test-Path "{path}"')
    return result.stdout.strip().lower() == "true"


def reg_value_get(path, name):
    """Return a registry value as a string, or None if it doesn't exist."""
    result = r(
        f'try {{ (Get-ItemProperty -Path "{path}" -Name "{name}" '
        f'-ErrorAction Stop).{name} }} catch {{ }}'
    )
    val = result.stdout.strip()
    return val if val else None


def reg_value_set(path, name, value):
    """Create the key (if needed) and set a registry value."""
    r(f'New-Item -Path "{path}" -Force | Out-Null')
    r(f'Set-ItemProperty -Path "{path}" -Name "{name}" -Value {value} -Force')


def reg_value_remove(path, name):
    """Remove a registry value (ignore errors if it doesn't exist)."""
    r(f'Remove-ItemProperty -Path "{path}" -Name "{name}" -Force -ErrorAction SilentlyContinue')


# --------------------------------------------------------------------------- #
#  IFEO-based blocking  (works on ALL Windows editions)
#
#  Setting a "Debugger" value under:
#    HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\
#        Image File Execution Options\<exe>
#  causes Windows to try to launch the "debugger" instead.  Pointing it at
#  a non-existent path ("nul") effectively prevents the executable from
#  starting.
# --------------------------------------------------------------------------- #

def ifeo_is_blocked(exe_name):
    """Return True if the executable is currently IFEO-blocked."""
    result = subprocess.run(
        ["reg", "query", f"{IFEO_BASE}\\{exe_name}", "/v", "Debugger"],
        capture_output=True, text=True,
    )
    return result.returncode == 0


def ifeo_block(exe_name):
    """Block an executable via IFEO."""
    subprocess.run(
        ["reg", "add", f"{IFEO_BASE}\\{exe_name}",
         "/v", "Debugger", "/t", "REG_SZ", "/d", "block.exe", "/f"],
        capture_output=True, text=True,
    )


def ifeo_unblock(exe_name):
    """Unblock an executable by removing the IFEO Debugger entry."""
    subprocess.run(
        ["reg", "delete", f"{IFEO_BASE}\\{exe_name}",
         "/v", "Debugger", "/f"],
        capture_output=True, text=True,
    )


def ifeo_toggle(exe_name, friendly_name):
    """Toggle an executable's IFEO block and print the result."""
    if ifeo_is_blocked(exe_name):
        ifeo_unblock(exe_name)
        print(f"{friendly_name} has been UNBLOCKED.")
    else:
        ifeo_block(exe_name)
        print(f"{friendly_name} has been BLOCKED.")


# --------------------------------------------------------------------------- #
#  Individual toggle functions
# --------------------------------------------------------------------------- #

def toggle_edge():
    """Toggle Microsoft Edge (msedge.exe) via IFEO."""
    ifeo_toggle("msedge.exe", "Microsoft Edge")


def toggle_chrome():
    """Toggle Google Chrome (chrome.exe) via IFEO."""
    ifeo_toggle("chrome.exe", "Google Chrome")


def toggle_cmd():
    """Toggle Command Prompt via the DisableCMD registry policy.

    Values:  0 = enabled,  2 = disabled (scripts still allowed),  missing = enabled
    """
    policy_path = "HKCU:\\Software\\Policies\\Microsoft\\Windows\\System"
    current = reg_value_get(policy_path, "DisableCMD")

    if current is None or current == "0":
        reg_value_set(policy_path, "DisableCMD", 2)
        print("Command Prompt has been DISABLED.")
    else:
        reg_value_set(policy_path, "DisableCMD", 0)
        print("Command Prompt has been ENABLED.")


def toggle_regedit():
    """Toggle Registry Editor via the DisableRegistryTools registry policy.

    Values:  0 / missing = enabled,  1 = fully disabled
    """
    policy_path = "HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System"
    current = reg_value_get(policy_path, "DisableRegistryTools")

    if current is None or current == "0":
        reg_value_set(policy_path, "DisableRegistryTools", 1)
        print("Registry Editor has been DISABLED.")
    else:
        reg_value_set(policy_path, "DisableRegistryTools", 0)
        print("Registry Editor has been ENABLED.")


def toggle_msi_installer():
    """Toggle the Windows Installer (msiexec) via the DisableMSI policy.

    Values:  0 / missing = enabled,  1 = disabled for non-admins,  2 = always disabled
    """
    policy_path = "HKLM:\\Software\\Policies\\Microsoft\\Windows\\Installer"
    current = reg_value_get(policy_path, "DisableMSI")

    if current is None or current == "0":
        reg_value_set(policy_path, "DisableMSI", 2)
        print("MSI Installer has been DISABLED.")
    else:
        reg_value_set(policy_path, "DisableMSI", 0)
        print("MSI Installer has been ENABLED.")


def toggle_microsoft_store():
    """Toggle the Microsoft Store via the RemoveWindowsStore policy."""
    policy_path = "HKLM:\\SOFTWARE\\Policies\\Microsoft\\WindowsStore"
    current = reg_value_get(policy_path, "RemoveWindowsStore")

    if current is None or current == "0":
        reg_value_set(policy_path, "RemoveWindowsStore", 1)
        print("Microsoft Store has been DISABLED.")
    else:
        reg_value_set(policy_path, "RemoveWindowsStore", 0)
        print("Microsoft Store has been ENABLED.")


def toggle_total_lockdown():
    """Toggle total lockdown: Edge, Chrome, CMD, regedit, MSI, Store.

    If ANY of them are currently blocked, total lockdown is considered active
    and everything gets UNBLOCKED.  Otherwise everything gets BLOCKED.
    """
    targets_ifeo = [
        ("msedge.exe", "Microsoft Edge"),
        ("chrome.exe", "Google Chrome"),
    ]

    any_blocked = any(ifeo_is_blocked(exe) for exe, _ in targets_ifeo)

    cmd_val = reg_value_get("HKCU:\\Software\\Policies\\Microsoft\\Windows\\System", "DisableCMD")
    cmd_blocked = cmd_val is not None and cmd_val != "0"

    reg_val = reg_value_get("HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "DisableRegistryTools")
    reg_blocked = reg_val is not None and reg_val != "0"

    msi_val = reg_value_get("HKLM:\\Software\\Policies\\Microsoft\\Windows\\Installer", "DisableMSI")
    msi_blocked = msi_val is not None and msi_val != "0"

    store_val = reg_value_get("HKLM:\\SOFTWARE\\Policies\\Microsoft\\WindowsStore", "RemoveWindowsStore")
    store_blocked = store_val is not None and store_val != "0"

    lockdown_active = any_blocked or cmd_blocked or reg_blocked or msi_blocked or store_blocked

    if lockdown_active:
        print("Lockdown is currently ACTIVE — lifting all restrictions...")
        for exe, name in targets_ifeo:
            ifeo_unblock(exe)
            print(f"  {name}: unblocked")
        reg_value_set("HKCU:\\Software\\Policies\\Microsoft\\Windows\\System", "DisableCMD", 0)
        print("  Command Prompt: enabled")
        reg_value_set("HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "DisableRegistryTools", 0)
        print("  Registry Editor: enabled")
        reg_value_set("HKLM:\\Software\\Policies\\Microsoft\\Windows\\Installer", "DisableMSI", 0)
        print("  MSI Installer: enabled")
        reg_value_set("HKLM:\\SOFTWARE\\Policies\\Microsoft\\WindowsStore", "RemoveWindowsStore", 0)
        print("  Microsoft Store: enabled")
        print("Total lockdown LIFTED.")
    else:
        print("Engaging total lockdown...")
        for exe, name in targets_ifeo:
            ifeo_block(exe)
            print(f"  {name}: blocked")
        reg_value_set("HKCU:\\Software\\Policies\\Microsoft\\Windows\\System", "DisableCMD", 2)
        print("  Command Prompt: disabled")
        reg_value_set("HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "DisableRegistryTools", 1)
        print("  Registry Editor: disabled")
        reg_value_set("HKLM:\\Software\\Policies\\Microsoft\\Windows\\Installer", "DisableMSI", 2)
        print("  MSI Installer: disabled")
        reg_value_set("HKLM:\\SOFTWARE\\Policies\\Microsoft\\WindowsStore", "RemoveWindowsStore", 1)
        print("  Microsoft Store: disabled")
        print("Total lockdown ENGAGED.")


# --------------------------------------------------------------------------- #
#  Dynamic application discovery
# --------------------------------------------------------------------------- #

def get_installed_apps():
    """Scan the registry for installed apps that have a discoverable executable.

    Returns a list of dicts: {'name': str, 'exe': str}
    Apps whose executables are already in STATIC_EXES are excluded.

    Sources checked (low-complexity, high coverage):
      1. Uninstall keys — HKLM + HKCU, 64-bit + 32-bit
      2. DisplayIcon fallback when InstallLocation is missing
      3. App Paths keys — HKLM + HKCU (direct exe-name → path mapping)
    """
    apps = []
    seen_exes = set(STATIC_EXES)

    # --- 1 & 2: Uninstall keys (all four hive/bitness combinations) ---
    uninstall_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]

    for hive, reg_path in uninstall_paths:
        try:
            key = winreg.OpenKey(hive, reg_path)
        except OSError:
            continue

        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
            except OSError:
                break
            i += 1

            try:
                subkey = winreg.OpenKey(key, subkey_name)
                display_name, _ = winreg.QueryValueEx(subkey, "DisplayName")
            except (FileNotFoundError, OSError):
                continue

            install_location = None
            try:
                install_location, _ = winreg.QueryValueEx(subkey, "InstallLocation")
            except FileNotFoundError:
                pass

            display_icon = None
            try:
                display_icon, _ = winreg.QueryValueEx(subkey, "DisplayIcon")
            except FileNotFoundError:
                pass

            winreg.CloseKey(subkey)

            exe_name = None

            # Primary: look for an exe in the root of InstallLocation
            if install_location and os.path.isdir(install_location):
                try:
                    for f in os.listdir(install_location):
                        if f.lower().endswith(".exe") and f.lower() not in seen_exes:
                            exe_name = f
                            break
                except OSError:
                    pass

            # Fallback: DisplayIcon is usually "C:\path\to\app.exe,0"
            if not exe_name and display_icon:
                icon_path = display_icon.split(",")[0].strip().strip('"')
                if icon_path.lower().endswith(".exe") and os.path.isfile(icon_path):
                    candidate = os.path.basename(icon_path)
                    if candidate.lower() not in seen_exes:
                        exe_name = candidate

            if not exe_name:
                continue

            seen_exes.add(exe_name.lower())
            apps.append({"name": display_name, "exe": exe_name})

        winreg.CloseKey(key)

    # --- 3: App Paths keys (subkey name IS the exe name, default value is full path) ---
    app_paths_locations = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
        (winreg.HKEY_CURRENT_USER,  r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"),
    ]

    for hive, reg_path in app_paths_locations:
        try:
            key = winreg.OpenKey(hive, reg_path)
        except OSError:
            continue

        i = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(key, i)
            except OSError:
                break
            i += 1

            if not subkey_name.lower().endswith(".exe"):
                continue
            if subkey_name.lower() in seen_exes:
                continue

            try:
                subkey = winreg.OpenKey(key, subkey_name)
                exe_full_path = winreg.QueryValue(subkey, "")
                winreg.CloseKey(subkey)
            except OSError:
                continue

            exe_full_path = exe_full_path.strip().strip('"')
            if not os.path.isfile(exe_full_path):
                continue

            exe_name = os.path.basename(exe_full_path)
            seen_exes.add(exe_name.lower())
            apps.append({"name": subkey_name, "exe": exe_name})

        winreg.CloseKey(key)

    apps.sort(key=lambda a: a["name"].lower())
    return apps


def manage_installed_apps():
    """Sub-menu: toggle IFEO blocks for dynamically discovered installed apps."""
    print("\nScanning installed applications...")
    apps = get_installed_apps()

    if not apps:
        print("No additional installed applications found.")
        return

    while True:
        print("\n--- Installed Applications ---")
        for idx, app in enumerate(apps, start=1):
            status = "BLOCKED" if ifeo_is_blocked(app["exe"]) else "allowed"
            print(f"  {idx:3} — {app['name']} ({app['exe']}) [{status}]")
        print("    0 — Back to main menu")

        try:
            raw = input("Select application: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if raw.lower() in ("0", "b", "back", "q"):
            break

        try:
            choice = int(raw)
        except ValueError:
            print("Invalid input — enter a number from the list.")
            continue

        if 1 <= choice <= len(apps):
            app = apps[choice - 1]
            ifeo_toggle(app["exe"], app["name"])
        else:
            print(f"Invalid choice: {choice}")


# --------------------------------------------------------------------------- #
#  Menu / main loop
# --------------------------------------------------------------------------- #

def show_status():
    """Show current block/unblock status for all managed targets."""
    print("Current restriction status:")

    edge_blocked = ifeo_is_blocked("msedge.exe")
    print(f"  Microsoft Edge:   {'BLOCKED' if edge_blocked else 'allowed'}")

    chrome_blocked = ifeo_is_blocked("chrome.exe")
    print(f"  Google Chrome:    {'BLOCKED' if chrome_blocked else 'allowed'}")

    cmd_val = reg_value_get("HKCU:\\Software\\Policies\\Microsoft\\Windows\\System", "DisableCMD")
    cmd_blocked = cmd_val is not None and cmd_val != "0"
    print(f"  Command Prompt:   {'BLOCKED' if cmd_blocked else 'allowed'}")

    reg_val = reg_value_get("HKCU:\\Software\\Microsoft\\Windows\\CurrentVersion\\Policies\\System", "DisableRegistryTools")
    reg_blocked = reg_val is not None and reg_val != "0"
    print(f"  Registry Editor:  {'BLOCKED' if reg_blocked else 'allowed'}")

    msi_val = reg_value_get("HKLM:\\Software\\Policies\\Microsoft\\Windows\\Installer", "DisableMSI")
    msi_blocked = msi_val is not None and msi_val != "0"
    print(f"  MSI Installer:    {'BLOCKED' if msi_blocked else 'allowed'}")

    store_val = reg_value_get("HKLM:\\SOFTWARE\\Policies\\Microsoft\\WindowsStore", "RemoveWindowsStore")
    store_blocked = store_val is not None and store_val != "0"
    print(f"  Microsoft Store:  {'BLOCKED' if store_blocked else 'allowed'}")


MENU = """
==================================
       Application Restricter
==================================
  1 — Toggle Microsoft Edge
  2 — Toggle Google Chrome
  3 — Toggle Command Prompt
  4 — Toggle Total Lockdown
  5 — Toggle Registry Editor
  6 — Toggle MSI Installer
  7 — Toggle Microsoft Store
  8 — Show Current Status
  9 — Manage Installed Applications
  0 — Quit
==================================
"""

COMMANDS = {
    1: toggle_edge,
    2: toggle_chrome,
    3: toggle_cmd,
    4: toggle_total_lockdown,
    5: toggle_regedit,
    6: toggle_msi_installer,
    7: toggle_microsoft_store,
    8: show_status,
    9: manage_installed_apps,
}


def main():
    print(MENU)
    while True:
        try:
            raw = input("Enter command number: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if raw.lower() in ("q", "quit", "0"):
            print("Exiting.")
            break

        try:
            choice = int(raw)
        except ValueError:
            print("Invalid input — enter a number from the menu.")
            continue

        handler = COMMANDS.get(choice)
        if handler is None:
            print(f"Unknown command: {choice}")
            continue

        handler()
        print()  # blank line between commands


if __name__ == "__main__":
    main()

# implemented dynamic application finding and restriction (zoom doesn't work for some reason)
# also made script.py more viable for receiving commands from firebase

# - importlib.util loads ai-commandtoggle.py by file path, bypassing the hyphen issue
#   - COMMANDS maps integers 1–7 to the static toggle functions (8/show_status excluded since it's console output, not useful from mobile)
#   - check_cmd_value() now spawns a daemon thread when the rolling code changes, keeping the GUI responsive while PowerShell runs
#   - _dispatch_command() handles two cases:
#     - cmd_value 1–7 → calls the matching static toggle function
#     - cmd_value 9 → fetches app_exe from the database and calls ifeo_toggle directly