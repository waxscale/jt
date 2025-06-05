import os
import sys
import json
import re
import subprocess
import jtconf

DB_PATH = os.path.expanduser("~/.cache/jdex/jt.json")

RE_DIR_ID  = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")
RE_EXT     = re.compile(r"^[0-9]{2}\.[0-9]{2}\+[0-9]{4}$")

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

def build_choices_for_dir(data, dir_id):
  choices = []
  for ext_tag in data["dir"].get(dir_id, {}).get("ext", []):
    ext_info = data["ext"].get(ext_tag, {})
    name = ext_info.get("name", "")
    choices.append(f"[{ext_tag}] {name}")
  return sorted(choices)

def run_fzf(choices):
  try:
    p = subprocess.Popen(
      ["fzf", "--ansi", "--prompt=Select EXT to remove: "],
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

def main():
  cwd = os.getcwd()
  vault_prefix = jtconf.CONFIG['vault'] + os.sep
  if not cwd.startswith(vault_prefix):
    print(
      f"Error: Not inside vault directory ({jtconf.CONFIG['vault']}).",
      file=sys.stderr,
    )
    sys.exit(1)

  dir_id = cwd[len(vault_prefix):]
  if not RE_DIR_ID.match(dir_id):
    print(
      f"Error: Current directory '{cwd}' is not in 'vault/0000_0000_0000_0000' format.",
      file=sys.stderr
    )
    sys.exit(1)

  data = load_db()

  choices = build_choices_for_dir(data, dir_id)
  if not choices:
    print(f"No EXT tags refer to this directory ({dir_id}).")
    sys.exit(0)

  selection = run_fzf(choices)
  if not selection:
    sys.exit(0)

  token = extract_token(selection)
  if not token or token not in data["ext"]:
    print("Error: could not parse selection or EXT not found.", file=sys.stderr)
    sys.exit(1)

  ext_info = data["ext"][token]
  dirs_list = ext_info.get("dirs", [])
  if dir_id in dirs_list:
    dirs_list.remove(dir_id)

  data["dir"][dir_id]["ext"] = [
    e for e in data["dir"][dir_id]["ext"] if e != token
  ]

  save_db(data)

  name = ext_info.get("name", "")
  dir_name = data.get("dir", {}).get(dir_id, {}).get("name", "")
  print(
    f"{jtconf.CONFIG['color_ext']}{jtconf.CONFIG['icon_tag']} [{token}] {name} removed from "
    f"{jtconf.CONFIG['color_dir']}{jtconf.CONFIG['icon_dir']} {dir_id} {dir_name}{jtconf.CONFIG['color_reset']}"
  )
  sys.exit(0)

if __name__ == "__main__":
  main()

