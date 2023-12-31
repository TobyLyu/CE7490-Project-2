import yaml
import os
import numpy as np
import shutil

class Monitor:
    def __init__(self) -> None:
        self.files_info_path = os.path.join(os.getcwd(), 'core/config/files.csv')
        self.load_system_info()
        self.detect_storage()
        self.gen_file_list()
        
    def load_system_info(self):
        """load system information from file since last shutdown       
        """
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
        for disk_name in self.disk_name:
            self.disk_path.append(os.path.join(os.getcwd(), "storage", disk_name))
        
    def detect_storage(self):
        """_summary_

        Returns:
            int: error code
        """
        if not os.path.exists(os.path.join(os.getcwd(), 'storage')):
            self.disk_status = np.zeros(len(self.disk_status), dtype=bool)
            return 1
        disk_lst = os.listdir(os.path.join(os.getcwd(), 'storage'))
        self.num_of_disk = len(disk_lst)
        disk_on = np.zeros(len(self.disk_status), dtype=bool)
        for disk_name in disk_lst:
            disk_on[np.where(self.disk_name == disk_name)[0]] = True
        self.disk_status = self.disk_status & disk_on
        self.disk_on = disk_on
        return 0
            
    def gen_file_list(self):
        """read file list in RAID disk and their properties (address, length)
        """
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
        """save system information and last status for next time use
        """
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
        pass
    
    def save_system_info(self):
        """save user specified system configuration
        """
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
            
            
    def set_system_info(self, num_of_disk, data_disk, check_disk, chunk_size):
        """manually set system configuration

        Args:
            num_of_disk (int)
            data_disk (int)
            check_disk (int)
            chunk_size (int)
        """
        self.total_num_of_disk = num_of_disk
        self.num_data_disk = data_disk
        self.num_check_disk = check_disk
        self.chunk_size = chunk_size
        self.save_system_info()
    
    def create_database(self, num_of_disk):
        """create input and ouput folders and disks

        Args:
            num_of_disk (int)
        """
        folder = os.path.join(os.getcwd(), "storage")
        if not os.path.exists(folder):
            os.mkdir(folder)
            
        folder = os.path.join(os.getcwd(), "core/config")
        if not os.path.exists(folder):
            os.mkdir(folder)
                    
        folder = os.path.join(os.getcwd(), "input_data")
        if not os.path.exists(folder):
            os.mkdir(folder)
                    
        folder = os.path.join(os.getcwd(), "output_data")
        if not os.path.exists(folder):
            os.mkdir(folder)
            
        for i in range(num_of_disk):
            self.create_disk(i+1)
            
    def create_disk(self, n):
        """create the disk n

        Args:
            n (int): disk label
        """
        path = os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n))
        if os.path.exists(path):
            return
        with open(path, 'w') as f:
            pass
            
    def delete_disk(self, n):
        """remove the disk m

        Args:
            n (int): disk label
        """
        path = os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n))
        if os.path.exists(path):
            os.remove(os.path.join(os.getcwd(), "storage", "disk{}.bin".format(n)))
        
    def erase_database(self):
        """remove all folders and delete the disks
        """
        if os.path.exists(os.path.join(os.getcwd(), "storage/")):
            shutil.rmtree(os.path.join(os.getcwd(), "storage/"))
        if os.path.exists(os.path.join(os.getcwd(), "core/config/")):
            shutil.rmtree(os.path.join(os.getcwd(), "core/config/"))
        if os.path.exists(os.path.join(os.getcwd(), "output_data/")):
            shutil.rmtree(os.path.join(os.getcwd(), "output_data/"))