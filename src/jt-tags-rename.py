import os
import sys
import json
import re
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_AC     = re.compile(r"^[0-9]{2}$")
RE_ID     = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
RE_EXT    = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")


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
  if len(sys.argv) != 3:
    print(
      "Usage: jt tags rename <AC | AC.ID | AC.ID+EXT> <new-name>",
      file=sys.stderr
    )
    sys.exit(1)

  fragment = sys.argv[1].strip()
  new_name = sys.argv[2].strip()
  data = load_db()

  if RE_AC.match(fragment):
    ac_id = fragment
    if ac_id not in data["ac"]:
      print(f"Error: AC '{ac_id}' does not exist.", file=sys.stderr)
      sys.exit(1)
    data["ac"][ac_id]["name"] = new_name
    save_db(data)
    print(f"{jtconf.CONFIG['color_ac']}{jtconf.CONFIG['icon_tag']} [{ac_id}] {new_name}{jtconf.CONFIG['color_reset']}")
    return

  if RE_ID.match(fragment):
    id_tag = fragment
    if id_tag not in data["id"]:
      print(f"Error: ID '{id_tag}' does not exist.", file=sys.stderr)
      sys.exit(1)
    data["id"][id_tag]["name"] = new_name
    save_db(data)
    print(f"{jtconf.CONFIG['color_id']}{jtconf.CONFIG['icon_tag']} [{id_tag}] {new_name}{jtconf.CONFIG['color_reset']}")
    return

  if RE_EXT.match(fragment):
    ext_tag = fragment
    if ext_tag not in data["ext"]:
      print(f"Error: EXT '{ext_tag}' does not exist.", file=sys.stderr)
      sys.exit(1)
    data["ext"][ext_tag]["name"] = new_name
    save_db(data)

    ext_info = data["ext"][ext_tag]
    dirs = ext_info.get("dirs", [])
    if dirs:
      for dir_id in dirs:
        print(
          f"{jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id} {jtconf.CONFIG['color_ext']}\u2190{jtconf.CONFIG['color_reset']} "
          f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{ext_tag}] {new_name}{jtconf.CONFIG['color_reset']}"
        )
    else:
      print(f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{ext_tag}] {new_name}{jtconf.CONFIG['color_reset']}")
    return

  print(
    "Error: fragment must be one of:\n"
    "  \u2022 AC      \u2192 two digits (e.g. 01)\n"
    "  \u2022 AC.ID   \u2192 XX.YY (e.g. 01.02)\n"
    "  \u2022 AC.ID+EXT \u2192 XX.YY+ZZZZ (e.g. 01.02+0001)",
    file=sys.stderr
  )
  sys.exit(1)

if __name__ == "__main__":
  main()

