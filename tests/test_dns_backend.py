import importlib.util
import io
import json
import os
import pathlib
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch


BACKEND = (
    pathlib.Path(__file__).resolve().parents[1]
    / "dns-toggle@didzislauva/files/dns-toggle@didzislauva/dns_backend.py"
)
spec = importlib.util.spec_from_file_location("dns_backend", BACKEND)
backend = importlib.util.module_from_spec(spec)
spec.loader.exec_module(backend)


class DnsBackendTests(unittest.TestCase):
    def test_rejects_invalid_address(self):
        with self.assertRaisesRegex(ValueError, "Invalid IPv4 address"):
            backend.parse_addresses("192.168.8.999", "custom DNS")

    def test_switches_from_custom_to_alternate_on_active_wifi(self):
        calls = []

        def fake_nmcli(*args):
            calls.append(args)
            if args[:2] == ("-t", "-f"):
                return "wlp3s0:wifi:connected"
            if args[:2] == ("-g", "GENERAL.CON-UUID"):
                return "wifi-uuid"
            if args[:2] == ("-g", "ipv4.dns"):
                return "192.0.2.53"
            if args[:2] in (("-g", "ipv4.ignore-auto-dns"), ("-g", "ipv6.ignore-auto-dns")):
                return "yes"
            return ""

        output = io.StringIO()
        with tempfile.TemporaryDirectory() as state_home, patch.dict(
            os.environ, {"XDG_STATE_HOME": state_home}
        ), patch.object(backend, "run_nmcli", side_effect=fake_nmcli), patch.object(
            sys, "argv", ["dns_backend.py", "toggle", "192.0.2.53", "8.8.8.8, 8.8.4.4"]
        ), redirect_stdout(output):
            backend.main()
            self.assertTrue(backend.backup_path("wifi-uuid").is_file())

        self.assertEqual(output.getvalue().strip(), "alternate")
        self.assertIn(
            (
                "connection", "modify", "wifi-uuid", "ipv4.dns", "8.8.8.8 8.8.4.4",
                "ipv4.ignore-auto-dns", "yes", "ipv6.dns", "", "ipv6.ignore-auto-dns", "yes"
            ),
            calls,
        )
        self.assertIn(("device", "reapply", "wlp3s0"), calls)

    def test_restore_keeps_first_snapshot_and_restores_all_dns_fields(self):
        original = {
            "ipv4.dns": "",
            "ipv4.ignore-auto-dns": "no",
            "ipv6.dns": "2001:4860:4860::8888",
            "ipv6.ignore-auto-dns": "no",
        }
        calls = []

        def fake_nmcli(*args):
            calls.append(args)
            return ""

        with tempfile.TemporaryDirectory() as state_home, patch.dict(
            os.environ, {"XDG_STATE_HOME": state_home}
        ), patch.object(backend, "run_nmcli", side_effect=fake_nmcli):
            backend.save_backup("wifi-uuid", original)
            backend.save_backup("wifi-uuid", {**original, "ipv4.dns": "8.8.8.8"})
            path = backend.backup_path("wifi-uuid")
            self.assertEqual(json.loads(path.read_text())["settings"], original)

            backend.restore_backup("wifi-uuid", "wlp3s0")
            self.assertFalse(path.exists())

        self.assertIn(
            (
                "connection", "modify", "wifi-uuid",
                "ipv4.dns", "", "ipv4.ignore-auto-dns", "no",
                "ipv6.dns", "2001:4860:4860::8888", "ipv6.ignore-auto-dns", "no",
            ), calls,
        )
        self.assertIn(("device", "reapply", "wlp3s0"), calls)

    def test_unconfigured_mode_never_modifies_network(self):
        calls = []

        def fake_nmcli(*args):
            calls.append(args)
            if args[:2] == ("-t", "-f"):
                return "wlp3s0:wifi:connected"
            if args[:2] == ("-g", "GENERAL.CON-UUID"):
                return "wifi-uuid"
            raise AssertionError("Unexpected NetworkManager call")

        output = io.StringIO()
        with patch.object(backend, "run_nmcli", side_effect=fake_nmcli), patch.object(
            sys, "argv", ["dns_backend.py", "mode", "", "8.8.8.8, 8.8.4.4"]
        ), redirect_stdout(output):
            backend.main()

        self.assertEqual(output.getvalue().strip(), "unconfigured")
        self.assertFalse(any(call[0] == "connection" for call in calls))


if __name__ == "__main__":
    unittest.main()
