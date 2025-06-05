import os
import sys
import json
import re

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

COLOR_RESET = "\033[0m"
COLOR_AC    = "\033[38;5;75m"
COLOR_ID    = "\033[38;5;107m"
COLOR_EXT   = "\033[38;5;175m"

ICON_TAG = "\uf02b"

RE_AC  = re.compile(r"^[0-9]{2}$")
RE_ID  = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
RE_EXT = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")

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

def save_db(data):
  with open(DB_PATH, "w") as f:
    json.dump(data, f, indent=2)

def add_ac(ac_id, name):
  data = load_db()
  if ac_id in data["ac"]:
    print(f"Error: AC '{ac_id}' already exists.", file=sys.stderr)
    sys.exit(1)
  data["ac"][ac_id] = {"name": name}
  save_db(data)
  print(f"{COLOR_AC}{ICON_TAG} [{ac_id}] {name}{COLOR_RESET}")

def add_id(id_tag, name):
  data = load_db()
  ac_id = id_tag.split(".")[0]
  if ac_id not in data["ac"]:
    print(f"Error: Parent AC '{ac_id}' does not exist.", file=sys.stderr)
    sys.exit(1)
  if id_tag in data["id"]:
    print(f"Error: ID '{id_tag}' already exists.", file=sys.stderr)
    sys.exit(1)
  data["id"][id_tag] = {"name": name}
  save_db(data)
  print(f"{COLOR_ID}{ICON_TAG} [{id_tag}] {name}{COLOR_RESET}")

def add_ext(ext_tag, name):
  data = load_db()
  id_part = ext_tag.split("+")[0]
  if id_part not in data["id"]:
    print(f"Error: Parent ID '{id_part}' does not exist.", file=sys.stderr)
    sys.exit(1)
  if ext_tag in data["ext"]:
    print(f"Error: EXT '{ext_tag}' already exists.", file=sys.stderr)
    sys.exit(1)
  data["ext"][ext_tag] = {"name": name}
  save_db(data)
  print(f"{COLOR_EXT}{ICON_TAG} [{ext_tag}] {name}{COLOR_RESET}")

def main():
  argv = sys.argv
  argc = len(argv)

  if argc != 3:
    print(
      "Usage:\n"
      "  jt tags add <AC> <name>\n"
      "  jt tags add <AC.ID> <name>\n"
      "  jt tags add <AC.ID+EXT> <name>\n",
      file=sys.stderr
    )
    sys.exit(1)

  token = argv[1].strip()
  name  = argv[2].strip()

  if RE_AC.match(token):
    add_ac(token, name)
    sys.exit(0)
  elif RE_ID.match(token):
    add_id(token, name)
    sys.exit(0)
  elif RE_EXT.match(token):
    add_ext(token, name)
    sys.exit(0)
  else:
    print(
      "Error: Invalid tag format. Must be one of:\n"
      "  \u2022 AC        \u2192 two digits (e.g. 31)\n"
      "  \u2022 AC.ID     \u2192 XX.YY (e.g. 31.11)\n"
      "  \u2022 AC.ID+EXT \u2192 XX.YY+ZZZZ (e.g. 31.11+0001)",
      file=sys.stderr
    )
    sys.exit(1)

if __name__ == "__main__":
  main()

