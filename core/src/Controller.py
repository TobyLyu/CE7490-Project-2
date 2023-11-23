import numpy as np
import copy
import ipdb
import struct
from core.src.GaloisField import GaloisField
from core.src.Monitor import Monitor
# from GaloisField import GaloisField
# from Monitor import Monitor
from threading import Thread
from multiprocessing import Process, Queue, Manager
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
        self.disk_num = self.data_num + self.check_num
        self.F = np.zeros([m, n], dtype=int)
        for i in range(0, m):
            for j in range(1, n+1):
                self.F[i, j-1] = self.pow(j, i)
        self.A = np.vstack([np.eye(n, dtype=int), self.F])
    
    # def encode(self, bit_in, result = [None], index = 0):
    def encode(self, bit_in, use_que, queue_in, queue_out):
        """encode the input bit string with checksum

        Args:
            bit_str (nparray): N x {stripe_len} input data

        Returns:
            nparray: encoded output with checksum
        """
        
        # print(result)
        if use_que: bit_in = queue_in.get()
        if len(bit_in) == 0:
            # result[index]  = []
            if use_que: queue_out.put([])
            return []
        
        # ipdb.set_trace()
        # print(bit_in)
        assert self.A.shape[1] == bit_in.shape[1]
        # bit_str = copy.deepcopy(bit_in)
        bit_str = bit_in
        # this calculation is slow and think the above I matrix is not necessary
        # self.matrix_multiply(self.A, bit_in)
        # return self.matrix_multiply(self.A, bit_in)
        
        # so we only ccalculate the checksum bit only
        check_bit = self.matrix_multiply(self.A[-self.check_num:, :], bit_str.T).T
        enc_str = np.hstack([bit_str, check_bit])
        for idx, enc in enumerate(enc_str):
            enc_str[idx, :] = np.roll(enc, -(idx % self.disk_num)) # save checksum into all disks
        # result[index] = enc_str
        if use_que: queue_out.put(enc_str)
        # return np.hstack([bit_str.T, check_bit.T]).T
        return enc_str
        
    
    # def decode(self, bit_in, disk_status, result = [None], index = 0):
    def decode(self,  bit_in, disk_status, use_que, queue_in, queue_out):
        
        if use_que: [bit_in, disk_status] = queue_in.get()
        if len(bit_in) == 0:
            # result[index]  = []
            if use_que: queue_out.put([])
            return []
        
        # print(bit_in.shape[0])
        
        bit_str = copy.deepcopy(bit_in)
        enc_str = np.zeros([bit_str.shape[0], self.num_data_disk], dtype=int)
        for idx, enc in enumerate(bit_str):
            roll_n = idx % self.total_num_of_disk
            # ipdb.set_trace()
            enc_str[idx, :] = np.roll(bit_str[idx, :], roll_n)[np.roll(disk_status, roll_n)][:self.data_num]
            
            # bit_str[idx, :] = np.roll(enc, (idx % self.disk_num)) # save checksum into all disks

        
        if all(disk_status):
            # result[index]  = enc_str
            pass
        else:
            enc_str = self.restore(enc_str)
        
        # result[index] = self.restore(enc_str)
        # result[index] = bit_str
        if use_que: queue_out.put(enc_str)
        return enc_str
    
    def cal_A_i(self, disk_status):
        self.A_i_lst = []
        for i in range(self.disk_num):
            roll_n = i % self.disk_num
            # ipdb.set_trace()
            self.A_i_lst.append(self.matrix_inverse(self.A[np.roll(disk_status, roll_n), :][:self.data_num, :]))
        
    
    def restore(self, bit_in):
        """decode the input bit string from data or checksum

        Args:
            bit_str (N x strape_len): encoded input string
            use_disk (list or nparray): 1xN list of disk available

        Returns:
            nparray: decoded output
        """
        # ipdb.set_trace()
        # assert bit_str.shape[0] == len(use_disk)
        # if type(use_disk) == list:
        #     use_disk = np.array(use_disk, dtype = int)
        # use_disk -= 1
        # A_i = self.matrix_inverse(self.A[use_disk, :])
        # return self.matrix_multiply(A_i, bit_str)
        
        bit_str = bit_in
        
        assert bit_str.shape[1] == self.A.shape[1]
        
        output = np.zeros([bit_str.shape[0], self.data_num], dtype=int)
        for i in range(bit_str.shape[0]):
            roll_n = i % self.disk_num
            # ipdb.set_trace()
            output[i, :] = self.matrix_multiply(self.A_i_lst[roll_n], bit_str[i, :].reshape(-1, 1)).reshape(-1)
        
        return output
        
    
    def update(self, bit_str):
        pass
    
    
    
class Controller(Monitor, RAID6):
    def __init__(self) -> None:
        Monitor.__init__(self)
        RAID6.__init__(self, w=int(8*self.chunk_size), n=self.num_data_disk, m=self.num_check_disk)
        self.__content_cache = []
        self.pack_m = ['c', 'B', 'H', 'L', 'Q']
        self.thread_num = 16
        self.block_size_thre = 31250
    
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

        enc_str = np.zeros([stripe_len, self.total_num_of_disk], dtype=int)
        # enc_str = np.zeros([stripe_len, self.num_data_disk], dtype=int)
        for idx in range(self.total_num_of_disk):
            if not self.disk_status[idx]:
                continue
            else:
                with open(self.disk_path[idx], 'rb') as f:
                    f.seek(start_p, 0)
                    # enc_str[:, idx] = list(f.read(stripe_len))    
                    byte_data = f.read(stripe_len * self.chunk_size) 
                    # print(len(byte_data))
                    enc_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)            
        # for idx in range(stripe_len):
        #     roll_n = idx % self.total_num_of_disk
        #     # ipdb.set_trace()
        #     enc_str[idx, :] = np.roll(tmp_str[idx, :], roll_n)[np.roll(self.disk_status, roll_n)][:self.num_data_disk]
            
        # print(enc_str)
        # if all(self.disk_status):
        #     self.__content_cache = enc_str
        # else:

        # print(enc_str.shape)

        # ipdb.set_trace()
        if len(enc_str) % (self.thread_num * self.total_num_of_disk) == 0:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        # print(block_size)
        if block_size < self.block_size_thre:
            self.__content_cache = self.decode(enc_str, self.disk_status, False, "", "")
        else:
            threads = [None] * self.thread_num
            results = [None] * self.thread_num
            queue_in = [Manager().Queue()] * self.thread_num
            queue_out = [Manager().Queue()] * self.thread_num
            for i in range(self.thread_num):
                block = enc_str[block_size*i:min(enc_str.shape[0], block_size*(i+1)), :]
                # results[i] = ShareableList([" "*block.nbytes/block.size for _ in range(block.size)])
                # threads[i] = Process(target=self.decode, args=(enc_str[block_size*i:min(enc_str.shape[0], block_size*(i+1)), :], 
                                                            # self.disk_status, results[i], i, ))
                threads[i] = Process(target=self.decode, args=("", "", True, queue_in[i],queue_out[i]))
                queue_in[i].put([block, self.disk_status ])
                threads[i].start()
            
            
            for i in range(self.thread_num):
                results[i] = queue_out[i].get()
                threads[i].join()
                
            self.__content_cache = np.vstack([result for result in results if len(result)])
        
        # print(self.__content_cache)
    
    def write_to_disk(self):
        
        # results = [None] * self.thread_num

        if not len(self.__content_cache) % (self.thread_num * self.total_num_of_disk):
            block_size = self.stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = self.stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        if block_size < self.block_size_thre:
            enc_str = self.encode(self.__content_cache, False, "", "")
        else:
            threads = [None] * self.thread_num
            results = [None] * self.thread_num
            queue_in = [Manager().Queue()] * self.thread_num
            queue_out = [Manager().Queue()] * self.thread_num
            for i in range(self.thread_num):
                block = self.__content_cache[block_size*i:min(self.__content_cache.shape[0], block_size*(i+1)), :]
                threads[i] = Process(target=self.encode, args=("", True, queue_in[i], queue_out[i]))
                queue_in[i].put(block)
                threads[i].start()
            
            
            for i in range(self.thread_num):
                results[i] = queue_out[i].get()
                threads[i].join()
                
            enc_str = np.vstack([result for result in results if len(result)])

        
        # print(len(enc_str))
        # enc_str = self.encode(self.__content_cache.T).T
        # print(enc_str)

        
        # print(enc_str)
        for i in range(self.total_num_of_disk):
            with open(self.disk_path[i], 'ab+') as f:
                start_p = f.tell()
                byte_data = struct.pack('<'+str(len(enc_str[:, i]))+self.pack_m[self.chunk_size], *enc_str[:, i].tolist())
                # byte_data = bytes(enc_str[:, i].tolist())
                # print(len(byte_data))
                f.write(byte_data)
        
        self.files_info[self.filename] = [str(start_p), str(self.stripe_len), str(self.content_len)]
        with open(self.files_info_path, 'a+') as f:
            f.writelines([self.filename, ',', str(start_p), ',',  str(self.stripe_len), ',', str(self.content_len), '\n'])
    
    def splitter(self):
        """split the whole file into different disk partition
        """
        if self.content_len % self.num_data_disk == 0:
            self.stripe_len = self.content_len // self.num_data_disk
        else:
            self.stripe_len = self.content_len // self.num_data_disk + 1
        self.__content_cache = self.__content_cache + [0] * (self.stripe_len * self.num_data_disk - self.content_len)
        self.__content_cache = np.asarray(self.__content_cache).astype(int).reshape([self.stripe_len, self.num_data_disk])
        # print(self.__content_cache)
        
        # print(self.__content_cache)
        
        # print(self.__content_cache.shape)
    
    def combiner(self):
        content_len = int(self.files_info[self.filename][2])
        # print(self.__content_cache.shape)
        # print(self.__content_cache)
        self.__content_cache = self.__content_cache.reshape(-1)
        self.__content_cache = self.__content_cache[:content_len].tolist()
        # print(self.__content_cache[:10])
    
    def rebuild_disk(self):

        # results = [None] * self.thread_num
        start_p = int(self.files_info[self.filename][0])
        stripe_len = int(self.files_info[self.filename][1])
        
        if not len(self.__content_cache) % (self.thread_num * self.total_num_of_disk):
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        if block_size < self.block_size_thre:
            enc_str = self.encode(self.__content_cache, False, "", "")
        else:
            threads = [None] * self.thread_num
            results = [None] * self.thread_num
            queue_in = [Manager().Queue()] * self.thread_num
            queue_out = [Manager().Queue()] * self.thread_num
            for i in range(self.thread_num):
                block = self.__content_cache[block_size*i:min(self.__content_cache.shape[0], block_size*(i+1)), :]
                threads[i] = Process(target=self.encode, args=("", True, queue_in[i], queue_out[i]))
                queue_in[i].put(block)
                threads[i].start()
            
            
            for i in range(self.thread_num):
                results[i] = queue_out[i].get()
                threads[i].join()
                
            enc_str = np.vstack([result for result in results if len(result)])

        # enc_str = self.encode(self.__content_cache)
        
        # for idx, enc in enumerate(enc_str):
        #     enc_str[idx, :] = np.roll(enc, -(idx % self.total_num_of_disk)) # save checksum into all disks
        
        die_disk = np.arange(0, self.total_num_of_disk)[~self.disk_status]
        for i in die_disk:
            with open(self.disk_path[i], 'ab+') as f:
                # ipdb.set_trace()
                # start_p = f.tell()
                f.seek(start_p)
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
                    self.cal_A_i(self.disk_status)
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
            self.cal_A_i(self.disk_status)
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
