import os
import sys
import json
import re
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")
RE_EXT_TAG = re.compile(r"^([0-9]{2})\.([0-9]{2})\+([0-9]{4})$")

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

  vault = jtconf.CONFIG['vault']
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

  if dir_name:
    print(
      f"{jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_name}{jtconf.CONFIG['color_reset']}"
    )
  else:
    print(
      f"{jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id}{jtconf.CONFIG['color_reset']}"
    )

  ext_tags = [
    ext_tag
    for ext_tag, ext_info in data["ext"].items()
    if dir_id in ext_info.get("dirs", [])
  ]

  group_map = {}
  for ext in ext_tags:
    m = RE_EXT_TAG.match(ext)
    if not m:
      continue
    ac_id = m.group(1)
    group_map.setdefault(ac_id, []).append(ext)

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
            entries.append(f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{ext_tag}] {ext_name}{jtconf.CONFIG['color_reset']}")
          else:
            entries.append(f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{ext_tag}]{jtconf.CONFIG['color_reset']}")
        else:
          if ext_name and id_name:
            entries.append(
              f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} {ext_name} {jtconf.CONFIG['color_id']}({id_name}){jtconf.CONFIG['color_reset']}"
            )
          elif ext_name and not id_name:
            entries.append(
              f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} {ext_tag} {jtconf.CONFIG['color_id']}({id_part}){jtconf.CONFIG['color_reset']}"
            )
          elif not ext_name and id_name:
            entries.append(
              f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} {jtconf.CONFIG['color_id']}({id_name}){jtconf.CONFIG['color_reset']}"
            )
          else:
            entries.append(
              f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} {ext_tag} {jtconf.CONFIG['color_id']}({id_part}){jtconf.CONFIG['color_reset']}"
            )

      joined = " ".join(entries)
      print(f"{indent}{jtconf.CONFIG['color_ac']}{ac_name}:{jtconf.CONFIG['color_reset']} {joined}")
    else:
      if show_all:
        print(f"{indent}{jtconf.CONFIG['color_ac']}{ac_name}:{jtconf.CONFIG['color_reset']} -")

if __name__ == "__main__":
  main()

