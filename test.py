from core.src.Monitor import Simulator
from core.src.Controller import Controller

simu = Simulator()

# to remove the whole database and restart
# simu.erase_database()
# simu.set_system_info()
# simu.save_system_info()
# simu.create_fake_disk()


cont = Controller()
# cont.process(mode="write", filename="colorbar_bi.png")
cont.process(mode="read", filename="colorbar_bi.png")