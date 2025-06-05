import os
import sys
import json
import re
import subprocess
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")
RE_ID      = re.compile(r"^[0-9]{2}\.[0-9]{2}$")
RE_EXT     = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")
RE_EXT_TAG = re.compile(r"^([0-9]{2}\.[0-9]{2})\+([0-9]{4})$")

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

def build_choices(data):
  choices = []
  for id_tag, info in data["id"].items():
    name = info.get("name", "")
    choices.append(f"[{id_tag}] {name}")
  for ext_tag, ext_info in data["ext"].items():
    name = ext_info.get("name", "")
    choices.append(f"[{ext_tag}] {name}")
  return sorted(choices)

def run_fzf(choices):
  try:
    p = subprocess.Popen(
      ["fzf", "--ansi", "--prompt=Select tag: "],
      stdin=subprocess.PIPE,
      stdout=subprocess.PIPE,
      stderr=subprocess.PIPE,
      text=True
    )
  except FileNotFoundError:
    print("Error: fzf not found. Please install fzf.", file=sys.stderr)
    sys.exit(1)

  stdout, _ = p.communicate("\n".join(choices))
  if p.returncode != 0:
    return None
  return stdout.strip()

def extract_token(line):
  if not line.startswith("["):
    return None
  end = line.find("]")
  if end == -1:
    return None
  return line[1:end]

def next_ext_for_id(id_tag, data):
  max_num = 0
  prefix = id_tag + "+"
  for ext_tag in data["ext"].keys():
    if ext_tag.startswith(prefix):
      m = RE_EXT_TAG.match(ext_tag)
      if m:
        num = int(m.group(2))
        if num > max_num:
          max_num = num
  new_num = max_num + 1
  return f"{id_tag}+{new_num:04d}"

def main():
  cwd = os.getcwd()
  vault_prefix = jtconf.CONFIG['vault'] + os.sep
  if not cwd.startswith(vault_prefix):
    print(f"Error: Not inside vault directory ({jtconf.CONFIG['vault']}).", file=sys.stderr)
    sys.exit(1)

  dir_id = cwd[len(vault_prefix):]
  if not RE_DIR_ID.match(dir_id):
    print(
      f"Error: Current directory '{cwd}' is not in 'vault/0000_0000_0000_0000' format.",
      file=sys.stderr
    )
    sys.exit(1)

  data = load_db()
  choices = build_choices(data)
  if not choices:
    print("No ID or EXT tags available.", file=sys.stderr)
    sys.exit(1)

  selection = run_fzf(choices)
  if not selection:
    sys.exit(0)

  token = extract_token(selection)
  if not token:
    print("Error: could not parse selection.", file=sys.stderr)
    sys.exit(1)

  if RE_EXT.match(token):
    ext_info = data["ext"].get(token)
    if ext_info is None:
      print(f"Error: EXT '{token}' not found.", file=sys.stderr)
      sys.exit(1)

    old_dirs = ext_info.get("dirs", [])
    for old_dir in list(old_dirs):
      if old_dir == dir_id:
        print(f"EXT '{token}' already assigned to {dir_id}.", file=sys.stderr)
        sys.exit(0)

    ext_info.setdefault("dirs", []).append(dir_id)

    if dir_id not in data["dir"]:
      data["dir"][dir_id] = {"ext": [], "name": data["dir"].get(dir_id, {}).get("name", "")}
    if token not in data["dir"][dir_id]["ext"]:
      data["dir"][dir_id]["ext"].append(token)

    save_db(data)
    name = ext_info.get("name", "")
    dir_name = data["dir"][dir_id].get("name", "")
    print(
      f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{token}] {name} "
      f"\u2192 {jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id} {dir_name}{jtconf.CONFIG['color_reset']}"
    )
    sys.exit(0)

  if RE_ID.match(token):
    id_tag = token
    if id_tag not in data["id"]:
      print(f"Error: ID '{id_tag}' not found.", file=sys.stderr)
      sys.exit(1)
    new_ext = next_ext_for_id(id_tag, data)

    try:
      proc = subprocess.run(
        ["gum", "input", "--placeholder", "Name (optional)"],
        stdin=sys.stdin,
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        text=True
      )
      name = proc.stdout.strip()
    except FileNotFoundError:
      name = ""

    data["ext"][new_ext] = {"name": name, "dirs": [dir_id]}

    if dir_id not in data["dir"]:
      data["dir"][dir_id] = {"ext": [], "name": data["dir"].get(dir_id, {}).get("name", "")}
    data["dir"][dir_id]["ext"].append(new_ext)

    save_db(data)
    display_name = name if name else "(no name)"
    dir_name = data["dir"][dir_id].get("name", "")
    print(
      f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{new_ext}] {display_name} "
      f"\u2192 {jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id} {dir_name}{jtconf.CONFIG['color_reset']}"
    )
    sys.exit(0)

  print(f"Error: '{token}' is not a valid ID or EXT.", file=sys.stderr)
  sys.exit(1)

if __name__ == "__main__":
  main()

