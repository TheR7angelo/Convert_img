from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

drawing = svg2rlg(r"test_valid/path/after_effects.svg")
renderPM.drawToFile(drawing, r'test/ice.png', fmt='png')

