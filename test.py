from core.src.Monitor import Simulator
from core.src.Controller import Controller
import numpy as np

simu = Simulator()

# # to remove the whole database
simu.erase_database()
simu.create_database(8)
# to create the database
simu.set_system_info(8, 6, 2, 1)
# simu.save_system_info()


cont = Controller()
filename = "colorbar_bi.png"
# filename = "Project 1.2023.pdf"
# filename = "PureMagLocalization-ShenHongming.pptx"
cont.process(mode="write", filename=[filename])
simu.delete_disk(1)
cont.disk_status = np.array([False, True, True, True, 
                            True, True, True, True], dtype=bool)
cont.process(mode="read", filename=[filename])

