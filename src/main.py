from FossBox import FossBox
from PimoroniI75 import PimoroniI75
from MatrixPortalS3 import MatrixPortalS3

# disp = PimoroniI75()
disp = MatrixPortalS3()
FossBox(disp, disp.weapon_left(), disp.weapon_right(), disp.bell_left(), disp.bell_right()).run()