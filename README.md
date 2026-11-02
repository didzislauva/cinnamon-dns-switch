# Cinnamon DNS Switch

A Cinnamon panel applet for switching the active Wi-Fi connection between a custom DNS server and alternate DNS servers.

The applet saves each Wi-Fi profile's previous DNS settings before its first change. Use **Restore previous DNS settings** from the applet's right-click menu to return to them.

The Cinnamon Spices package is in [`dns-toggle@didzislauva/`](dns-toggle@didzislauva/). Its [README](dns-toggle@didzislauva/README.md) explains configuration and installation. The custom DNS address is configured through the applet's **Configure** menu.

## Install manually

On a computer running Cinnamon with NetworkManager, `nmcli`, and Python 3:

```bash
git clone https://github.com/didzislauva/cinnamon-dns-switch.git
cd cinnamon-dns-switch
./install.sh
```

Then right-click the Cinnamon panel, open **Applets**, find **DNS Switch**, and add it to the panel. Right-click the new switch and choose **Configure** to enter your custom DNS address. The alternate DNS defaults to Google (`8.8.8.8, 8.8.4.4`).

This applet is not yet in Cinnamon's built-in download catalog. The GitHub repository is the current installation source.

## Development

Run the backend tests with:

```bash
python3 -B -m unittest discover -s tests
```

Validate the package with the `validate-spice` script from the [Cinnamon Spices applets repository](https://github.com/linuxmint/cinnamon-spices-applets):

```bash
python3 validate-spice dns-toggle@didzislauva
```

Licensed under MIT; see [LICENSE](LICENSE).
