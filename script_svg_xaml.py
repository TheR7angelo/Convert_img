import os
import re

import glob

from collections import defaultdict

from script_svg_xaml_sql import database


class svg_xaml:

    def __init__(self):
        self.connector = database(file="tmp_style.sqlite")
        self.name = defaultdict(lambda: 0)
        self.tabulation = 0
        self.xaml = []
        self.color_group = ""
        self.table = ""

    def setEllipse(self, line: str, geom: str):
        tmp = self.getValue(line=line, geom=geom)
        tabulation = "".join(["\t"] * self.tabulation)

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

        row = f'{tabulation}<Ellipse xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["left"]}" Canvas.Top="{tmp["top"]}" Width="{tmp["Width"]}" Height="{tmp["Height"]}"'

        if self.color_group:
            row = f'{row} Fill="{{StaticResource {self.color_group}}}"/>'
        elif "fill" in line or "class" in line:
            row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"/>'
        else:
            row = f'{row} Fill="#FF000000"/>'

        self.xaml.append(row)

    def getFontSize(self, size: float, fontSize: str):
        return size - float(fontSize.replace("px", ""))

    def setText(self, line: str, geom: str):

        tmp = self.getValue(line=line, geom=geom)
        tabulation = "".join(["\t"] * self.tabulation)

        matrix = tmp['transform'].split("(")[1].split(")")[0].split(" ")
        matrix = list(map(float, matrix))

        params = tmp["class"].split(" ")

        style = {}
        for param in params:
            values = self.connector.find_value(key_name="class", value=param)
            for row in values:
                match row["type"]:
                    case "SolidColorBrush":
                        style["fill"] = f'{{StaticResource {row["class"]}}}'
                    case "StrokeColorBrush":
                        style["strokecolor"] = row["value"]
                    case "stroke-miterlimit":
                        style["miterlimit"] = row["value"]
                    case "font-family":
                        style["family"] = f'{{StaticResource {row["class"]}}}'
                        try:
                            value = row["value"].split("-")
                            style["style"] = value[1]
                        except IndexError:
                            pass
                    case "font-size":
                        style["top"] = self.getFontSize(size=matrix[5], fontSize=row["value"])
                        style["size"] = row["value"]

        row = f'{tabulation}<TextBlock xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{matrix[4]}" Canvas.Top="{style["top"]}"'
        if "family" in list(style):
            row = f'{row} FontFamily="{style["family"]}"'
        if "style" in list(style):
            row = f'{row} FontStyle="{style["style"]}"'
        if "size" in list(style):
            row = f'{row} FontSize="{style["size"]}"'
        if "fill" in list(style):
            row = f'{row} Foreground="{style["fill"]}"'
        if "strokecolor" in list(style):
            row = f'{row} '
        row = f'{row} Name="Text{self.name[geom]}" Text="{tmp["value"]}"/>'

        self.xaml.append(row)

    def setRect(self, line: str, geom: str):
        tmp = self.getValue(line=line, geom=geom)
        tabulation = "".join(["\t"] * self.tabulation)

        for key in ["x", "y"]:
            if key not in list(tmp):
                tmp[key] = "0"

        row = f'{tabulation}<Rectangle xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Canvas.Left="{tmp["x"]}" Canvas.Top="{tmp["y"]}" Width="{tmp["width"]}" Height="{tmp["height"]}" Name="Rect{self.name[geom]}"'

        if self.color_group:
            row = f'{row} Fill="{{StaticResource {self.color_group}}}"/>'
        elif "fill" in line or "class" in line:
            row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"/>'
        else:
            row = f'{row} Fill="#FF000000"/>'

        self.xaml.append(row)

    def setPolygon(self, line: str, geom: str):
        tmp = self.getValue(line=line, geom=geom)
        tabulation = "".join(["\t"] * self.tabulation)

        row = f'{tabulation}<Polygon xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Polygon{self.name[geom]}" FillRule="NonZero"'

        if self.color_group:
            row = f'{row} Fill="{{StaticResource {self.color_group}}}"'
        elif "fill" in line or "class" in line:
            row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"'
        else:
            row = f'{row} Fill="#FF000000"'

        row = f'{row} Points="{tmp["points"]}"/>'

        self.xaml.append(row)

    def setPath(self, line: str, geom: str):
        tmp = self.getValue(line=line, geom=geom)

        tabulation = "".join(["\t"] * self.tabulation)

        row = f'{tabulation}<Path xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Path{self.name[geom]}"'

        if self.color_group:
            row = f'{row} Fill="{{StaticResource {self.color_group}}}"'
        elif "fill" in line or "class" in line:
            row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"'
        else:
            row = f'{row} Fill="#FF000000"'

        row = f'{row} Data="{tmp["d"]}"/>'

        self.xaml.append(row)

    def setGroup(self, line: str, geom: str):
        tabulation = "".join(["\t"] * self.tabulation)

        if "fill" in line:
            self.color_group = self.setColor(line=line)

        if "id" in line:
            name_calque = line.split('"')[1]
            line = f"{tabulation}<Canvas Name=\"{name_calque}\">"
        else:
            line = f"{tabulation}<Canvas Name=\"{geom[-1]}{self.name[geom]}\">"
            self.name[geom] += 1

        self.tabulation += 1

        self.xaml.append(line)

    def setGeom(self, line: str, geom: str):
        match geom:
            case "<g":
                self.setGroup(line=line, geom=geom)
            case "<path":
                self.setPath(line=line, geom=geom)
            case "<rect":
                self.setRect(line=line, geom=geom)
            case "<polygon":
                self.setPolygon(line=line, geom=geom)
            case "<text":
                self.setText(line=line, geom=geom)
            case "<circle" | "<ellipse":
                self.setEllipse(line=line, geom=geom)
        self.name[geom] += 1

    def setStyle(self, line: str):
        lines = line.split("\t")

        for rows in lines:
            row = rows.split("}")[0]
            if "<" not in row and ">" not in row:
                key = row[1:].split("{")[0]

                rows = row.split("{")[1].split(";")

                for row in rows:
                    if "#" in row and not next((x for x in ["width", "miterlimit"] if x in row), False):
                        self.setColor(line=row, key=key)
                    elif "stroke" in row:
                        self.setStroke(line=row, key=key)
                    elif "font" in row:
                        self.setFont(line=row, key=key)
                    else:
                        continue

    def setFont(self, line: str, key: str):
        row = line.replace(":", "=").replace("'", "").split("=")
        self.connector.insert_style(key=key, type_value=row[0], value=row[1])
        self.connector.commit()

    def setStroke(self, line: str, key: str):
        row = line.replace(":", "=").split("=")

        self.connector.insert_style(key=key, type_value=row[0], value=row[1])
        self.connector.commit()

    def setColor(self, line: str, key=None):
        sub_key = line.replace(":", "=").split("=")[0]
        return self.setFill(line=line, sub_key=sub_key, key=key)

    def setFill(self, line: str, sub_key: str, key=None):
        index = line.find(sub_key)
        row = line[index:].replace(":", "=").replace('"', '').replace(">", "").split("=")

        color = row[1].replace("#", "").replace(";", "")

        if len(color) == 3:  # color mode CSS
            color = "".join([char * 2 for char in color])

        color = f"#FF{color}" if len(color) == 6 else f"#{color}"
        color = color.upper()

        if base_style := self.connector.find_value(key_name="value", value=color) and key is None:
            st = base_style[0]["class"]
        else:
            text = "st"
            if key is None:
                st = f"{text}{self.name[text]}"
                self.name[text] += 1
            else:
                st = key

                self.name[text] = int(st.replace(text, "")) + 1

            type_value = "SolidColorBrush" if sub_key == "fill" else "StrokeColorBrush"

            self.connector.insert_style(key=st, type_value=type_value, value=color)
            self.connector.commit()

        return st

    def getValue(self, line: str, geom: str):
        line = line.replace(f"{geom}", "").replace("/>", "").strip()

        if "</" in line:
            value = line.split(">")[1].split("<")[0]
            line = f"{line.split('>')[0]} value=\"{value}\""

        line = line.split('" ')
        tmp = {}
        for row in line:
            if "style" in row or "fill" in row:
                st = self.setColor(line=row)

                row = f"class={st}"

            row = row.replace('"', "")
            row = row.split("=")
            tmp[row[0]] = row[1]

        return tmp

    def setParams(self, line: str, geom: str):
        line = line.replace(f"{geom} ", "").replace(">", "")
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
            line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name=\"Svg{self.name[geom]}\" Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"

        self.name[geom] += 1
        self.xaml.append(line)

    def getFontFamily(self, family: str):
        family = family.split("-")
        return " ".join(re.findall("[A-Z][^A-Z]*", family[0]))

    def setRessources(self):

        start = "\t<Canvas.Resources>"
        tab = "\t\t"
        end = "\t</Canvas.Resources>"

        idx = next((i for i, s in enumerate(self.xaml) if "\t" in s), -1)

        resource = list(self.xaml[:idx])

        resource.append(start)

        style = self.connector.read_all(table="t_tmp_style")

        """<FontFamily xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Key="st2" FamilyNames="Calibri"/>"""

        for row in style:
            match row["type"]:
                case "SolidColorBrush":
                    txt = f'<{row["type"]} xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Key="{row["class"]}" Color="{row["value"]}"/>'
                case "font-family":
                    txt = f'<FontFamily xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Key="{row["class"]}">{self.getFontFamily(family=row["value"])}</FontFamily>'
                case _:
                    txt = None
            if txt is not None:
                resource.append(f'{tab}{txt}')
        resource.append(end)

        resource += self.xaml[idx:]

        self.xaml = resource

    def getFileData(self, path: str):
        with open(path, "r", encoding="UTF-8") as file:
            return file.read()

    def getXaml(self, path: str):
        svg = self.getFileData(path=path)

        start = 0

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
                self.tabulation = 0
                self.xaml.append("</Canvas>")

            elif "</g>" in line:
                self.tabulation -= 1
                self.color_group = ""
                prefixe = "".join(["\t"] * self.tabulation)
                self.xaml.append(f"{prefixe}</Canvas>")

            if "?" in line:  # or "<!--" in line:
                self.xaml.extend(
                    (line, "<!-- Generator: Python 3.10, SVG Convert XAML . SVG Version: 6.00 Build 0)  -->"))

            elif "<svg" in line:
                self.tabulation += 1
                self.setParams(line=line, geom="<svg")

            elif "<style" in line:
                self.setStyle(line)

            if balise_geom := next((x for x in ["<g", "<path", "<rect", "<polygon", "<text", "<circle", "<ellipse"] if x in line), False):
                self.setGeom(line=line, geom=balise_geom)

            start = index

        self.setRessources()

        return "\n".join(self.xaml)

    def getFiles(self, path: str, ext: str):
        return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)

    def reset(self):
        self.connector.reset_table(self.table)

        self.name.clear()
        self.tabulation = 0
        self.xaml = []
        self.color_group = ""

    def convertDir(self, directory):
        self.table = self.connector.create_table_style_tmp()

        for file in self.getFiles(path=directory, ext="svg"):
            truc = self.getXaml(path=file)

            path, file_name = os.path.split(file)
            file_name = f'{file_name.split(".")[0]}_tmp'

            with open(f"{path}/{file_name}.xaml", "w", encoding='utf-8') as output:
                output.write(truc)

            self.reset()


if __name__ == '__main__':
    tmp = svg_xaml()
    tmp.convertDir(directory="test")
