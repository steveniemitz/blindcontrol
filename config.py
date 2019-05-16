import json
import os

if os.path.exists('config.json'):
  with open('config.json') as fp:
    CONFIG = json.load(fp)
else:
  with open('config.example.json') as fp:
    CONFIG = json.load(fp)
