import xml.etree.ElementTree as ET

import glob


def getFiles(path: str, ext="svg"):
    return glob.glob(f"{path}/**/*.{ext}", recursive=True)

def getCode(path: str):
    tree = ET.parse(path)
    return tree.getroot()



if __name__ == '__main__':
    print(getFiles(path="test"))

    truc = getCode(getFiles(path="test")[0])

    print("hey")
