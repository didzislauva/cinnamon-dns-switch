# DNS Switch

A Cinnamon panel applet that switches the **active Wi-Fi connection** between a custom IPv4 DNS server and alternate IPv4 DNS servers. The panel label shows the saved mode for the current Wi-Fi. Click it to switch.

## Configure

Right-click the panel applet and choose **Configure**. Enter:

- **Custom DNS server:** your DNS server address, such as `192.0.2.53` (documentation example).
- **DNS servers when custom DNS is off:** defaults to Google DNS (`8.8.8.8, 8.8.4.4`).
- **Names shown in the panel:** optional labels, such as `NAS` and `Google`.

Both fields accept one or more IPv4 addresses separated by spaces or commas. The custom field starts empty, so the applet will not change DNS until you configure it.

The applet applies settings to the currently connected Wi-Fi profile through NetworkManager. Each Wi-Fi profile keeps its last DNS choice. On a different Wi-Fi, click the applet to apply your choice to that connection. The applet disables DNS learned automatically from that Wi-Fi, including IPv6 DNS, while either mode is selected. It does not change Ethernet or VPN profiles.

Before changing a Wi-Fi profile for the first time, the applet saves that profile's IPv4 and IPv6 DNS settings in your user state directory (`~/.local/state/dns-toggle@didzislauva/`, unless `XDG_STATE_HOME` is set). Repeated toggles keep the first backup. To restore it, right-click the applet and choose **Restore previous DNS settings**. The backup is removed after a successful restore. Backups cannot recover settings that were changed before this feature was installed.

If your custom DNS server is reachable only through a VPN, connect the VPN before switching to it. A Wi-Fi captive portal may require the network's own DNS until sign-in is complete.

## Requirements

- Cinnamon desktop
- NetworkManager with `nmcli`
- Python 3

Your account must be allowed to modify the active NetworkManager connection. Some systems may show an authentication prompt.

## Install locally

Copy `files/dns-toggle@didzislauva/` into `~/.local/share/cinnamon/applets/`, then add **DNS Switch** in Cinnamon's Applets settings.

## Source and license

All applet code is included in this package. Licensed under MIT; see `LICENSE`.
