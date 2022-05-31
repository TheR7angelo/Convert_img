import os
import traceback
import re

import glob


def path_geom(geom: str):
    pass


def getFiles(path: str, ext="svg"):
    return glob.glob(f"{os.path.abspath(path)}/**/*.{ext}", recursive=True)


def getDict(path: str):
    try:
        with open(path, "r") as file:
            svg = file.read()
        # return xmltodict.parse(file)

        fill = {}

        start = 0
        xaml = []
        end = False
        for match in re.finditer(">", svg):
            line = svg[start:match.end()]
            index = match.end()

            if "\n" in line:
                line = line.replace("\n", "")
            if "\t" in line:
                line = line.replace("\t", "")

            if "?" in line or "<!--" in line:
                xaml.append(line)
            elif "<svg" in line[:4]:
                print("params")
                svg = svg.replace("</svg>", "")
                line = line.replace("<svg ", "").replace(">", "")
                line = line.replace("\" ", "\"||")
                line = line.split("||")

                tmp = {}
                for row in line:
                    row = row.split("=")
                    tmp[row[0]] = row[1]
                tmp["viewBox"] = tmp["viewBox"].replace('"', '').split(" ")
                tmp["viewBox"] = [f'"{item}"' for item in tmp["viewBox"]]
                line = f"<Canvas xmlns=\"http://schemas.microsoft.com/winfx/2006/xaml/presentation\" Name={tmp['id']} Canvas.Left={tmp['viewBox'][0]} Canvas.Top={tmp['viewBox'][1]} Width={tmp['viewBox'][2]} Height={tmp['viewBox'][3]}>"
                xaml.append(line)

            elif "<style" in line:
                print("style")
                index = svg.find("</style>") + len("</style>")
                line = svg[start:index].replace("\n", "").split("\t")
                for row in line:
                    if "<" not in row and ">" not in row:
                        key = row[1:].split("{")[0]
                        color = row.split(":")[1].split(";")[0]
                        fill[key] = color

            elif "<path" in line:
                print(line)

                # line = line.replace("<path", "").replace("/>", "")


            start = index
    except Exception:
        traceback.print_exc()
        xaml = []

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
