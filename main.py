import os
import re

import glob

from collections import defaultdict


def getGeom(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    match geom:
        case "<path":
            line, name, tab = getPath(line=line, name=name, tab=tab, fill=fill, geom=geom)
        case "<rect":
            line, name, tab = getRect(line=line, name=name, tab=tab, fill=fill, geom=geom)
        case "<polygon":
            line, name, tab = getPolygon(line=line, name=name, tab=tab, fill=fill, geom=geom)

    return line, name, tab


def getName(line: str, name: defaultdict, geom: str, fill: defaultdict):
    line = line.replace(f"{geom}", "").replace("/>", "").strip()
    line = line.split('" ')
    tmp = {}
    for row in line:
        if "style" in row:
            row = row.replace('"', '').split("=")
            row = f".st{name['st']}{{{row[1]}}}"

            fill = getStyle(row)

            row = f"class=\"st{name['st']}\""

            name["st"] += 1
        row = row.replace('"', "")
        row = row.split("=")
        tmp[row[0]] = f'"{row[1]}"'

    name[geom] += 1

    return tmp, name, fill


def getPath(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getName(line=line, name=name, geom=geom, fill=fill)

    prefixe = "".join(["\t"] * tab)

    line = f"{prefixe}<Path xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" Name=\"Path{name['path']}\" Fill={fill[tmp['class']]} Data={tmp['d']}/>"

    return line, name, tab


def getRect(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getName(line=line, name=name, geom=geom, fill=fill)
    prefixe = "".join(["\t"] * tab)

    try:
        line = f"{prefixe}<Rectangle xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" Canvas.Left={tmp['x']} Canvas.Top={tmp['y']} Width={tmp['width']} Height={tmp['height']} Name=\"Rect{name['rect']}\" Fill={fill[tmp['class']]}/>"
    except KeyError:
        line = f"{prefixe}<Rectangle xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" Width={tmp['width']} Height={tmp['height']} Name=\"Rect{name['rect']}\" Fill={fill[tmp['class']]}/>"

    return line, name, tab


def getPolygon(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getName(line=line, name=name, geom=geom, fill=fill)
    prefixe = "".join(["\t"] * tab)

    line = f"{prefixe}<Polygon xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" Points={tmp['points']} Name=\"Polygon{name['polygon']}\" FillRule=\"NonZero\" Fill={fill[tmp['class']]}/>"

    return line, name, tab


def getTextBlock(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):
    tmp, name, fill = getName(line=line, name=name, geom=geom, fill=fill)
    prefixe = "".join(["\t"] * tab)


def getFiles(path: str, ext="svg"):
    return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)


def getParams(line: str, name: defaultdict):
    line = line.replace("<svg ", "").replace(">", "")
    line = line.replace("\" ", "\"||")
    line = line.split("||")

    tmp = {}
    for row in line:
        row = row.split("=")
        tmp[row[0]] = row[1]
    tmp["viewBox"] = tmp["viewBox"].replace('"', '').split(" ")
    tmp["viewBox"] = [f'"{item}"' for item in tmp["viewBox"]]
    try:
        line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name={tmp['id']} Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"
    except KeyError:
        line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name=\"Svg{name['svg']}\" Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"

    name["svg"] += 1

    return line, name


def getStyle(line: str):

    fill = defaultdict(lambda: '"#FFFFFF"')
    lines = line.split("\t")

    for rows in lines:
        row = rows.split("}")[0]
        if "<" not in row and ">" not in row:
            key = row[1:].split("{")[0]
            color = row.split(":")[1].split(";")[0]
            fill[f'"{key}"'] = f'"{color}"'
    return fill


def getDict(path: str):
    with open(path, "r") as file:
        svg = file.read()

    fill = None

    name = defaultdict(lambda: 0)

    tab = 0

    start = 0
    xaml = []
    for match in re.finditer(">", svg):
        line = svg[start:match.end()]
        index = match.end()

        if "\n" in line:
            line = line.replace("\n", "")
        if "\t" in line:
            line = line.replace("\t", "")

        if "</svg" in line:
            tab = 0
            xaml.append("</Canvas>")
        elif "</g>" in line:
            tab -= 1
            prefixe = "".join(["\t"] * tab)
            xaml.append(f"{prefixe}</Canvas>")

        if "?" in line or "<!--" in line:
            xaml.append(line)
        elif "<svg" in line[:4]:
            print("params")
            tab += 1
            line, name = getParams(line=line, name=name)
            xaml.append(line)

        elif "<style" in line:
            print("style")
            index = svg.find("</style>") + len("</style>")
            line = svg[start:index].replace("\n", "")
            fill = getStyle(line)

        elif "<g" in line:
            prefixe = "".join(["\t"] * tab)

            if "id" in line:
                name_calque = line.split('"')[1]
                xaml.append(f"{prefixe}<Canvas Name=\"{name_calque}\">")
            else:
                xaml.append(f"{prefixe}<Canvas Name=\"g{name['group']}\">")
                name["group"] += 1

            tab += 1

        if balise_geom := next((x for x in ["<path", "<rect", "<polygon"] if x in line), False):
            geom, name, tab = getGeom(line=line, name=name, tab=tab, fill=fill, geom=balise_geom)

        start = index

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