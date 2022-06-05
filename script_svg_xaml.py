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
        self.fill = None
        self.xaml = []
        self.color_group = ""

    def setPath(self, line: str, geom: str):
        tmp = self.getValue(line=line, geom=geom)

        tabulation = "".join(["\t"] * self.tabulation)

        row = f'{tabulation}<Path xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" Name="Path{self.name[geom]}"'

        if self.color_group:
            row = f'{row} Fill="{{StaticResource {self.color_group}}}"'
        elif "fill" in line:
            row = f'{row} Fill="{{StaticResource {tmp["class"]}}}"'
        else:
            row = f'{row} Fill="#FF000000"'

        row = f'{row} Data="{tmp["d"]}"/>'

        self.xaml.append(row)

    def setGroup(self, line: str, geom: str):
        tabulation = "".join(["\t"] * self.tabulation)

        if "fill" in line:
            self.color_group = self.setColor(line=line)
            # color_group = True

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
            # case "<rect":
            #     line, name, tab, fill, color_group = getRect(line=line, name=name, tab=tab, fill=fill, geom=geom,
            #                                                  color_group=color_group)
            # case "<polygon":
            #     line, name, tab, fill, color_group = getPolygon(line=line, name=name, tab=tab, fill=fill, geom=geom,
            #                                                     color_group=color_group)
            # case "<text":
            #     line, name, tab, fill, color_group = getText(line=line, name=name, tab=tab, fill=fill, geom=geom,
            #                                                  color_group=color_group)
            # case "<circle" | "<ellipse":
            #     line, name, tab, fill, color_group = getEllipse(line=line, name=name, tab=tab, fill=fill, geom=geom,
            #                                                     color_group=color_group)

    def setStyle(self, line: str):
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

                        value = f"#FF{color}" if len(color) == 6 else f"#{color}"
                        value = value.upper()

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

                    # if not (base_style := connector.find_value(key_name="value", value=color)):
                    #     text = "st"
                    #     st = f"{text}{name[text]}"
                    #     name[text] += 1
                    #     connector.insert_style(key=st, type_value="SolidColorBrush", value=color)
                    #     connector.commit()

                    self.connector.insert_style(key=key, type_value=sub_key, value=value)

                self.fill[key] = tmp.copy()

    def setColor(self, line: str):
        index = line.find("fill")
        row = line[index:].replace(":", "=").replace('"', '').replace(">", "").split("=")

        color = row[1].replace("#", "").replace(";", "")

        if len(color) == 3:  # color mode CSS
            color = "".join([char * 2 for char in color])

        color = f"#FF{color}" if len(color) == 6 else f"#{color}"
        color = color.upper()

        if base_style := self.connector.find_value(key_name="value", value=color):
            st = base_style[0]["class"]
        else:
            text = "st"
            st = f"{text}{self.name[text]}"
            self.name[text] += 1
            self.connector.insert_style(key=st, type_value="SolidColorBrush", value=color)
            self.connector.commit()

        # row = f".{st}{{fill:{color};}}"

        # fill = getStyle(row) if fill is None else fill | getStyle(row)

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

        self.name[geom] += 1

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

    def getFileData(self, path: str):
        with open(path, "r", encoding="UTF-8") as file:
            return file.read()

    def setRessources(self):
        start = "\t<Canvas.Resources>"
        tab = "\t\t"
        end = "\t</Canvas.Resources>"

        resource = list(self.xaml[:3])

        resource.append(start)

        style = self.connector.read_all(table="t_tmp_style")

        for row in style:
            match row["type"]:
                case "SolidColorBrush":
                    txt = f'{tab}<{row["type"]} xmlns:x="http://schemas.microsoft.com/winfx/2006/xaml" x:Key="{row["class"]}" Color="{row["value"]}"/>'
            resource.append(txt)
        resource.append(end)

        resource += self.xaml[3:]

        self.xaml = resource

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

    def convertDir(self, directory):
        self.table = self.connector.create_table_style_tmp()

        for file in self.getFiles(path=directory, ext="svg"):
            truc = self.getXaml(path=file)

            path, file_name = os.path.split(file)
            file_name = f'{file_name.split(".")[0]}_tmp'

            with open(f"{path}/{file_name}.xaml", "w", encoding='utf-8') as output:
                output.write(truc)

            # self.connector.reset_table(self.table)


if __name__ == '__main__':
    tmp = svg_xaml()
    tmp.convertDir(directory="test")
