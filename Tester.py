import time
import numpy as np
from core.src.Monitor import Simulator
from core.src.Controller import Controller
# from Monitor import Simulator
# from Controller import Controller
import struct
from time import perf_counter
import os

def create_dat(file_size):
    path = os.path.join(os.getcwd(), "test_data")
    if not os.path.exists(path):
        os.mkdir(path)
    arr = np.ones(file_size, dtype=np.uint8) * 255
    byte_data = struct.pack('<'+str(file_size)+'B', *arr.tolist())
    file_name = "s_{}.dat".format(file_size)
    with open(os.path.join(path, file_name), 'wb') as f:
        f.write(byte_data)
    return file_name


if __name__ == "__main__":
    size_list = [2**i for i in range(0,25)]
    path = os.path.join(os.getcwd(), "test_data")
    if not os.path.exists(path):
        os.mkdir(path)
    file_list = os.listdir(path)
    if len(file_list) == 0: 
        file_list = [create_dat(size) for size in size_list]
    
    file_list.sort()
    
    simu = Simulator()
    
    with open(os.path.join(os.getcwd(), "result.csv"), "w+") as f:
        f.writelines(["chunk_size, file_name, write, read, rebuild\n"])
    
    for chunk_size in [1, 2]:
        for file in file_list:
            simu.erase_database()
            simu.create_database(8)
            simu.set_system_info(8, 6, 2, chunk_size=chunk_size)
            cont = Controller()
            cont.detect_storage()
            
            print([chunk_size, file, "write"])
            start = perf_counter()
            cont.process(mode="write", filename=[file])
            write_time = perf_counter() - start
            
            
            print([chunk_size, file, "read"])
            start = perf_counter()
            cont.process(mode="read", filename=[file])
            read_time = perf_counter() - start
            
            print([chunk_size, file, "rebuild"])
            cont.disk_status = np.array([False, True, True, True, 
                                True, True, True, False], dtype=bool)
            cont.disk_on
            start = perf_counter()
            cont.process(mode="rebuild", filename=[file])
            rebuild_time = perf_counter() - start
            with open(os.path.join(os.getcwd(), "result.csv"), "a+") as f:
                f.writelines([str(chunk_size), ",", 
                        file[2:-4], ",", 
                        str(write_time), ",", 
                        str(read_time), ",", 
                        str(rebuild_time), "\n"])
            
    # f.close()