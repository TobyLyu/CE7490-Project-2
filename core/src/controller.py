import numpy as np
import copy
import ipdb
from GaloisField import GaloisField
from Monitor import Monitor
import struct

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
    
    def decode(self, bit_str, use_disk):
        """decode the input bit string from data or checksum

        Args:
            bit_str (Nx1): encoded input string
            use_disk (list or nparray): 1xN list of disk available

        Returns:
            nparray: decoded output
        """
        if type(use_disk) == list:
            use_disk = np.array(use_disk, dtype = int)
        use_disk -= 1
        A_i = self.matrix_inverse(self.A[use_disk, :])
        return self.matrix_multiply(A_i, bit_str)
    
    
class Controller(Monitor, RAID6):
    def __init__(self) -> None:
        Monitor.__init__(self)
        RAID6.__init__(self, w=int(8*self.chunk_size), n=self.num_data_disk, m=self.num_check_disk)
        self.__content_cache = []
        self.create_fake_disk()
    
    def reset(self):
        self.__content_cache = []
    
    def create_fake_disk(self):
        for i in range(self.num_of_disk):
            with open("D:\CE7490\CE7490-Project-2\storage\disk{}.txt".format(i+1), 'w') as f:
                pass

    
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
    
    def write_to_system(self):
        with open("D:\CE7490\CE7490-Project-2\output_data\colorbar_bi.png", 'wb') as f:
            byte_data = bytes(self.__content_cache)
            f.write(byte_data)
    
    def read_from_disk(self, disk_list):
        print(disk_list)
        enc_str = np.zeros([self.stripe_len, len(disk_list)], dtype=int)
        for idx, i in enumerate(disk_list):
            with open("D:\CE7490\CE7490-Project-2\storage\disk{}.txt".format(i), 'rb') as f:
                enc_str[:, idx] = list(f.read())
        # for idx, enc in enumerate(enc_str):
            # enc_str[idx, :] = np.roll(enc, (idx % self.num_data_disk)) # read checksum from all disks
        print(enc_str)
        self.__content_cache = self.decode(enc_str.T, disk_list).T
    
    def write_to_disk(self):
        enc_str = self.encode(self.__content_cache.T).T
        # print(enc_str)
        print(enc_str)
        # for idx, enc in enumerate(enc_str):
            # enc_str[idx, :] = np.roll(enc, -(idx % self.num_data_disk)) # save checksum into all disks
        for i in range(self.num_of_disk):
            with open("D:\CE7490\CE7490-Project-2\storage\disk{}.txt".format(i+1), 'wb') as f:
                byte_data = bytes(enc_str[:, i].tolist())
                f.write(byte_data)
    
    def splitter(self):
        """split the whole file into different disk partition
        """
        print(self.__content_cache[:10])
        self.stripe_len = self.content_len // self.num_data_disk + 1
        self.__content_cache = self.__content_cache + [0] * (self.stripe_len * self.num_data_disk - self.content_len)
        self.__content_cache = np.asarray(self.__content_cache).astype(int).reshape([self.stripe_len, self.num_data_disk])
        print(self.__content_cache.shape)
    
    def combiner(self):
        print(self.__content_cache.shape)
        self.__content_cache = self.__content_cache.reshape(-1)
        self.__content_cache = self.__content_cache[:self.content_len].tolist()
        print(self.__content_cache[:10])
    
    def process(self, mode, filepath):
        self.reset()
        # filepath = "D:\CE7490\CE7490-Project-2\input_data\PureMagLocalization-ShenHongming.pptx"
        
        if mode == "write":
            filepath = "D:\CE7490\CE7490-Project-2\input_data\colorbar_bi.png"
            self.read_from_system(filepath)
            self.splitter()
            self.write_to_disk()
        
        if mode == "read":
            self.read_from_disk([3,4,5,6,7, 8])
            self.combiner()
            self.write_to_system()
    
if __name__ == "__main__":
    # test case
    # rd6 = RAID6(w=4, n=6, m=2)
    # pw = rd6.encode(np.array([[13, 14, 15, 10, 11, 12]], dtype=int).T)
    # print(rd6.decode(pw, [0, 1, 2, 4, 5, 7]).T)
    
    # rd6 = RAID6(w=8, n=6, m=2)
    # pw = rd6.encode(np.array([[32, 12, 24, 47, 10, 22]], dtype=int).T)
    # print(rd6.decode(pw, [0, 1, 2, 4, 5, 7]).T)
    
    # rd6 = RAID6(w=16, n=8, m=2)
    # pw = rd6.encode(np.array([[543, 1231, 23425, 33, 765, 41435, 214, 27383]], dtype=int).T)
    # print(rd6.decode(pw, [0, 3, 4, 5, 6, 7, 8, 9]).T)
    
    cont = Controller()
    cont.process(mode="write", filepath=[])
    cont.process(mode="read", filepath=[])