import os
import sys
import json
import re
import subprocess

CONF_PATH = os.path.expanduser("~/.config/jdex/jt.conf")
DB_PATH   = os.path.expanduser("~/.cache/jdex/jt.json")
DEFAULT_VAULT = "/mnt/nas"

RE_DIR_ID = re.compile(r"^[0-9]{4}(?:_[0-9]{4}){3}$")

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

def prompt_name():
  try:
    proc = subprocess.run(
      ["gum", "input", "--placeholder", "Name"],
      stdin=sys.stdin,
      stdout=subprocess.PIPE,
      stderr=sys.stderr,
      text=True
    )
    return proc.stdout.strip()
  except FileNotFoundError:
    return ""

def format_dir_id(num):
  s = f"{num:016d}"
  return "_".join(s[i:i+4] for i in range(0, 16, 4))

def main():
  vault = load_vault_path()
  cwd = os.getcwd()

  if os.path.normpath(cwd) != os.path.normpath(vault):
    print(f"Error: jt append must be run in vault base ({vault}).", file=sys.stderr)
    sys.exit(1)

  existing = [
    name for name in os.listdir(vault)
    if os.path.isdir(os.path.join(vault, name)) and RE_DIR_ID.match(name)
  ]

  if existing:
    nums = [int(name.replace("_", "")) for name in existing]
    new_num = max(nums) + 1
  else:
    new_num = 0

  new_dir_id = format_dir_id(new_num)
  new_path = os.path.join(vault, new_dir_id)

  name = prompt_name()

  try:
    os.makedirs(new_path, exist_ok=False)
  except Exception as e:
    print(f"Error creating directory '{new_dir_id}': {e}", file=sys.stderr)
    sys.exit(1)

  data = load_db()
  data["dir"][new_dir_id] = {"name": name, "ext": []}
  save_db(data)

  print(f"Created directory {new_dir_id} with name '{name}'")

if __name__ == "__main__":
  main()

