from FossBox import FossBox
from PimoroniI75 import PimoroniI75

disp = PimoroniI75()
FossBox(disp, disp.weapon_left(), disp.weapon_right(), disp.bell_left(), disp.bell_right()).run()