#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
    printf 'Usage: %s\n' "${0##*/}" >&2
    exit 2
fi

if ! command -v nmcli >/dev/null 2>&1; then
    printf 'NetworkManager (nmcli) is required.\n' >&2
    exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
    printf 'Python 3 is required.\n' >&2
    exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
applet_name=dns-toggle@didzislauva
source_dir=$script_dir/$applet_name/files/$applet_name
data_dir=${XDG_DATA_HOME:-"$HOME/.local/share"}
target_dir=$data_dir/cinnamon/applets/$applet_name

if [ ! -f "$source_dir/applet.js" ] || [ ! -f "$source_dir/metadata.json" ]; then
    printf 'Applet files are missing from %s.\n' "$source_dir" >&2
    exit 1
fi

mkdir -p "$target_dir"
cp -R "$source_dir/." "$target_dir/"

printf 'Installed DNS Switch to %s\n' "$target_dir"
printf 'Right-click the Cinnamon panel, open Applets, and add DNS Switch.\n'
printf 'Then right-click the switch and choose Configure to set your DNS address.\n'
