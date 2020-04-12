import argparse
import os
import re
import sys
import tempfile

import colorsys
from PIL import ImageColor

import json
import zipfile

import appex
import console


class Swatch:
  def __init__(self, jsonData=None):
    self.jsonData = jsonData or {
      'hue': 0.0,
      'saturation': 0.0,
      'brightness': 0.0,
      'alpha': 1,
      'colorSpace': 0
    }

  def __str__(self):
    return str(self.jsonData)

  @property
  def hsv(self):
    return (
      self.jsonData['hue'], self.jsonData['saturation'],
      self.jsonData['brightness']
    )

  @hsv.setter
  def hsv(self, value):
    self.jsonData['hue'] = value[0]
    self.jsonData['saturation'] = value[1]
    self.jsonData['brightness'] = value[2]

  @classmethod
  def from_rgb(cls, value):
    instance = cls()
    instance.hsv = colorsys.rgb_to_hsv(*map(lambda v: v / 255, value))
    return instance

  @classmethod
  def from_hex(cls, value):
    if not value.startswith('#'):
      value = '#' + value
    rgb = ImageColor.getcolor(value, 'RGB')
    return cls.from_rgb(rgb)


class Palette:
  max_rows = 3
  row_size = 10
  max_length = max_rows * row_size
  json_file_name = 'Swatches.json'
  json_key_name = 'name'
  json_key_swatches = 'swatches'
  hex_regex = re.compile('(?P<value>#?[A-Fa-f0-9]{2,6})')

  def __init__(self, jsonData=None):
    self.jsonData = jsonData or {
      self.json_key_name: 'Untitled Palette',
      self.json_key_swatches: [None] * self.max_length
    }
    self.jsonSwatches = self.jsonData[self.json_key_swatches]

  def __len__(self):
    return len(self.jsonSwatches)

  def __getitem__(self, index):
    return Swatch(self.jsonSwatches[index])

  def __setitem__(self, index, value):
    self.jsonSwatches[index] = value and value.jsonData

  def __str__(self):
    return str(self.jsonData)

  @property
  def name(self):
    return self.jsonData[self.json_key_name]

  @name.setter
  def name(self, value):
    self.jsonData[self.json_key_name] = value

  def save(self, file):
    jsonString = json.dumps(self.jsonData)
    with zipfile.ZipFile(file, 'w') as zip:
      zip.writestr(self.json_file_name, jsonString)

  @classmethod
  def from_file(cls, file):
    with zipfile.ZipFile(file, 'r').open(cls.json_file_name) as jsonFile:
      jsonData = json.loads(jsonFile)
      return cls(jsonData)

  @classmethod
  def from_string(cls, value):
    instance = cls()
    lines = value.splitlines()
    for x in range(min(len(lines), cls.max_rows)):
      row = cls.hex_regex.findall(lines[x])
      for y in range(min(len(row), cls.row_size)):
        instance[x * cls.row_size + y] = Swatch.from_hex(row[y])
    return instance


def main():
  palette = None
  paletteFile = None
  paletteString = None

  parser = argparse.ArgumentParser()
  parser.add_argument(
    'command', choices=['create', 'view'], nargs='?', default='view'
  )
  args = parser.parse_args()

  if appex.is_running_extension():
    paletteFile = appex.get_file_path()
    paletteString = appex.get_text()

  command = args.command
  if command == 'create':
    palette = Palette.from_string(paletteString)
    path = os.path.join(tempfile.gettempdir(), palette.name + '.swatches')
    palette.save(path)
    console.open_in(path)
  elif command == 'view':
    palette = paletteFile and Palette.from_file(paletteFile) or Palette()
    print(palette)
  else:
    print('Unknown command: ' + command)


if __name__ == "__main__":
  main()

