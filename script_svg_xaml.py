import os
import re

import glob

from collections import defaultdict


def getGeom(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    match geom:
        case "<g":
            line, name, tab, fill, color_group = getGroup(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)
        case "<path":
            line, name, tab, fill, color_group = getPath(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)
        case "<rect":
            line, name, tab, fill, color_group = getRect(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)
        case "<polygon":
            line, name, tab, fill, color_group = getPolygon(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)
        case "<text":
            line, name, tab, fill, color_group = getText(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)

    return line, name, tab, fill, color_group


def getPath(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)

    prefixe = "".join(["\t"] * tab)


    line = f'{prefixe}<Path xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Path{name[geom]}"'
    line = f'{line} Fill="{fill[list(fill)[-1]]}"' if color_group else f'{line} Fill="{fill[tmp["class"]]}"'
    line = f'{line} Data="{tmp["d"]}"/>'

    return line, name, tab, fill, color_group


def getRect(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    prefixe = "".join(["\t"] * tab)

    if "x" in list(fill):
        line = f'{prefixe}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["x"]}" Canvas.Top="{tmp["y"]}" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{name[geom]}"'
    else:
        line = f'{prefixe}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{name[geom]}"'

    line = f'{line} Fill="{fill[list(fill)[-1]]}"' if color_group else f'{line} Fill="{fill[tmp["class"]]}"'

    return line, name, tab, fill, color_group


def getPolygon(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    prefixe = "".join(["\t"] * tab)

    line = f'{prefixe}<Polygon xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Points="{tmp["points"]}" Name="Polygon{name[geom]}" FillRule="NonZero"'
    line = f'{line} Fill="{fill[list(fill)[-1]]}"' if color_group else f'{line} Fill="{fill[tmp["class"]]}"'

    return line, name, tab, fill, color_group


def getText(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):
    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    prefixe = "".join(["\t"] * tab)

    matrix = tmp['transform'].split("(")[1].split(")")[0].split(" ")
    matrix = list(map(float, matrix))

    params = tmp["class"].split(" ")

    value = {}
    for param in params:
        if "#" in fill[param]:
            value["color"] = fill[param]
        elif "px" in fill[param]:
            value["top"] = getFontSize(size=matrix[5], fontSize=fill[param])
            value["size"] = fill[param]
        else:
            font = fill[param].replace("'", "").split("-")
            value["family"] = getFontFamilly(font[0])
            try:
                value["style"] = font[1]
            except IndexError:
                pass

    try:
        line = f'{prefixe}<TextBlock xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{matrix[4]}" Canvas.Top="{value["top"]}" FontFamily="{value["family"]}" FontStyle="{value["style"]}" FontSize="{value["size"]}" Name="Text{name["<text"]}">{tmp["value"]}</TextBlock>'
    except KeyError:
        line = f'{prefixe}<TextBlock xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{matrix[4]}" Canvas.Top="{value["top"]}" FontFamily="{value["family"]}" FontSize="{value["size"]}" Name="Text{name["<text"]}">{tmp["value"]}</TextBlock>'

    return line, name, tab, fill, color_group


def getGroup(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    prefixe = "".join(["\t"] * tab)

    if "fill" in line:
        line, name, fill, _ = setColors(line=line, name=name, fill=fill)
        color_group = True

    if "id" in line:
        name_calque = line.split('"')[1]
        line = f"{prefixe}<Canvas Name=\"{name_calque}\">"
    else:
        line = f"{prefixe}<Canvas Name=\"{geom[-1]}{name[geom]}\">"
        name[geom] += 1


    tab += 1

    return line, name, tab, fill, color_group


def getFontFamilly(familly: str):
    familly = familly.split("-")
    return " ".join(re.findall("[A-Z][^A-Z]*", familly[0]))


def getFontSize(size: float, fontSize: str):
    return size - float(fontSize.replace("px", ""))


def getStyle(line: str):

    fill = defaultdict(lambda: "#FFFFFF")
    lines = line.split("\t")

    for rows in lines:
        row = rows.split("}")[0]
        if "<" not in row and ">" not in row:
            key = row[1:].split("{")[0]
            color = row.split(":")[1].split(";")[0].replace("#", "")

            if len(color) == 3: #color mode CSS
                color = "".join([char*2 for char in color])
            color = f"#FF{color}".upper()

            fill[key] = color
    return fill


def getValue(line: str, name: defaultdict, geom: str, fill: defaultdict, color_group: bool):
    line = line.replace(f"{geom}", "").replace("/>", "").strip()

    if "</" in line:
        value = line.split(">")[1].split("<")[0]
        line = f"{line.split('>')[0]} value=\"{value}\""

    line = line.split('" ')
    tmp = {}
    for row in line:
        if "style" in row or "fill" in row:

            _, name, fill, row = setColors(line=row, name=name, fill=fill)

            text = "st"

            row = f"class=st{name[text]-1}"

        row = row.replace('"', "")
        row = row.split("=")
        tmp[row[0]] = row[1]

    name[geom] += 1

    return tmp, name, fill


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

    name["<svg"] += 1

    return line, name


def setColors(line: str, name: defaultdict, fill: defaultdict):
    text = "st"
    index = line.find("fill=")
    row = line[index:].replace('"', '').replace(">", "").split("=")
    row = f".{text}{name[text]}{{fill:{row[1]};}}"

    fill = getStyle(row) if fill is None else fill | getStyle(row)

    name[text] += 1

    return line, name, fill, row


def getFiles(path: str, ext="svg"):
    return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)


def getFileData(path: str):
    with open(path, "r", encoding="UTF-8") as file:
        return file.read()


def getDict(path: str):
    svg = getFileData(path=path)

    fill = None

    name = defaultdict(lambda: 0)

    tab = 0
    start = 0
    color_group = False
    xaml = []
    for match in re.finditer(">", svg):
        line = svg[start:match.end()]
        index = match.end()

        chars = [x for x in ["\n", "\t", "\r"] if x in line]
        for char in chars:
            line = line.replace(char, " ")

        if balise_geom := next((x for x in ["<style", "<text"] if x in line), False):
            text = f"{balise_geom[:1]}/{balise_geom[1:]}>"
            index = svg[start:].find(text) + len(text) + start
            line = svg[start:index].replace("\n", "")

        if "</svg" in line:
            tab = 0
            xaml.append("</Canvas>")
        elif "</g>" in line:
            tab -= 1
            color_group = False
            prefixe = "".join(["\t"] * tab)
            xaml.append(f"{prefixe}</Canvas>")

        if "?" in line: #  or "<!--" in line:
            xaml.extend((line, "<!-- Generator: Python 3.10, SVG Convert XAML . SVG Version: 6.00 Build 0)  -->"))

        elif "<svg" in line[:4]:
            tab += 1
            line, name = getParams(line=line, name=name)
            xaml.append(line)

        elif "<style" in line:
            fill = getStyle(line)

        if balise_geom := next((x for x in ["<g", "<path", "<rect", "<polygon", "<text"] if x in line), False):
            line, name, tab, fill, color_group = getGeom(line=line, name=name, tab=tab, fill=fill, geom=balise_geom, color_group=color_group)
            xaml.append(line)

        start = index

    return "\n".join(xaml)


if __name__ == '__main__':

    for file in getFiles(path="test"):
        truc = getDict(path=file)

        directory, name = os.path.split(file)
        name = f'{name.split(".")[0]}_tmp'



        with open(f"{directory}/{name}.xaml", "w", encoding='utf-8') as output:
            output.write(truc)

        print(truc)