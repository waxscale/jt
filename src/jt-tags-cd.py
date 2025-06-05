import os
import sys
import json
import re
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_EXT = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")

def main():
  if len(sys.argv) != 2:
    print("Usage: jt tags cd <AC.ID+EXT>", file=sys.stderr)
    sys.exit(1)

  token = sys.argv[1].strip()
  if not RE_EXT.match(token):
    print("Error: EXT token must be in format XX.YY+ZZZZ", file=sys.stderr)
    sys.exit(1)

  if not os.path.isfile(DB_PATH):
    print(f"Error: Database not found at {DB_PATH}", file=sys.stderr)
    sys.exit(1)

  with open(DB_PATH, "r") as f:
    try:
      data = json.load(f)
    except json.JSONDecodeError:
      data = {}

  ext_info = data.get("ext", {}).get(token)
  if not ext_info:
    print(f"Error: EXT '{token}' not found in database.", file=sys.stderr)
    sys.exit(1)

  dir_id = None
  if isinstance(ext_info, dict):
    if "dir" in ext_info:
      dir_id = ext_info.get("dir")
    else:
      dirs = ext_info.get("dirs", [])
      if len(dirs) == 1:
        dir_id = dirs[0]
      elif dirs:
        dir_id = dirs[0]
  if not dir_id:
    print(f"Error: EXT '{token}' has no directory associated.", file=sys.stderr)
    sys.exit(1)

  vault = jtconf.CONFIG['vault']
  print(os.path.join(vault, dir_id))

if __name__ == "__main__":
  main()
