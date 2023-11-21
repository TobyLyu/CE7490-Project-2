import yaml
import os
import numpy as np
import shutil
import ipdb

class Monitor:
    def __init__(self) -> None:
        self.files_info_path = os.path.join(os.getcwd(), 'core/config/files.csv')
        self.load_system_info()
        self.detect_storage()
        self.gen_file_list()
        
    def load_system_info(self):
        path = os.path.join(os.getcwd(), 'core/config/config.yml')
        with open(path, 'r') as file:
            self.config = yaml.safe_load(file)
        self.total_num_of_disk = self.config['total_num_of_disk']
        self.num_data_disk = self.config['num_data_disk']
        self.num_check_disk = self.config['num_check_disk']
        self.chunk_size = self.config['chunk_size']
        self.disk_status = np.array(self.config['disk_status'], dtype=bool)
        self.strip_size = self.num_data_disk * self.chunk_size
        
        self.disk_name = np.array(["disk{}.bin".format(i+1) for i in range(self.total_num_of_disk)])
        self.disk_path = []
        # self.disk_status = []
        for disk_name in self.disk_name:
            self.disk_path.append(os.path.join(os.getcwd(), "storage", disk_name))
            # self.disk_status.append(False)
        # self.disk_status = np.array(self.disk_status)
        
    def detect_storage(self):
        disk_lst = os.listdir(os.path.join(os.getcwd(), 'storage'))
        self.num_of_disk = len(disk_lst)
        disk_on = np.zeros(len(self.disk_status), dtype=bool)
        for disk_name in disk_lst:
            disk_on[np.where(self.disk_name == disk_name)[0]] = True
        self.disk_status = self.disk_status & disk_on
        self.disk_on = disk_on
            
    def gen_file_list(self):
        self.files_info = dict()
        if os.path.exists(self.files_info_path):
            with open(self.files_info_path, 'r') as f:
                files_info = f.readlines()
            for file in files_info:
                file = file.split(',')
                self.files_info[file[0]] = file[1:]
        else:
            with open(self.files_info_path, 'w') as f:
                pass
            
    def save_system_info(self):
        data = {"total_num_of_disk": self.total_num_of_disk,
                "num_data_disk": self.num_data_disk,
                "num_check_disk": self.num_check_disk,
                "chunk_size": self.chunk_size,
                "disk_status": self.disk_status.tolist()
                }
        
        folder = os.path.join(os.getcwd(), 'core/config')
        if not os.path.exists(folder):
            os.mkdir(folder)
        path = os.path.join(os.getcwd(), 'core/config/config.yml')
        with open(path, 'w') as file:
            yaml.safe_dump(data, file)
        

class Simulator():
    def __init__(self) -> None:
        # self.path = 
        pass
    
    def save_system_info(self):
        data = {"total_num_of_disk": self.total_num_of_disk,
                "num_data_disk": self.num_data_disk,
                "num_check_disk": self.num_check_disk,
                "chunk_size": self.chunk_size,
                "disk_status": [True for _ in range(self.total_num_of_disk)]
                }
        
        folder = os.path.join(os.getcwd(), 'core/config')
        if not os.path.exists(folder):
            os.mkdir(folder)
        path = os.path.join(os.getcwd(), 'core/config/config.yml')
        with open(path, 'w') as file:
            yaml.safe_dump(data, file)
            
            
    def set_system_info(self):
        self.total_num_of_disk = 8
        self.num_data_disk = 6
        self.num_check_disk = 2
        self.chunk_size = 1
    
    def create_database(self):
        folder = os.path.join(os.getcwd(), "storage")
        if not os.path.exists(folder):
            os.mkdir(folder)
            
        folder = os.path.join(os.getcwd(), "core/config")
        if not os.path.exists(folder):
            os.mkdir(folder)
                    
        for i in range(self.total_num_of_disk):
            self.create_fake_disk(i+1)
            # path = os.path.join(os.getcwd(), "storage", "disk{}.bin".format(i+1))
            # if os.path.exists(path):
            #     continue
            # with open(path, 'w') as f:
            #     pass
            
    def create_disk(self, n):
        path = os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n))
        if os.path.exists(path):
            return
        with open(path, 'w') as f:
            pass
            
    def delete_disk(self, n):
        path = os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n))
        if os.path.exists(path):
            os.remove(os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n)))
        
    def erase_database(self):
        if os.path.exists(os.path.join(os.getcwd(), "storage/")):
            shutil.rmtree(os.path.join(os.getcwd(), "storage/"))
        if os.path.exists(os.path.join(os.getcwd(), "core/config/")):
            shutil.rmtree(os.path.join(os.getcwd(), "core/config/"))