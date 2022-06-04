import os
import re

import glob

from collections import defaultdict

from script_svg_xaml_sql import database


connector = database(file="tmp_style.sqlite")

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
        case "<circle" | "<ellipse":
            line, name, tab, fill, color_group = getEllipse(line=line, name=name, tab=tab, fill=fill, geom=geom, color_group=color_group)

    return line, name, tab, fill, color_group


def getPath(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)

    tabulation = "".join(["\t"] * tab)

    row = f'{tabulation}<Path xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Path{name[geom]}"'

    if color_group:
        row = f'{row} Fill="{fill[list(fill)[-1]]["SolidColorBrush"]}"'
    elif "fill" in line:
        row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"'
    else:
        row = f'{row} Fill="#FF000000"'

    row = f'{row} Data="{tmp["d"]}"/>'

    # """Fill="{StaticResource a}""""

    # if color_group:
    #     row = f'{row} Fill="{fill[list(fill)[-1]]["SolidColorBrush"]}"'
    # elif "fill" in line:
    #     st = line.split("#")[1].split(";")[0]
    #     if len(st) ==6:
    #         st = f"#FF{st}"
    #     for key in fill:
    #         if fill[key]["SolidColorBrush"] == st:
    #             st = f'{{StaticResource {key}}}'
    #             break
    #     row = f'{row} Fill="{st}"'
    # else:
    #     row = f'{row} Fill="#FF000000"'

    # row = f'{row} Data="{tmp["d"]}"/>'


    return row, name, tab, fill, color_group


def getRect(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    tabulation = "".join(["\t"] * tab)

    for key in ["x", "y"]:
        if key not in list(tmp):
            tmp[key] = "0"

    row = f'{tabulation}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["x"]}" Canvas.Top="{tmp["y"]}" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{name[geom]}"'

    row = f'{row} Fill="{fill[list(fill)[-1]]["color"]}"/>' if color_group else f'{row} Fill="{fill[tmp["class"]]["color"]}"/>' if "fill" in line else f'{row} Fill="#FF000000"/>'

    return row, name, tab, fill, color_group


def getEllipse(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    tabulation = "".join(["\t"] * tab)

    if "r" in list(tmp):
        tmp["Width"] = f'{float(tmp["r"]) * 2}'
        tmp["Height"] = f'{float(tmp["r"]) * 2}'
        tmp["left"] = f'{float(tmp["cx"]) - float(tmp["r"])}'
        tmp["top"] = f'{float(tmp["cy"]) - float(tmp["r"])}'
    else:
        tmp["Width"] = f'{float(tmp["rx"]) * 2}'
        tmp["Height"] = f'{float(tmp["ry"]) * 2}'
        tmp["left"] = f'{float(tmp["cx"]) - float(tmp["rx"])}'
        tmp["top"] = f'{float(tmp["cy"]) - float(tmp["ry"])}'

    line = f'{tabulation}<Ellipse xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["left"]}" Canvas.Top="{tmp["top"]}" Width="{tmp["Width"]}" Height="{tmp["Height"]}"'
    line = f'{line} Fill="{fill[list(fill)[-1]]["color"]}"/>' if color_group else f'{line} Fill="{fill[tmp["class"]]["color"]}"/>' if "fill" in line else f'{line} Fill="#FF000000"/>'

    return line, name, tab, fill, color_group


def getPolygon(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    tabulation = "".join(["\t"] * tab)

    line = f'{tabulation}<Polygon xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Points="{tmp["points"]}" Name="Polygon{name[geom]}" FillRule="NonZero"'
    line = f'{line} Fill="{fill[list(fill)[-1]]["color"]}"/>' if color_group else f'{line} Fill="{fill[tmp["class"]]["color"]}"/>' if "fill" in line else f'{line} Fill="#FF000000"/>'

    return line, name, tab, fill, color_group


def getText(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):
    tmp, name, fill = getValue(line=line, name=name, geom=geom, fill=fill, color_group=color_group)
    tabulation = "".join(["\t"] * tab)

    matrix = tmp['transform'].split("(")[1].split(")")[0].split(" ")
    matrix = list(map(float, matrix))

    params = tmp["class"].split(" ")

    value = {}
    for param in params:
        for key, valeurs in fill[param].items():
            match key:
                case "color":
                    value[key] = valeurs
                case "font-family":
                    font = valeurs.replace("'", "").split("-")
                    value["family"] = getFontFamilly(font[0])
                    try:
                        if font[1].lower() == "regular":
                            font[1] = "Normal"
                        value["style"] = font[1]
                    except IndexError:
                        pass
                case "font-size":
                    value["top"] = getFontSize(size=matrix[5], fontSize=valeurs)
                    value["size"] = valeurs

    try:
        line = f'{tabulation}<TextBlock xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{matrix[4]}" Canvas.Top="{value["top"]}" FontFamily="{value["family"]}" FontStyle="{value["style"]}" FontSize="{value["size"]}" Foreground="{value["color"]}" Name="Text{name["<text"]}">{tmp["value"]}</TextBlock>'
    except KeyError:
        line = f'{tabulation}<TextBlock xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{matrix[4]}" Canvas.Top="{value["top"]}" FontFamily="{value["family"]}" FontSize="{value["size"]}" Foreground="{value["color"]}" Name="Text{name["<text"]}">{tmp["value"]}</TextBlock>'

    return line, name, tab, fill, color_group


def getGroup(line: str, name: defaultdict, tab: int, fill: defaultdict, geom: str, color_group: bool):

    tabulation = "".join(["\t"] * tab)

    if "fill" in line:
        line, name, fill, _ = setColors(line=line, name=name, fill=fill)
        color_group = True

    if "id" in line:
        name_calque = line.split('"')[1]
        line = f"{tabulation}<Canvas Name=\"{name_calque}\">"
    else:
        line = f"{tabulation}<Canvas Name=\"{geom[-1]}{name[geom]}\">"
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

            rows = row.split("{")[1].split(";")
            tmp = {}
            sub_key, value = "", ""

            for row in rows:
                if "#" in row and not next((x for x in ["width", "miterlimit"] if x in row), False):
                    sub_key = "SolidColorBrush"
                    color = row.replace("#", "").split(":")[1]
                    if len(color) == 3:  # color mode CSS
                        color = "".join([char * 2 for char in color])
                    value = f"#FF{color}".upper() if len(color) == 6 else f"#{color}"
                elif "width" in row:
                    sub_key = "epaisseur"
                    value = row.split(":")[1]
                elif "miterlimit" in row:
                    pass
                elif "family" in row:
                    sub_key = "font-family"
                    value = row.split(":")[1]
                elif "font-size" in row:
                    sub_key = "font-size"
                    value = row.split(":")[1]
                else:
                    continue
                tmp[sub_key] = value

            fill[key] = tmp.copy()

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

            _, name, fill, row, st = setColors(line=row, name=name, fill=fill)

            row = f"class={st}"

        row = row.replace('"', "")
        row = row.split("=")
        tmp[row[0]] = row[1]

    name[geom] += 1

    return tmp, name, fill


def getParams(line: str, name: defaultdict):
    line = line.replace("<svg ", "").replace(">", "")
    line = line.replace("\" ", "\"||")
    line = line.split("||")
    line = [item.strip() for item in line]

    tmp = {}
    for row in line:
        row = row.split("=")
        tmp[row[0]] = row[1]

    if "viewBox" not in list(tmp):
        tmp["viewBox"] = f"0 0 {tmp['width']} {tmp['height']}"

    tmp["viewBox"] = tmp["viewBox"].replace('"', '').split(" ")
    tmp["viewBox"] = [f'"{item}"' for item in tmp["viewBox"]]
    try:
        line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name={tmp['id']} Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"
    except KeyError:
        line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name=\"Svg{name['svg']}\" Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"

    name["<svg"] += 1

    return line, name


def setColors(line: str, name: defaultdict, fill: defaultdict):

    index = line.find("fill")
    row = line[index:].replace(":", "=").replace('"', '').replace(">", "").split("=")

    color = row[1].replace("#", "").replace(";", "")
    color = f"#FF{color}" if len(color) == 6 else f"#{color}"

    if base_style:= connector.find_value(key_name="value", value=color):
        st = base_style[0]["class"]
    else:
        text = "st"
        st = f"{text}{name[text]}"
        name[text] += 1
        connector.insert_style(key=st, type_value="SolidColorBrush", value=color)
        connector.commit()


    row = f".{st}{{fill:{row[1]};}}"


    fill = getStyle(row) if fill is None else fill | getStyle(row)

    return line, name, fill, row, st


def setRessource(xaml: list, brush: defaultdict):

    start = "\t<Canvas.Resources>"
    tab = "\t\t"
    end = "\t</Canvas.Resources>"

    resource = list(xaml[:3])
    xaml = xaml[3:]

    resource.append(start)

    txt = None
    for key in brush:
        for sub_key, value in brush[key].items():
            match sub_key:
                case "SolidColorBrush":
                    txt = f"{tab}<SolidColorBrush xmlns:x=\"http://schemas.microsoft.com/winfx/2006/xaml\" x:Key=\"{key}\" Color=\"{value}\"/>"
            if txt is not None:
                resource.append(txt)
                txt = None

    resource.append(end)

    for row in xaml:
        resource.append(row)

    return resource


def getFiles(path: str, ext: str):
    return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)


def getFileData(path: str):
    print(path)
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

        elif "<svg" in line:
            tab += 1
            line, name = getParams(line=line, name=name)
            xaml.append(line)

        elif "<style" in line:
            fill = getStyle(line)

        if balise_geom := next((x for x in ["<g", "<path", "<rect", "<polygon", "<text", "<circle", "<ellipse"] if x in line), False):
            line, name, tab, fill, color_group = getGeom(line=line, name=name, tab=tab, fill=fill, geom=balise_geom, color_group=color_group)
            xaml.append(line)

        start = index

    xaml = setRessource(xaml=xaml, brush=fill)

    return "\n".join(xaml)


if __name__ == '__main__':

    table = connector.create_table_style_tmp()

    for file in getFiles(path="test", ext="svg"):

        truc = getDict(path=file)

        directory, name = os.path.split(file)
        name = f'{name.split(".")[0]}_tmp'

        with open(f"{directory}/{name}.xaml", "w", encoding='utf-8') as output:
            output.write(truc)

        # connector.reset_table(table)

        # print(truc)

    # connector.delete_table(table)

