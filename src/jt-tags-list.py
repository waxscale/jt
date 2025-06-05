import os
import sys
import json
import re

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

COLOR_RESET = "\033[0m"
COLOR_AC    = "\033[38;5;75m"    # blue-ish for AC
COLOR_ID    = "\033[38;5;107m"   # green-ish for ID
COLOR_EXT   = "\033[38;5;175m"   # pink-ish for EXT
COLOR_DIR   = "\033[38;5;141m"   # purple-ish for DIR

ICON_TAG  = "\uf02b"   # \uf02b
ICON_DIR  = "\uf07b"   # \uf73b
LEFT_ARROW = f"{COLOR_EXT}\u2190{COLOR_RESET}"

RE_AC     = re.compile(r"^[0-9]{2}$")                       # \u201cXX\u201d
RE_ID     = re.compile(r"^[0-9]{2}\.[0-9]{2}$")             # \u201cXX.YY\u201d
RE_EXT    = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")   # \u201cXX.YY+ZZZZ\u201d
RE_DIR_ID = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")        # \u201c0000_0000_0000_0000\u201d

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

def print_ac(ac_id, data, indent=0):
    name = data["ac"][ac_id]["name"]
    print(" " * indent + f"{COLOR_AC}{ICON_TAG} [{ac_id}] {name}{COLOR_RESET}")

def print_id(id_tag, data, indent=2):
    name = data["id"][id_tag]["name"]
    print(" " * indent + f"{COLOR_ID}{ICON_TAG} [{id_tag}] {name}{COLOR_RESET}")

def print_ext(ext_tag, data, indent=4, show_dir=False):
    ext_info = data["ext"][ext_tag]
    name     = ext_info["name"]
    print(" " * indent + f"{COLOR_EXT}{ICON_TAG} [{ext_tag}] {name}{COLOR_RESET}")
    if show_dir:
        # Gather directories and sort by directory name
        dirs_list = ext_info.get("dirs", [])
        dir_entries = []
        for dir_id in dirs_list:
            dir_entry = data["dir"].get(dir_id, {})
            dir_name  = dir_entry.get("name", "")
            dir_entries.append((dir_id, dir_name))
        # sort alphabetically by dir_name
        dir_entries.sort(key=lambda x: x[1].lower())
        for dir_id, dir_name in dir_entries:
            print(" " * (indent + 2) +
                  f"{COLOR_DIR}{ICON_DIR} [{dir_id}] {dir_name}{COLOR_RESET}")

def list_all_ac(data):
    if not data["ac"]:
        print("No AC tags defined.")
        return
    for ac_id in sorted(data["ac"]):
        print_ac(ac_id, data)

def list_ac_and_ids(ac_id, data):
    if ac_id not in data["ac"]:
        print(f"Error: AC '{ac_id}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_ac(ac_id, data)
    for id_tag in sorted(data["id"]):
        if id_tag.startswith(f"{ac_id}."):
            print_id(id_tag, data)

def list_id_and_ext(ac_id, id_tag, data, show_all):
    if ac_id not in data["ac"]:
        print(f"Error: AC '{ac_id}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_ac(ac_id, data)
    if id_tag not in data["id"]:
        print(f"Error: ID '{id_tag}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_id(id_tag, data)
    for ext_tag in sorted(data["ext"]):
        if ext_tag.startswith(f"{id_tag}+"):
            print_ext(ext_tag, data, show_dir=show_all)

def list_ext_full(ext_tag, data):
    id_part = ext_tag.split("+")[0]
    ac_id   = id_part.split(".")[0]

    if ac_id not in data["ac"]:
        print(f"Error: AC '{ac_id}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_ac(ac_id, data)

    if id_part not in data["id"]:
        print(f"Error: ID '{id_part}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_id(id_part, data)

    if ext_tag not in data["ext"]:
        print(f"Error: EXT '{ext_tag}' does not exist.", file=sys.stderr)
        sys.exit(1)
    print_ext(ext_tag, data, show_dir=True)

def main():
    data = load_db()
    args = sys.argv[1:]

    show_all = False
    if args and args[0] in ("-a", "--all"):
        show_all = True
        args = args[1:]

    if len(args) > 1:
        print("Usage: jt tags list [-a|--all] [AC | AC.ID | AC.ID+EXT]", file=sys.stderr)
        sys.exit(1)

    if not args:
        list_all_ac(data)
        return

    token = args[0].strip()
    if RE_AC.match(token):
        list_ac_and_ids(token, data)
    elif RE_ID.match(token):
        ac_part = token.split(".")[0]
        list_id_and_ext(ac_part, token, data, show_all)
    elif RE_EXT.match(token):
        list_ext_full(token, data)
    else:
        print(
            "Error: argument must be one of:\n"
            "  \u2022 AC        \u2192 two digits (e.g. 31)\n"
            "  \u2022 AC.ID     \u2192 XX.YY (e.g. 31.11)\n"
            "  \u2022 AC.ID+EXT \u2192 XX.YY+ZZZZ (e.g. 31.11+0001)",
            file=sys.stderr
        )
        sys.exit(1)

if __name__ == "__main__":
    main()

