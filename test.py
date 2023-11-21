from core.src.Monitor import Simulator
from core.src.Controller import Controller

simu = Simulator()

# # to remove the whole database
# simu.erase_database()

# # to create the database
# simu.set_system_info()
# simu.save_system_info()
# simu.create_fake_disk()


cont = Controller()
# filename = "colorbar_bi.png"
filename = "Project 1.2023.pdf"
# filename = "PureMagLocalization-ShenHongming.pptx"
# cont.process(mode="write", filename=filename)
cont.process(mode="read", filename=filename)