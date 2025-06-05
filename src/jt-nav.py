import os
import sys
import json
import re
import subprocess

DB_PATH   = os.path.expanduser("~/.cache/jdex/jt.json")
CONF_PATH = os.path.expanduser("~/.config/jdex/jt.conf")
DEFAULT_VAULT = "/mnt/nas"

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
    for k in default:
        if k not in data:
            data[k] = {}
    return data

def run_fzf(choices):
    try:
        p = subprocess.Popen(
            ["fzf", "--ansi", "--prompt=Select tag: "],
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
    vault = VAULT_PATH
    cwd = os.getcwd()
    prefix = vault + os.sep
    if not cwd.startswith(prefix):
        print(f"Error: Not inside vault directory ({vault}).", file=sys.stderr)
        sys.exit(1)

    dir_id = cwd[len(prefix):]
    if not RE_DIR_ID.match(dir_id):
        print(
            f"Error: Current directory '{cwd}' is not in 'vault/0000_0000_0000_0000' format.",
            file=sys.stderr
        )
        sys.exit(1)

    data = load_db()
    # Collect EXT tags where current dir appears in the "dirs" list
    ext_tags = [
        ext_tag for ext_tag, ext_info in data["ext"].items()
        if dir_id in ext_info.get("dirs", [])
    ]
    if not ext_tags:
        print(f"No tags refer to this directory ({dir_id}).")
        sys.exit(0)

    # Build choices "[EXT] name"
    choices = []
    for ext_tag in sorted(ext_tags):
        name = data["ext"][ext_tag].get("name", "")
        choices.append(f"[{ext_tag}] {name}")

    selection = run_fzf(choices)
    if not selection:
        sys.exit(0)

    token = extract_token(selection)
    if not token or not RE_EXT.match(token):
        print("Error: invalid selection.", file=sys.stderr)
        sys.exit(1)

    os.execvp("jt", ["jt", "tags", "list", token])

if __name__ == "__main__":
    main()

