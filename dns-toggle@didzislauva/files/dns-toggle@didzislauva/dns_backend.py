#!/usr/bin/env python3
"""NetworkManager backend for the Cinnamon DNS Switch applet."""

import ipaddress
import json
import os
import re
import subprocess
import sys
import tempfile
from hashlib import sha256
from pathlib import Path


def run_nmcli(*args):
    result = subprocess.run(
        ["nmcli", *args], capture_output=True, text=True, check=False,
        env={**os.environ, "LC_ALL": "C"},
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or "NetworkManager command failed")
    return result.stdout.strip()


def parse_addresses(value, label, required=True):
    words = [word for word in re.split(r"[\s,]+", value.strip()) if word]
    if required and not words:
        raise ValueError(f"Set {label} in the applet settings first")
    addresses = []
    for word in words:
        try:
            address = str(ipaddress.IPv4Address(word))
        except ipaddress.AddressValueError as error:
            raise ValueError(f"Invalid IPv4 address in {label}: {word}") from error
        if address not in addresses:
            addresses.append(address)
    return addresses


def active_wifi():
    for row in run_nmcli("-t", "-f", "DEVICE,TYPE,STATE", "device", "status").splitlines():
        device, kind, state = row.split(":", 2)
        if kind == "wifi" and state == "connected":
            uuid = run_nmcli("-g", "GENERAL.CON-UUID", "device", "show", device)
            return device, uuid
    return None


PROFILE_FIELDS = (
    "ipv4.dns",
    "ipv4.ignore-auto-dns",
    "ipv6.dns",
    "ipv6.ignore-auto-dns",
)


def profile_settings(uuid):
    return {
        field: run_nmcli("-g", field, "connection", "show", uuid)
        for field in PROFILE_FIELDS
    }


def backup_path(uuid):
    state_home = Path(os.environ.get("XDG_STATE_HOME") or Path.home() / ".local/state")
    return state_home / "dns-toggle@didzislauva" / (sha256(uuid.encode()).hexdigest() + ".json")


def save_backup(uuid, settings):
    path = backup_path(uuid)
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    temporary = None
    try:
        descriptor, temporary = tempfile.mkstemp(prefix=".backup-", dir=path.parent)
        with os.fdopen(descriptor, "w", encoding="utf-8") as output:
            json.dump({"uuid": uuid, "settings": settings}, output)
            output.flush()
            os.fsync(output.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            pass  # Keep the first snapshot, even after repeated toggles.
    finally:
        if temporary is not None:
            os.unlink(temporary)


def restore_backup(uuid, device):
    path = backup_path(uuid)
    try:
        with path.open(encoding="utf-8") as source:
            backup = json.load(source)
    except FileNotFoundError as error:
        raise ValueError("No previous DNS settings were saved for this Wi-Fi") from error
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Saved DNS settings could not be read") from error
    if backup.get("uuid") != uuid or not isinstance(backup.get("settings"), dict):
        raise ValueError("Saved DNS settings do not match this Wi-Fi")
    settings = backup["settings"]
    if any(field not in settings or not isinstance(settings[field], str) for field in PROFILE_FIELDS):
        raise ValueError("Saved DNS settings are incomplete")

    run_nmcli(
        "connection", "modify", uuid,
        "ipv4.dns", settings["ipv4.dns"],
        "ipv4.ignore-auto-dns", settings["ipv4.ignore-auto-dns"],
        "ipv6.dns", settings["ipv6.dns"],
        "ipv6.ignore-auto-dns", settings["ipv6.ignore-auto-dns"],
    )
    run_nmcli("device", "reapply", device)
    path.unlink()


def current_mode(settings, custom, alternate):
    saved = settings["ipv4.dns"]
    addresses = [str(ipaddress.IPv4Address(value)) for value in re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", saved)]
    ipv4_auto = settings["ipv4.ignore-auto-dns"]
    ipv6_auto = settings["ipv6.ignore-auto-dns"]
    if ipv4_auto != "yes" or ipv6_auto != "yes":
        if not saved and not settings["ipv6.dns"] and ipv4_auto == "no" and ipv6_auto == "no":
            return "network"
        return "other"
    if custom and addresses == custom:
        return "custom"
    if addresses == alternate:
        return "alternate"
    return "other"


def main():
    if len(sys.argv) != 4 or sys.argv[1] not in ("mode", "toggle", "restore"):
        raise ValueError("Usage: dns_backend.py {mode|toggle|restore} CUSTOM_DNS ALTERNATE_DNS")
    command, custom_text, alternate_text = sys.argv[1:]
    if command == "restore":
        active = active_wifi()
        if not active:
            raise ValueError("No active Wi-Fi connection")
        restore_backup(active[1], active[0])
        print("restored")
        return

    custom = parse_addresses(custom_text, "custom DNS", required=False)
    alternate = parse_addresses(alternate_text, "alternate DNS")
    if custom and custom == alternate:
        raise ValueError("Custom and alternate DNS must differ")

    active = active_wifi()
    if not active:
        print("no-wifi")
        return
    device, uuid = active
    if not custom:
        if command == "mode":
            print("unconfigured")
            return
        raise ValueError("Set custom DNS in the applet settings first")

    settings = profile_settings(uuid)
    mode = current_mode(settings, custom, alternate)
    if command == "mode":
        print(mode)
        return

    save_backup(uuid, settings)
    target = alternate if mode == "custom" else custom
    run_nmcli(
        "connection", "modify", uuid,
        "ipv4.dns", " ".join(target),
        "ipv4.ignore-auto-dns", "yes",
        "ipv6.dns", "",
        "ipv6.ignore-auto-dns", "yes",
    )
    run_nmcli("device", "reapply", device)
    print("alternate" if mode == "custom" else "custom")


if __name__ == "__main__":
    try:
        main()
    except (RuntimeError, ValueError, OSError) as error:
        print(error, file=sys.stderr)
        sys.exit(1)
