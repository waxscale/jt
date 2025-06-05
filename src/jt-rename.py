import os
import sys
import json
import re
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_DIR_ID = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")

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

def main():
  if len(sys.argv) != 2:
    print(
      f"{jtconf.CONFIG['color_err']}Usage: jt-rename <NEW_DIR_NAME>{jtconf.CONFIG['color_reset']}",
      file=sys.stderr,
    )
    sys.exit(1)

  new_name = sys.argv[1].strip()

  vault = jtconf.CONFIG['vault']
  cwd = os.getcwd()
  vault_prefix = vault + os.sep
  if not cwd.startswith(vault_prefix):
    print(
      f"{jtconf.CONFIG['color_err']}Error: Not inside vault ({vault}).{jtconf.CONFIG['color_reset']}",
      file=sys.stderr,
    )
    sys.exit(1)

  dir_id = cwd[len(vault_prefix):]
  if not RE_DIR_ID.match(dir_id):
    print(
      f"{jtconf.CONFIG['color_err']}Error: Current directory '{cwd}' is not in 'vault/XXXX_XXXX_XXXX_XXXX' format.{jtconf.CONFIG['color_reset']}",
      file=sys.stderr
    )
    sys.exit(1)

  data = load_db()

  if dir_id not in data["dir"]:
    data["dir"][dir_id] = {"name": new_name, "ext": []}
    dir_entry = data["dir"][dir_id]
    old_name = ""
  else:
    dir_entry = data["dir"][dir_id]
    old_name = dir_entry.get("name", "")
    dir_entry["name"] = new_name

  save_db(data)

  display_old = old_name if old_name else dir_id
  display_new = new_name if new_name else dir_id

  print(
    f"{jtconf.CONFIG['color_ok']}{jtconf.CONFIG['icon_dir']} Renamed dir '{display_old}' \u2192 '{display_new}'{jtconf.CONFIG['color_reset']}"
  )

if __name__ == "__main__":
  main()

