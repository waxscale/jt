import os
import sys
import json
import re

DB_PATH   = os.path.expanduser("~/.cache/jdex/jt.json")

COLOR_RESET = "\033[0m"
COLOR_AC    = "\033[38;5;75m"
COLOR_ID    = "\033[38;5;107m"
COLOR_EXT   = "\033[38;5;175m"

ICON_TAG = "\uf02b"   # \uf02b

RE_AC     = re.compile(r"^[0-9]{2}$")
RE_ID     = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
RE_EXT    = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")

def load_db():
    default = {"ac": {}, "id": {}, "ext": {}, "dir": {}}
    if not os.path.exists(DB_PATH):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with open(DB_PATH,"w") as f:
            json.dump(default, f, indent=2)
        return default
    with open(DB_PATH,"r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = default
    for k in ("ac","id","ext","dir"):
        if k not in data:
            data[k] = {}
    return data

def save_db(data):
    with open(DB_PATH,"w") as f:
        json.dump(data, f, indent=2)

def rm_ac(ac_id):
    data = load_db()
    if ac_id not in data["ac"]:
        print(f"Error: AC '{ac_id}' does not exist.", file=sys.stderr)
        sys.exit(1)
    children = [k for k in data["id"] if k.startswith(f"{ac_id}.")]
    if children:
        print(f"Error: Cannot remove AC '{ac_id}' \u2014 it has child ID tags.", file=sys.stderr)
        sys.exit(1)
    del data["ac"][ac_id]
    save_db(data)
    print(f"{COLOR_AC}{ICON_TAG} [{ac_id}] removed{COLOR_RESET}")

def rm_id(id_tag):
    data = load_db()
    if id_tag not in data["id"]:
        print(f"Error: ID '{id_tag}' does not exist.", file=sys.stderr)
        sys.exit(1)
    children = [k for k in data["ext"] if k.startswith(f"{id_tag}+")]
    if children:
        print(f"Error: Cannot remove ID '{id_tag}' \u2014 it has child EXT tags.", file=sys.stderr)
        sys.exit(1)
    del data["id"][id_tag]
    save_db(data)
    print(f"{COLOR_ID}{ICON_TAG} [{id_tag}] removed{COLOR_RESET}")

def rm_ext(ext_tag):
    data = load_db()
    if ext_tag not in data["ext"]:
        print(f"Error: EXT '{ext_tag}' does not exist.", file=sys.stderr)
        sys.exit(1)
    ext_info = data["ext"][ext_tag]
    # Remove this ext_tag from every directory in its "dirs" list
    for dir_id in ext_info.get("dirs", []):
        if dir_id in data["dir"]:
            data["dir"][dir_id]["ext"] = [
                e for e in data["dir"][dir_id].get("ext", []) if e != ext_tag
            ]
            if not data["dir"][dir_id]["ext"]:
                del data["dir"][dir_id]
    del data["ext"][ext_tag]
    save_db(data)
    print(f"{COLOR_EXT}{ICON_TAG} [{ext_tag}] removed{COLOR_RESET}")

def main():
    if len(sys.argv) != 2:
        print("Usage: jt tags rm <AC | AC.ID | AC.ID+EXT>", file=sys.stderr)
        sys.exit(1)
    token = sys.argv[1].strip()
    if RE_AC.match(token):
        rm_ac(token)
    elif RE_ID.match(token):
        rm_id(token)
    elif RE_EXT.match(token):
        rm_ext(token)
    else:
        print(
            "Error: argument must be one of:\n"
            "  \u2022 AC      \u2192 2 digits (e.g. 01)\n"
            "  \u2022 AC.ID   \u2192 XX.YY   (e.g. 01.02)\n"
            "  \u2022 AC.ID+E \u2192 XX.YY+ZZZZ (e.g. 01.02+0001)",
            file=sys.stderr
        )
        sys.exit(1)

if __name__ == "__main__":
    main()

