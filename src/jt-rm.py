import os
import sys
import json
import re
import subprocess

DB_PATH   = os.path.expanduser("~/.cache/jdex/jt.json")
CONF_PATH = os.path.expanduser("~/.config/jdex/jt.conf")
DEFAULT_VAULT = "/mnt/nas"

COLOR_RESET = "\033[0m"
COLOR_EXT   = "\033[38;5;175m"  # pink-ish
COLOR_DIR   = "\033[38;5;141m"  # purple-ish

ICON_TAG = "\uf02b"   # \uf02b
ICON_DIR = "\uf07b"   # \uf73b

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")
RE_EXT     = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")

def load_vault_path():
    vault = DEFAULT_VAULT
    try:
        with open(CONF_PATH, "r") as cf:
            for line in cf:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key, val = key.strip(), val.strip()
                    if key == "vault" and val:
                        vault = val.rstrip("/")
    except FileNotFoundError:
        pass
    return vault

VAULT_PATH = load_vault_path()

def load_db():
    default = {"ac": {}, "id": {}, "ext": {}, "dir": {}}
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH, "w") as f:
            json.dump(default, f, indent=2)
        return default
    with open(DB_PATH, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = default
    for k in ("ac", "id", "ext", "dir"):
        if k not in data:
            data[k] = {}
    return data

def save_db(data):
    with open(DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def build_choices_for_dir(data, dir_id):
    choices = []
    for ext_tag in data["dir"].get(dir_id, {}).get("ext", []):
        ext_info = data["ext"].get(ext_tag, {})
        name = ext_info.get("name", "")
        choices.append(f"[{ext_tag}] {name}")
    return sorted(choices)

def run_fzf(choices):
    try:
        p = subprocess.Popen(
            ["fzf", "--ansi", "--prompt=Select EXT to remove: "],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
    except FileNotFoundError:
        print("Error: fzf not found. Please install fzf.", file=sys.stderr)
        sys.exit(1)

    stdout, _ = p.communicate("\n".join(choices))
    if p.returncode != 0:
        return None
    return stdout.strip()

def extract_token(line):
    if not line.startswith("["):
        return None
    end = line.find("]")
    if end == -1:
        return None
    return line[1:end]

def main():
    cwd = os.getcwd()
    vault_prefix = VAULT_PATH + os.sep
    if not cwd.startswith(vault_prefix):
        print(f"Error: Not inside vault directory ({VAULT_PATH}).", file=sys.stderr)
        sys.exit(1)

    dir_id = cwd[len(vault_prefix):]
    if not RE_DIR_ID.match(dir_id):
        print(
            f"Error: Current directory '{cwd}' is not in 'vault/0000_0000_0000_0000' format.",
            file=sys.stderr
        )
        sys.exit(1)

    data = load_db()

    choices = build_choices_for_dir(data, dir_id)
    if not choices:
        print(f"No EXT tags refer to this directory ({dir_id}).")
        sys.exit(0)

    selection = run_fzf(choices)
    if not selection:
        sys.exit(0)

    token = extract_token(selection)
    if not token or token not in data["ext"]:
        print("Error: could not parse selection or EXT not found.", file=sys.stderr)
        sys.exit(1)

    # Remove this dir from ext["dirs"]
    ext_info = data["ext"][token]
    dirs_list = ext_info.get("dirs", [])
    if dir_id in dirs_list:
        dirs_list.remove(dir_id)

    # Remove EXT from this dir's "ext" list
    data["dir"][dir_id]["ext"] = [
        e for e in data["dir"][dir_id]["ext"] if e != token
    ]

    save_db(data)

    name = ext_info.get("name", "")
    dir_name = data.get("dir", {}).get(dir_id, {}).get("name", "")
    print(
        f"{COLOR_EXT}{ICON_TAG} [{token}] {name} removed from "
        f"{COLOR_DIR}{ICON_DIR} {dir_id} {dir_name}{COLOR_RESET}"
    )
    sys.exit(0)

if __name__ == "__main__":
    main()

