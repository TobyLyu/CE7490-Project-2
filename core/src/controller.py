import numpy as np
import copy
import ipdb
from core.src.GaloisField import GaloisField
from core.src.Monitor import Monitor
# import struct
import os

class RAID6(GaloisField):
    def __init__(self, w, n, m) -> None:
        """_summary_

        Args:
            w (int): word bit length
            n (int): num of data disk
            m (int): num of checksum disk
        """
        super().__init__(w = w)
        self.disk_num = n
        self.check_num = m
        self.F = np.zeros([m, n], dtype=int)
        for i in range(0, m):
            for j in range(1, n+1):
                self.F[i, j-1] = self.pow(j, i)
        self.A = np.vstack([np.eye(n, dtype=int), self.F])
    
    def encode(self, bit_str):
        """encode the input bit string with checksum

        Args:
            bit_str (nparray): Nx1 input data

        Returns:
            nparray: encoded output with checksum
        """
        
        # ipdb.set_trace()
        assert self.A.shape[1] == bit_str.shape[0]
        bit_in = copy.deepcopy(bit_str)
        return self.matrix_multiply(self.A, bit_str)
    
    def decode(self, bit_str):
        
        assert bit_str.shape[0] == self.A.shape[1]
        print(self.A[:self.num_data_disk, :])
        A_i = self.matrix_inverse(self.A[:self.num_data_disk, :])
        return self.matrix_multiply(A_i, bit_str)
    
    def update(self):
        pass
    
    def restore(self, bit_str, use_disk):
        """decode the input bit string from data or checksum

        Args:
            bit_str (Nx1): encoded input string
            use_disk (list or nparray): 1xN list of disk available

        Returns:
            nparray: decoded output
        """
        # ipdb.set_trace()
        assert bit_str.shape[0] == len(use_disk)
        assert bit_str.shape[0] == self.A.shape[1]
        if type(use_disk) == list:
            use_disk = np.array(use_disk, dtype = int)
        use_disk -= 1
        A_i = self.matrix_inverse(self.A[use_disk, :])
        return self.matrix_multiply(A_i, bit_str)
    
    def update(self, bit_str):
        pass
    
    
    
class Controller(Monitor, RAID6):
    def __init__(self) -> None:
        Monitor.__init__(self)
        RAID6.__init__(self, w=int(8*self.chunk_size), n=self.num_data_disk, m=self.num_check_disk)
        self.__content_cache = []
    
    def reset(self):
        self.__content_cache = []
        self.stripe_len = 0
        self.content_len = 0
        self.filename = []

    
    def read_from_system(self, path):
        # read from system file
        
        with open(path, "rb") as f:
            while True:
                data_chunk = f.read(self.chunk_size)
                if not data_chunk:
                    break
                self.__content_cache.append(int.from_bytes(data_chunk, "big"))
                
            # print(self.__content_cache)
            # print(len(self.__content_cache), max(self.__content_cache))
            self.content_len = len(self.__content_cache)
    
    def write_to_system(self, path):
        with open(path, 'wb') as f:
            byte_data = bytes(self.__content_cache)
            f.write(byte_data)
    
    def read_from_disk(self):
        start_p = int(self.files_info[self.filename][0])
        stripe_len = int(self.files_info[self.filename][1])
        if all(self.disk_status):
            enc_str = np.zeros([stripe_len, self.num_data_disk], dtype=int)
            for idx in range(self.num_data_disk):
                with open(self.disk_path[idx], 'rb') as f:
                    f.seek(start_p, 0)
                    enc_str[:, idx] = list(f.read(stripe_len))     
            # for idx, enc in enumerate(enc_str):
            #     enc_str[idx, :] = np.roll(enc, (idx % self.num_data_disk)) #
            self.__content_cache = self.decode(enc_str.T).T
        else:
            disk_list = np.arange(1, self.total_num_of_disk+1)
            alive_disk = disk_list[self.disk_status][:self.num_data_disk]
            enc_str = np.zeros([stripe_len, len(alive_disk)], dtype=int)
            for idx, i in enumerate(alive_disk):
                with open(self.disk_path[i-1], 'rb') as f:
                    f.seek(start_p, 0)
                    enc_str[:, idx] = list(f.read(stripe_len))
            # for idx, enc in enumerate(enc_str):
            #     enc_str[idx, :] = np.roll(enc, (idx % self.num_data_disk)) # read checksum from all disks
            print(enc_str)
            self.__content_cache = self.restore(enc_str.T, alive_disk).T
    
    def write_to_disk(self):
        enc_str = self.encode(self.__content_cache.T).T
        # print(enc_str)
        # for idx, enc in enumerate(enc_str):
        #     enc_str[idx, :] = np.roll(enc, -(idx % self.num_data_disk)) # save checksum into all disks
        
        print(enc_str)
        for i in range(self.num_of_disk):
            with open(self.disk_path[i], 'ab+') as f:
                # ipdb.set_trace()
                start_p = f.tell()
                byte_data = bytes(enc_str[:, i].tolist())
                f.write(byte_data)
        
        self.files_info[self.filename] = [self.stripe_len, self.content_len]
        with open(self.files_info_path, 'a+') as f:
            f.writelines([self.filename, ',', str(start_p), ',',  str(self.stripe_len), ',', str(self.content_len), '\n'])
    
    def splitter(self):
        """split the whole file into different disk partition
        """
        print(self.__content_cache[:10])
        self.stripe_len = self.content_len // self.num_data_disk + 1
        self.__content_cache = self.__content_cache + [0] * (self.stripe_len * self.num_data_disk - self.content_len)
        self.__content_cache = np.asarray(self.__content_cache).astype(int).reshape([self.stripe_len, self.num_data_disk])
        
        print(self.__content_cache.shape)
    
    def combiner(self):
        content_len = int(self.files_info[self.filename][2])
        print(self.__content_cache.shape)
        self.__content_cache = self.__content_cache.reshape(-1)
        self.__content_cache = self.__content_cache[:content_len].tolist()
        print(self.__content_cache[:10])
    
    def process(self, mode, filename):
        self.reset()
        self.filename = filename
        
        # filepath = "D:\CE7490\CE7490-Project-2\input_data\PureMagLocalization-ShenHongming.pptx"
        
        if mode == "write":
            if filename in self.files_info:
                print("File with same name exist.")
                # ipdb.set_trace()
                return
            path = os.path.join(os.getcwd(), 'input_data', filename)
            self.read_from_system(path)
            self.splitter()
            self.write_to_disk()
        
        if mode == "read":
            if filename not in self.files_info:
                print("Fail to find {} in RAID6 disk.".format(filename))
                return
            if self.num_check_disk < self.total_num_of_disk - sum(self.disk_status):
                print("Critical Error! Data cannot be restored.")
                return
            path = os.path.join(os.getcwd(), 'output_data', filename)
            self.read_from_disk()
            self.combiner()
            self.write_to_system(path)
    
if __name__ == "__main__":
    # test case
    rd6 = RAID6(w=4, n=6, m=2)
    pw = rd6.encode(np.array([[13, 14, 15, 10, 11, 12]], dtype=int).T)
    print(rd6.decode(pw, [0, 1, 2, 4, 5, 7]).T)
    
    rd6 = RAID6(w=8, n=6, m=2)
    pw = rd6.encode(np.array([[32, 12, 24, 47, 10, 22]], dtype=int).T)
    print(rd6.decode(pw, [0, 1, 2, 4, 5, 7]).T)
    
    rd6 = RAID6(w=16, n=8, m=2)
    pw = rd6.encode(np.array([[543, 1231, 23425, 33, 765, 41435, 214, 27383]], dtype=int).T)
    print(rd6.decode(pw, [0, 3, 4, 5, 6, 7, 8, 9]).T)
    
    cont = Controller()
    cont.process(mode="write", filename="colorbar_bi.png")
    cont.process(mode="read", filename="colorbar_bi.png")
