import numpy as np
import copy
import ipdb
import struct
from core.src.GaloisField import GaloisField
from core.src.Monitor import Monitor
# from GaloisField import GaloisField
# from Monitor import Monitor
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
        self.data_num = n
        self.check_num = m
        self.F = np.zeros([m, n], dtype=int)
        for i in range(0, m):
            for j in range(1, n+1):
                self.F[i, j-1] = self.pow(j, i)
        self.A = np.vstack([np.eye(n, dtype=int), self.F])
    
    def encode(self, bit_str):
        """encode the input bit string with checksum

        Args:
            bit_str (nparray): N x {stripe_len} input data

        Returns:
            nparray: encoded output with checksum
        """
        
        # ipdb.set_trace()
        assert self.A.shape[1] == bit_str.shape[0]
        bit_in = copy.deepcopy(bit_str)
        
        # this calculation is slow and think the above I matrix is not necessary
        # self.matrix_multiply(self.A, bit_in)
        # return self.matrix_multiply(self.A, bit_in)
        
        # so we only ccalculate the checksum bit only
        check_bit = self.matrix_multiply(self.A[-self.check_num:, :], bit_in)
        return np.hstack([bit_str.T, check_bit.T]).T
        
    
    def decode(self, bit_str):
        
        assert bit_str.shape[0] == self.A.shape[1]
        # print(self.A[:self.data_num, :])
        A_i = self.matrix_inverse(self.A[:self.data_num, :])
        return self.matrix_multiply(A_i, bit_str)
    
    def cal_A_i(self, num_disk, num_data, disk_status):
        self.A_i_lst = []
        for i in range(num_disk):
            roll_n = i % num_disk
            # ipdb.set_trace()
            self.A_i_lst.append(self.matrix_inverse(self.A[np.roll(disk_status, roll_n), :][:num_data, :]))
        
    
    def restore(self, bit_str, disk_num, data_num):
        """decode the input bit string from data or checksum

        Args:
            bit_str (N x strape_len): encoded input string
            use_disk (list or nparray): 1xN list of disk available

        Returns:
            nparray: decoded output
        """
        # ipdb.set_trace()
        # assert bit_str.shape[0] == len(use_disk)
        assert bit_str.shape[0] == self.A.shape[1]
        # if type(use_disk) == list:
        #     use_disk = np.array(use_disk, dtype = int)
        # use_disk -= 1
        # A_i = self.matrix_inverse(self.A[use_disk, :])
        # return self.matrix_multiply(A_i, bit_str)
        output = np.zeros([data_num, bit_str.shape[1]], dtype=int)
        for i in range(bit_str.shape[1]):
            roll_n = i % disk_num
            # ipdb.set_trace()
            output[:, i] = self.matrix_multiply(self.A_i_lst[roll_n], bit_str[:, i].reshape(-1, 1)).reshape(-1)
        return output
        
    
    def update(self, bit_str):
        pass
    
    
    
class Controller(Monitor, RAID6):
    def __init__(self) -> None:
        Monitor.__init__(self)
        RAID6.__init__(self, w=int(8*self.chunk_size), n=self.num_data_disk, m=self.num_check_disk)
        self.__content_cache = []
        self.pack_m = ['c', 'B', 'H', 'L', 'Q']
    
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
                self.__content_cache.append(int.from_bytes(data_chunk, "little"))
            
            # print(self.__content_cache)
            # print(len(self.__content_cache), max(self.__content_cache))
            # data = f.read()
            # if len(data) % self.chunk_size: byte_len = len(data) // self.chunk_size + 1
            # else: byte_len = len(data) // self.chunk_size
            # ipdb.set_trace()
            
            # self.__content_cache = struct.unpack('<'+str(byte_len)+self.pack_m[self.chunk_size], data)
            self.content_len = len(self.__content_cache)
    
    def write_to_system(self, path):
        with open(path, 'wb') as f:
            # print(self.__content_cache)
            # ipdb.set_trace()
            byte_data = struct.pack('<'+str(len(self.__content_cache))+self.pack_m[self.chunk_size], *self.__content_cache)
            # ipdb.set_trace()
            # byte_data = struct.unpack('<'+str(len(byte_data))+'B', byte_data)
            # byte_data = bytes(self.__content_cache)
            f.write(byte_data)
    
    def read_from_disk(self):
        start_p = int(self.files_info[self.filename][0])
        stripe_len = int(self.files_info[self.filename][1])
        # if all(self.disk_status):
        #     enc_str = np.zeros([stripe_len, self.num_data_disk], dtype=int)
        #     for idx in range(self.num_data_disk):
        #         with open(self.disk_path[idx], 'rb') as f:
        #             f.seek(start_p, 0)
        #             # enc_str[:, idx] = list(f.read(stripe_len))    
        #             byte_data = f.read(stripe_len * self.chunk_size) 
        #             enc_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)

        #     enc_str = np.zeros([stripe_len, self.total_num_of_disk], dtype=int)
        #     for idx in range(self.num_data_disk):
        #         with open(self.disk_path[idx], 'rb') as f:
        #             f.seek(start_p, 0)
        #             # enc_str[:, idx] = list(f.read(stripe_len))    
        #             byte_data = f.read(stripe_len * self.chunk_size) 
        #             enc_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)
        #     # for idx, enc in enumerate(enc_str):
            
        #     # for idx, enc in enumerate(enc_str):
        #     #     enc_str[idx, :] = np.roll(enc, (idx % self.num_data_disk)) #
            
        #     # due to matrix multiply is slow, we do not decode if disk is healthy
        #     # self.__content_cache = self.decode(enc_str.T).T
        #     self.__content_cache = enc_str[:, :self.num_data_disk]
        # else:
            # disk_list = np.arange(1, self.total_num_of_disk+1)
            # alive_disk = disk_list[self.disk_status][:self.num_data_disk]
            # enc_str = np.zeros([stripe_len, len(alive_disk)], dtype=int)
            # for idx, i in enumerate(alive_disk):
            #     with open(self.disk_path[i-1], 'rb') as f:
            #         f.seek(start_p, 0)
            #         byte_data = f.read(stripe_len * self.chunk_size)
            #         enc_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)
            # self.__content_cache = self.restore(enc_str.T, alive_disk).T

        tmp_str = np.zeros([stripe_len, self.total_num_of_disk], dtype=int)
        enc_str = np.zeros([stripe_len, self.num_data_disk], dtype=int)
        for idx in range(self.total_num_of_disk):
            if not self.disk_status[idx]:
                continue
            else:
                with open(self.disk_path[idx], 'rb') as f:
                    f.seek(start_p, 0)
                    # enc_str[:, idx] = list(f.read(stripe_len))    
                    byte_data = f.read(stripe_len * self.chunk_size) 
                    tmp_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)            
        for idx in range(stripe_len):
            roll_n = idx % self.total_num_of_disk
            # ipdb.set_trace()
            enc_str[idx, :] = np.roll(tmp_str[idx, :], roll_n)[np.roll(self.disk_status, roll_n)][:self.num_data_disk]
            
        # print(enc_str)
        if all(self.disk_status):
            self.__content_cache = enc_str
        else:
            self.__content_cache = self.restore(enc_str.T, self.total_num_of_disk, self.num_data_disk).T
            
        # print(self.__content_cache)
    
    def write_to_disk(self):
        enc_str = self.encode(self.__content_cache.T).T
        # print(enc_str)

        for idx, enc in enumerate(enc_str):
            enc_str[idx, :] = np.roll(enc, -(idx % self.total_num_of_disk)) # save checksum into all disks
        
        
        # print(enc_str)
        for i in range(self.total_num_of_disk):
            with open(self.disk_path[i], 'ab+') as f:
                start_p = f.tell()
                byte_data = struct.pack('<'+str(len(enc_str[:, i]))+self.pack_m[self.chunk_size], *enc_str[:, i].tolist())
                # byte_data = bytes(enc_str[:, i].tolist())
                f.write(byte_data)
        
        self.files_info[self.filename] = [str(start_p), str(self.stripe_len), str(self.content_len)]
        with open(self.files_info_path, 'a+') as f:
            f.writelines([self.filename, ',', str(start_p), ',',  str(self.stripe_len), ',', str(self.content_len), '\n'])
    
    def splitter(self):
        """split the whole file into different disk partition
        """
        # print(self.__content_cache[:10])
        self.stripe_len = self.content_len // self.num_data_disk + 1
        self.__content_cache = self.__content_cache + [0] * (self.stripe_len * self.num_data_disk - self.content_len)
        self.__content_cache = np.asarray(self.__content_cache).astype(int).reshape([self.stripe_len, self.num_data_disk])
        # print(self.__content_cache)
        
        # print(self.__content_cache.shape)
    
    def combiner(self):
        content_len = int(self.files_info[self.filename][2])
        # print(self.__content_cache.shape)
        self.__content_cache = self.__content_cache.reshape(-1)
        self.__content_cache = self.__content_cache[:content_len].tolist()
        # print(self.__content_cache[:10])
    
    def rebuild_disk(self):
        enc_str = self.encode(self.__content_cache.T).T
        
        for idx, enc in enumerate(enc_str):
            enc_str[idx, :] = np.roll(enc, -(idx % self.total_num_of_disk)) # save checksum into all disks
        
        die_disk = np.arange(0, self.total_num_of_disk)[~self.disk_status]
        for i in die_disk:
            with open(self.disk_path[i], 'ab+') as f:
                # ipdb.set_trace()
                # start_p = f.tell()
                byte_data = struct.pack('<'+str(len(enc_str[:, i]))+self.pack_m[self.chunk_size], *enc_str[:, i].tolist())
                # byte_data = bytes(enc_str[:, i].tolist())
                f.write(byte_data)
    
    def process(self, mode, filename):
        if mode == "write":
            for file in filename:
                self.reset()
                self.filename = file
                if sum(self.disk_status) < self.total_num_of_disk:
                    return [1, "Disk {} failed! Place replace and rebuild it first!".format(self.disk_name[~self.disk_status])]
                if file in self.files_info:
                    print("File with same name exist.")
                    # ipdb.set_trace()
                    return [2, "File with same name exist."]
                path = os.path.join(os.getcwd(), 'input_data', file) # real-file
                # path = os.path.join(os.getcwd(), 'test_data', file) # test-data
                self.read_from_system(path)
                self.splitter()
                self.write_to_disk()
            return [0, "Success!"]
        
        if mode == "read":
            for file in filename:
                self.reset()
                self.filename = file
                if file not in self.files_info:
                    print("Fail to find {} in RAID6 disk.".format(file))
                    return [3, "Fail to find {} in RAID6 disk.".format(file)]
                if self.num_check_disk < self.total_num_of_disk - sum(self.disk_status):
                    print("Critical Error! Data cannot be restored.")
                    return [4, "Critical Error! Data cannot be restored."]
                if sum(self.disk_status) < self.total_num_of_disk:
                    self.cal_A_i(self.total_num_of_disk, self.num_data_disk, self.disk_status)
                path = os.path.join(os.getcwd(), 'output_data', file)
                self.read_from_disk()
                self.combiner()
                self.write_to_system(path)
            return [0, "Success!"]
        
        if mode == "rebuild":
            if sum(self.disk_status) == self.total_num_of_disk:
                return [6, "Rest Assured! Your database is healthy!\n Nothing to rebuild."]
            if sum(self.disk_on) != self.total_num_of_disk:
                missing_disk = self.disk_name[~self.disk_on]
                return[5, "\n\tPlease replace the fail disk \n\t{}".format(missing_disk)]
            self.cal_A_i(self.total_num_of_disk, self.num_data_disk, self.disk_status)
            for file in filename:
                self.reset()
                self.filename = file
                self.read_from_disk()
                self.rebuild_disk()
            self.disk_status[~self.disk_status] = True
            return [0, "Success!"]
        

    
if __name__ == "__main__":
    # test case
    rd6 = RAID6(w=4, n=6, m=2)
    pw = rd6.encode(np.array([[13, 14, 15, 10, 11, 12]], dtype=int).T)
    print(rd6.decode(pw[:6]))
    
    rd6 = RAID6(w=8, n=6, m=2)
    pw = rd6.encode(np.array([[32, 12, 24, 47, 10, 22]], dtype=int).T)
    print(rd6.decode(pw[:6]))
    
    rd6 = RAID6(w=16, n=8, m=2)
    pw = rd6.encode(np.array([[543, 1231, 23425, 33, 765, 41435, 214, 27383]], dtype=int).T)
    print(rd6.decode(pw[:8]))
    
    cont = Controller()
    cont.process(mode="write", filename=["colorbar_bi.png"])
    cont.process(mode="read", filename=["colorbar_bi.png"])
    cont.save_system_info()
