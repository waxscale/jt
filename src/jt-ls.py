import os
import sys
import json
import re

DB_PATH   = os.path.expanduser("~/.cache/jdex/jt.json")
CONF_PATH = os.path.expanduser("~/.config/jdex/jt.conf")
DEFAULT_VAULT = "/mnt/nas"

# ANSI colors (TokyoNight Dark)
COLOR_AC    = "\033[38;5;75m"   # blue-ish for AC labels
COLOR_ID    = "\033[38;5;107m"  # green-ish for ID names in parentheses
COLOR_EXT   = "\033[38;5;175m"  # pink-ish for EXT entries
COLOR_DIR   = "\033[38;5;141m"  # purple-ish for folder line
COLOR_RESET = "\033[0m"

# Nerd Font icons (FiraCode Nerd Font)
ICON_TAG = "\uf02b"   # \uf02b
ICON_DIR = "\uf07b"   # \uf73b

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")
RE_EXT_TAG = re.compile(r"^([0-9]{2})\.([0-9]{2})\+([0-9]{4})$")

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

def main():
  args = sys.argv[1:]
  show_all = False
  if args and args[0] in ("-a", "--all"):
    show_all = True
    args = args[1:]
  if args:
    print("Usage: jt-ls [-a|--all]", file=sys.stderr)
    sys.exit(1)

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
  dir_entry = data["dir"].get(dir_id, {})
  dir_name  = dir_entry.get("name", "")

  # Print folder line
  if dir_name:
    print(f"{COLOR_DIR}{ICON_DIR} {dir_name}{COLOR_RESET}")
  else:
    print(f"{COLOR_DIR}{ICON_DIR} {dir_id}{COLOR_RESET}")

  # Collect EXT tags for this dir (check membership in "dirs" list)
  ext_tags = [
    ext_tag
    for ext_tag, ext_info in data["ext"].items()
    if dir_id in ext_info.get("dirs", [])
  ]

  # Group EXT by AC
  group_map = {}
  for ext in ext_tags:
    m = RE_EXT_TAG.match(ext)
    if not m:
      continue
    ac_id = m.group(1)
    group_map.setdefault(ac_id, []).append(ext)

  # Determine AC keys to display
  ac_keys = sorted(data["ac"].keys()) if show_all else sorted(group_map.keys())

  for ac_id in ac_keys:
    ac_name = data["ac"].get(ac_id, {}).get("name", "(unknown)")
    indent = "  "
    ext_list = group_map.get(ac_id, [])

    if ext_list:
      entries = []
      for ext_tag in sorted(ext_list):
        ext_info = data["ext"][ext_tag]
        ext_name = ext_info.get("name", "")
        id_part  = ext_tag.rsplit("+", 1)[0]
        id_name  = data["id"].get(id_part, {}).get("name", "")

        if show_all:
          if ext_name:
            entries.append(f"{COLOR_EXT}{ICON_TAG} [{ext_tag}] {ext_name}{COLOR_RESET}")
          else:
            entries.append(f"{COLOR_EXT}{ICON_TAG} [{ext_tag}]{COLOR_RESET}")
        else:
          if ext_name and id_name:
            entries.append(
              f"{COLOR_EXT}{ICON_TAG} {ext_name} {COLOR_ID}({id_name}){COLOR_RESET}"
            )
          elif ext_name and not id_name:
            entries.append(
              f"{COLOR_EXT}{ICON_TAG} {ext_tag} {COLOR_ID}({id_part}){COLOR_RESET}"
            )
          elif not ext_name and id_name:
            entries.append(
              f"{COLOR_EXT}{ICON_TAG} {COLOR_ID}({id_name}){COLOR_RESET}"
            )
          else:
            entries.append(
              f"{COLOR_EXT}{ICON_TAG} {ext_tag} {COLOR_ID}({id_part}){COLOR_RESET}"
            )

      joined = " ".join(entries)
      print(f"{indent}{COLOR_AC}{ac_name}:{COLOR_RESET} {joined}")
    else:
      if show_all:
        print(f"{indent}{COLOR_AC}{ac_name}:{COLOR_RESET} -")

if __name__ == "__main__":
  main()

