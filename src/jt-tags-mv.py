import os
import sys
import json
import re
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_AC  = re.compile(r"^[0-9]{2}$")
RE_ID  = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
RE_EXT = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")
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

def mv_ac(old_ac, new_ac, data):
  if new_ac in data["ac"]:
    print(f"Error: AC '{new_ac}' already exists.", file=sys.stderr)
    sys.exit(1)

  ac_name = data["ac"][old_ac]["name"]
  data["ac"][new_ac] = {"name": ac_name}
  del data["ac"][old_ac]

  id_map = {}
  for id_tag in list(data["id"].keys()):
    if id_tag.startswith(f"{old_ac}."):
      suffix = id_tag[len(old_ac):]
      new_id = new_ac + suffix
      id_map[id_tag] = new_id

  ext_map = {}
  for ext_tag in list(data["ext"].keys()):
    if ext_tag.startswith(f"{old_ac}."):
      suffix = ext_tag[len(old_ac):]
      new_ext = new_ac + suffix
      ext_map[ext_tag] = new_ext

  for old_id, new_id in id_map.items():
    data["id"][new_id] = data["id"][old_id]
    del data["id"][old_id]

  for old_ext, new_ext in ext_map.items():
    data["ext"][new_ext] = data["ext"][old_ext]
    del data["ext"][old_ext]

  for dir_id, dir_entry in data["dir"].items():
    updated = []
    for e in dir_entry.get("ext", []):
      updated.append(ext_map.get(e, e))
    dir_entry["ext"] = updated

  save_db(data)
  print(f"{jtconf.CONFIG['color_ac']}{jtconf.CONFIG['icon_tag']} [{new_ac}] {ac_name}{jtconf.CONFIG['color_reset']}")

def mv_id(old_id, new_id, data):
  old_ac = old_id.split(".")[0]
  new_ac = new_id.split(".")[0]
  if old_ac != new_ac:
    print("Error: AC prefix must match when renaming ID.", file=sys.stderr)
    sys.exit(1)
  if new_id in data["id"]:
    print(f"Error: ID '{new_id}' already exists.", file=sys.stderr)
    sys.exit(1)

  id_name = data["id"][old_id]["name"]
  data["id"][new_id] = {"name": id_name}
  del data["id"][old_id]

  ext_map = {}
  for ext_tag in list(data["ext"].keys()):
    if ext_tag.startswith(f"{old_id}+"):
      suffix = ext_tag[len(old_id):]
      new_ext = new_id + suffix
      ext_map[ext_tag] = new_ext

  for old_ext, new_ext in ext_map.items():
    data["ext"][new_ext] = data["ext"][old_ext]
    del data["ext"][old_ext]

  for dir_id, dir_entry in data["dir"].items():
    updated = []
    for e in dir_entry.get("ext", []):
      updated.append(ext_map.get(e, e))
    dir_entry["ext"] = updated

  save_db(data)
  print(f"{jtconf.CONFIG['color_id']}{jtconf.CONFIG['icon_tag']} [{new_id}] {id_name}{jtconf.CONFIG['color_reset']}")

def mv_ext(old_ext, new_ext, data):
  old_id = old_ext.split("+")[0]
  new_id = new_ext.split("+")[0]
  if old_id != new_id:
    print("Error: ID prefix must match when renaming EXT.", file=sys.stderr)
    sys.exit(1)
  if new_ext in data["ext"]:
    print(f"Error: EXT '{new_ext}' already exists.", file=sys.stderr)
    sys.exit(1)

  ext_info = data["ext"][old_ext]
  data["ext"][new_ext] = ext_info
  del data["ext"][old_ext]

  for dir_id in ext_info.get("dirs", []):
    exts = data["dir"].get(dir_id, {}).get("ext", [])
    data["dir"][dir_id]["ext"] = [new_ext if e == old_ext else e for e in exts]

  save_db(data)
  name = ext_info.get("name", "")
  dirs = ext_info.get("dirs", [])
  if dirs:
    for dir_id in dirs:
      print(
        f"{jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id} {jtconf.CONFIG['color_ext']}\u2190{jtconf.CONFIG['color_reset']} "
        f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{new_ext}] {name}{jtconf.CONFIG['color_reset']}"
      )
  else:
    print(f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{new_ext}] {name}{jtconf.CONFIG['color_reset']}")

def main():
  if len(sys.argv) != 3:
    print(
      "Usage: jt tags mv <old-fragment> <new-fragment>",
      file=sys.stderr
    )
    sys.exit(1)

  old_frag = sys.argv[1].strip()
  new_frag = sys.argv[2].strip()
  data = load_db()

  if RE_AC.match(old_frag) and RE_AC.match(new_frag):
    if old_frag not in data["ac"]:
      print(f"Error: AC '{old_frag}' does not exist.", file=sys.stderr)
      sys.exit(1)
    mv_ac(old_frag, new_frag, data)
    return

  if RE_ID.match(old_frag) and RE_ID.match(new_frag):
    if old_frag not in data["id"]:
      print(f"Error: ID '{old_frag}' does not exist.", file=sys.stderr)
      sys.exit(1)
    mv_id(old_frag, new_frag, data)
    return

  if RE_EXT.match(old_frag) and RE_EXT.match(new_frag):
    if old_frag not in data["ext"]:
      print(f"Error: EXT '{old_frag}' does not exist.", file=sys.stderr)
      sys.exit(1)
    mv_ext(old_frag, new_frag, data)
    return

  print(
    "Error: Both fragments must be the same level:\n"
    "  \u2022 AC      \u2192 two digits   (e.g. 01 \u2192 02)\n"
    "  \u2022 AC.ID   \u2192 XX.YY        (e.g. 01.01 \u2192 01.02)\n"
    "  \u2022 AC.ID+E \u2192 XX.YY+ZZZZ   (e.g. 01.01+0001 \u2192 01.01+0002)",
    file=sys.stderr
  )
  sys.exit(1)

if __name__ == "__main__":
  main()

