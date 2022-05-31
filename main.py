import os
import xml.etree.ElementTree as ET
from xml.dom.minidom import parse, parseString
from svgpathtools import svg2paths
import xmltodict
import re

import glob


def path_geom(geom: str):
    pass


def getFiles(path: str, ext="svg"):
    return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)


def getDict(path: str):
    with open(path, "r") as file:
        file = file.read()
    # return xmltodict.parse(file)

    start = 0
    xaml = []
    end = False
    for match in re.finditer(">", file):
        line = file[start:match.end()]
        if "\n" in line:
            line = line.replace("\n", "")
        if "?" in line or "<!--" in line:
            xaml.append(line)
            start = match.end()
            continue
        # line = line.split(" ")

        start = match.end()

    return "\n".join(xaml)


if __name__ == '__main__':
    print(getFiles(path="test"))

    for file in getFiles(path="test"):
        truc = getDict(path=file)

        directory, name = os.path.split(file)
        name = f'{name.split(".")[0]}_tmp'

        with open(f"{directory}/{name}.xaml", "w") as output:
            output.write(truc)

    print(truc)
