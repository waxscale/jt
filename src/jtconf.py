import os

EXAMPLE_CONF = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples", "jt.conf")
CONF_PATH = os.path.expanduser("~/.config/jdex/jt.conf")


def parse_config(path):
  cfg = {}
  try:
    with open(path, "r") as f:
      for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
          continue
        if "=" in line:
          k, v = line.split("=", 1)
          cfg[k.strip()] = bytes(v.strip(), "utf-8").decode("unicode_escape")
  except FileNotFoundError:
    pass
  return cfg


DEFAULTS = parse_config(EXAMPLE_CONF)


def load_config():
  cfg = DEFAULTS.copy()
  cfg.update(parse_config(CONF_PATH))
  return cfg


CONFIG = load_config()
