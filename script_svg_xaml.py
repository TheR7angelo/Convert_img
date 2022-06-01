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
        case "<text":
            line, name, tab = getText(line=line, name=name, tab=tab, fill=fill, geom=geom)

    return line, name, tab


def getValue(line: str, name: defaultdict, geom: str, fill: defaultdict):
    line = line.replace(f"{geom}", "").replace("/>", "").strip()

    if "</" in line:
        value = line.split(">")[1].split("<")[0]
        line = f"{line.split('>')[0]} value=\"{value}\""

    line = line.split('" ')
    tmp = {}
    for row in line:
        if "style" in row:
            row = row.replace('"', '').split("=")
            row = f".st{name['st']}{{{row[1]}}}"

            fill = getStyle(row) if fill is None else fill | getStyle(row)
            row = f"class=st{name['st']}"

            name["st"] += 1
        row = row.replace('"', "")
        row = row.split("=")
        tmp[row[0]] = row[1]

    name[geom] += 1

    return tmp, name, fill


def getPath(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill)

    prefixe = "".join(["\t"] * tab)

    line = f'{prefixe}<Path xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Path{name[geom]}" Fill="{fill[tmp["class"]]}" Data="{tmp["d"]}"/>'

    return line, name, tab


def getRect(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill)
    prefixe = "".join(["\t"] * tab)

    try:
        line = f'{prefixe}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["x"]}" Canvas.Top="{tmp["y"]}" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{name[geom]}" Fill="{fill[tmp["class"]]}"/>'
    except KeyError:
        line = f'{prefixe}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{name[geom]}" Fill="{fill[tmp["class"]]}"/>'

    return line, name, tab


def getPolygon(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill)
    prefixe = "".join(["\t"] * tab)

    line = f'{prefixe}<Polygon xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Points="{tmp["points"]}" Name="Polygon{name[geom]}" FillRule="NonZero" Fill="{fill[tmp["class"]]}"/>'

    return line, name, tab


def getText(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str):
    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill)
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

    return line, name, tab


def getFontFamilly(familly: str):
    familly = familly.split("-")
    return " ".join(re.findall("[A-Z][^A-Z]*", familly[0]))


def getFontSize(size: float, fontSize: str):
    return size - float(fontSize.replace("px", ""))


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

    name["<svg"] += 1

    return line, name


def getStyle(line: str):

    fill = defaultdict(lambda: "#FFFFFF")
    lines = line.split("\t")

    for rows in lines:
        row = rows.split("}")[0]
        if "<" not in row and ">" not in row:
            key = row[1:].split("{")[0]
            color = row.split(":")[1].split(";")[0]
            fill[key] = color
    return fill


def getFileData(path: str):
    with open(path, "r", encoding="UTF-8") as file:
        return file.read()


def getDict(path: str):
    svg = getFileData(path=path)

    fill = None

    name = defaultdict(lambda: 0)

    tab = 0

    start = 0
    xaml = []
    for match in re.finditer(">", svg):
        line = svg[start:match.end()]
        index = match.end()

        chars = [x for x in ["\n", "\t", "\r"] if x in line]
        for char in chars:
            line = line.replace(char, "")

        if balise_geom := next((x for x in ["<style", "<text"] if x in line), False):
            text = f"{balise_geom[:1]}/{balise_geom[1:]}>"
            index = svg[start:].find(text) + len(text) + start
            line = svg[start:index].replace("\n", "")

        if "</svg" in line:
            tab = 0
            xaml.append("</Canvas>")
        elif "</g>" in line:
            tab -= 1
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

        elif "<g" in line:
            prefixe = "".join(["\t"] * tab)

            if "id" in line:
                name_calque = line.split('"')[1]
                xaml.append(f"{prefixe}<Canvas Name=\"{name_calque}\">")
            else:
                xaml.append(f"{prefixe}<Canvas Name=\"g{name['<g']}\">")
                name["<g"] += 1

            tab += 1

        if balise_geom := next((x for x in ["<path", "<rect", "<polygon", "<text"] if x in line), False):
            line, name, tab = getGeom(line=line, name=name, tab=tab, fill=fill, geom=balise_geom)
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