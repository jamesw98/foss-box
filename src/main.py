import Utils
from FossBox import FossBox
from PimoroniI75 import PimoroniI75
# from MatrixPortalS3 import MatrixPortalS3

pins = Utils.config_check()

disp = PimoroniI75(pins)
# disp = MatrixPortalS3(pins)
FossBox(disp, disp.weapon_left(), disp.weapon_right(), disp.bell_left(), disp.bell_right()).run()