import os
import json
import re
import sys
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")

ID_TAG     = "01.01"

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
  data = load_db()

  ext_tags = sorted(
    [ext for ext in data["ext"].keys() if ext.startswith(f"{ID_TAG}+")]
  )
  if not ext_tags:
    sys.exit(0)

  for ext_tag in ext_tags:
    ext_info = data["ext"][ext_tag]
    ext_name = ext_info.get("name", "")
    print(
      f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{ext_tag}] {ext_name}{jtconf.CONFIG['color_reset']}"
    )

    dirs_with_ext = ext_info.get("dirs", [])
    first_five = dirs_with_ext[:5]

    for dir_id in first_five:
      if RE_DIR_ID.match(dir_id):
        dir_name = data["dir"].get(dir_id, {}).get("name", "")
        print(
          f"  {jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} [{dir_id}] {dir_name}{jtconf.CONFIG['color_reset']}"
        )

    total = len(dirs_with_ext)
    if total > 5:
      print("  +more")
    else:
      for _ in range(5 - len(first_five)):
        print("  -")
      print("  -")

if __name__ == "__main__":
  main()

