const Applet = imports.ui.applet;
const Main = imports.ui.main;
const Mainloop = imports.mainloop;
const PopupMenu = imports.ui.popupMenu;
const Settings = imports.ui.settings;
const Util = imports.misc.util;

class DnsSwitchApplet extends Applet.TextIconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this._script = metadata.path + '/dns_backend.py';
        this._busy = false;
        this._removed = false;
        this.set_applet_icon_symbolic_name('network-server-symbolic');
        this.set_applet_label('DNS: …');
        this.set_applet_tooltip('Checking DNS settings');

        this.settings = new Settings.AppletSettings(this, metadata.uuid, instanceId);
        this.settings.bind('custom-dns', 'customDns', () => this._refresh());
        this.settings.bind('custom-name', 'customName', () => this._refresh());
        this.settings.bind('alternate-dns', 'alternateDns', () => this._refresh());
        this.settings.bind('alternate-name', 'alternateName', () => this._refresh());

        this._restoreItem = new PopupMenu.PopupMenuItem('Restore previous DNS settings');
        this._restoreItem.connect('activate', () => this._restore());
        this._applet_context_menu.addMenuItem(this._restoreItem);

        this._refresh();
        this._timer = Mainloop.timeout_add_seconds(10, () => {
            if (!this._busy) this._refresh();
            return true;
        });
    }

    _run(command, callback) {
        Util.spawnCommandLineAsyncIO('', (stdout, stderr, code) => {
            if (!this._removed) callback(stdout, stderr, code);
        }, {
            argv: ['python3', this._script, command, this.customDns || '', this.alternateDns || '']
        });
    }

    _show(mode) {
        if (mode === 'custom') {
            this.set_applet_label('DNS: ' + ((this.customName || '').trim() || 'Custom'));
            this.set_applet_tooltip('Custom DNS is on. Click to use alternate DNS.');
        } else if (mode === 'alternate') {
            this.set_applet_label('DNS: ' + ((this.alternateName || '').trim() || 'Alternate'));
            this.set_applet_tooltip('Alternate DNS is on. Click to use custom DNS.');
        } else if (mode === 'unconfigured') {
            this.set_applet_label('DNS: Setup');
            this.set_applet_tooltip('Set the custom DNS address in this applet’s settings.');
        } else if (mode === 'no-wifi') {
            this.set_applet_label('DNS: —');
            this.set_applet_tooltip('No active Wi-Fi connection');
        } else if (mode === 'network') {
            this.set_applet_label('DNS: Network');
            this.set_applet_tooltip('Using DNS supplied by this Wi-Fi network. Click to use custom DNS.');
        } else {
            this.set_applet_label('DNS: Other');
            this.set_applet_tooltip('Click to use custom DNS.');
        }
    }

    _refresh() {
        if (this._busy || this._removed) return;
        this._run('mode', (stdout, stderr, code) => {
            if (code === 0) {
                this._show(stdout.trim());
            } else {
                this.set_applet_label('DNS: Error');
                this.set_applet_tooltip(stderr.trim() || 'Could not read DNS settings');
            }
        });
    }

    on_applet_clicked() {
        if (this._busy) return;
        this._busy = true;
        this.set_applet_label('DNS: …');
        this._run('toggle', (stdout, stderr, code) => {
            this._busy = false;
            if (code === 0) {
                this._show(stdout.trim());
            } else {
                Main.notifyError('DNS switch failed', stderr.trim() || 'Check NetworkManager permissions.');
                this._refresh();
            }
        });
    }

    _restore() {
        if (this._busy) return;
        this._busy = true;
        this.set_applet_label('DNS: …');
        this._run('restore', (stdout, stderr, code) => {
            this._busy = false;
            if (code === 0) {
                Main.notify('DNS settings restored', 'Previous settings for this Wi-Fi have been restored.');
            } else {
                Main.notifyError('DNS restore failed', stderr.trim() || 'Could not restore previous settings.');
            }
            this._refresh();
        });
    }

    on_applet_removed_from_panel() {
        this._removed = true;
        if (this._timer) Mainloop.source_remove(this._timer);
        this.settings.finalize();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new DnsSwitchApplet(metadata, orientation, panelHeight, instanceId);
}
