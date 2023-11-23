import numpy as np
import copy
import os
import struct
from core.src.GaloisField import GaloisField
from core.src.Monitor import Monitor
from multiprocessing import Process, Pipe



class RAID6(GaloisField):
    def __init__(self, w, n, m) -> None:
        """_summary_

        Args:
            w (int): word bit length / chunk size
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
    
    def encode(self, bit_in, use_que, queue_out):
        """encode the input bit string with checksum

        Args:
            bit_str (nparray): {data_num} x {stripe_len} input data
            use_que (bool): single core or multi core
            queue_out (Queue()): communication pipe

        Returns:
            nparray: {disk_num} x {stripe_len} encoded output with parity
        """
        
        if use_que: bit_in = queue_out.recv()
        if len(bit_in) == 0:
            if use_que: queue_out.send([])
            return []
        
        assert self.A.shape[1] == bit_in.shape[1]
        bit_str = bit_in
        
        # this calculation is slow and think the above I matrix is not necessary
        # self.matrix_multiply(self.A, bit_in)
        # return self.matrix_multiply(self.A, bit_in)
        
        # so we only ccalculate the checksum bit only
        check_bit = self.matrix_multiply(self.A[-self.check_num:, :], bit_str.T).T
        enc_str = np.hstack([bit_str, check_bit])
        for idx, enc in enumerate(enc_str):
            enc_str[idx, :] = np.roll(enc, -(idx % self.disk_num)) # save parity into all disks
            
        # output
        if use_que: queue_out.send(enc_str)
        return enc_str
        
    
    def decode(self,  bit_in, disk_status, use_que, queue_out):
        """_summary_

        Args:
            bit_in (nparray): {data_num} x {stripe_len} input data
            disk_status (nparray): current disk status
            use_que (bool): single core or multi core
            queue_out (Queue()): communication pipe

        Returns:
            nparray: {data_num} x {stripe_len} original
        """
        if use_que: [bit_in, disk_status] = queue_out.recv()
        if len(bit_in) == 0:
            if use_que: queue_out.send([])
            return []
        
        
        bit_str = copy.deepcopy(bit_in)
        enc_str = np.zeros([bit_str.shape[0], self.num_data_disk], dtype=int)
        for idx, enc in enumerate(bit_str):
            roll_n = idx % self.total_num_of_disk
            # restore the shifting
            enc_str[idx, :] = np.roll(bit_str[idx, :], roll_n)[np.roll(disk_status, roll_n)][:self.data_num]
        
        if all(disk_status): # all disk heathy, directly return
            pass
        else: # disk lost, restore from remaining
            enc_str = self.restore(enc_str)
        
        if use_que: queue_out.send(enc_str)
        return enc_str
    
    def cal_A_i(self, disk_status):
        """calculate inverse A matrix with selected rows

        Args:
            disk_status (nparray): current disk status
        """
        self.A_i_lst = []
        for i in range(self.disk_num):
            roll_n = i % self.disk_num
            self.A_i_lst.append(self.matrix_inverse(self.A[np.roll(disk_status, roll_n), :][:self.data_num, :]))
        
    
    def restore(self, bit_in):
        """restore all the data from data or checksum

        Args:
            bit_str (nparray): {data_num} x {strape_len" encoded input string
            use_disk (nparray): current disk status

        Returns:
            nparray: decoded output
        """
        
        bit_str = bit_in
        
        assert bit_str.shape[1] == self.A.shape[1]
        
        output = np.zeros([bit_str.shape[0], self.data_num], dtype=int)
        for i in range(bit_str.shape[0]):
            roll_n = i % self.disk_num
            output[i, :] = self.matrix_multiply(self.A_i_lst[roll_n], bit_str[i, :].reshape(-1, 1)).reshape(-1)
        
        return output
        
    
    def update(self, bit_str):
        # TODO
        pass
    
    
    
class Controller(Monitor, RAID6):
    def __init__(self) -> None:
        Monitor.__init__(self)
        RAID6.__init__(self, w=int(8*self.chunk_size), n=self.num_data_disk, m=self.num_check_disk)
        self.__content_cache = []
        self.pack_m = ['c', 'B', 'H', 'L', 'Q'] # B: Byte, H: 8 Bytes, L: 16 Bytes, Q: 32 Bytes
        self.thread_num = 16 # number of sub-process
        self.block_size_thre = [21600, 40800, 9600] # single/multi-process change threshold
    
    def reset(self):
        """reset all sensitive value
        """
        self.__content_cache = []
        self.stripe_len = 0
        self.content_len = 0
        self.filename = []

    
    def read_from_system(self, path):
        """read from user disk's file
        
        Args:
            path (str): file path
        """
        
        with open(path, "rb") as f:
            while True:
                data_chunk = f.read(self.chunk_size)
                if not data_chunk:
                    break
                self.__content_cache.append(int.from_bytes(data_chunk, "little"))
            
            self.content_len = len(self.__content_cache)
    
    def write_to_system(self, path):
        """write to user's disk

        Args:
            path (str): file path
        """
        with open(path, 'wb') as f:
            byte_data = struct.pack('<'+str(len(self.__content_cache))+self.pack_m[self.chunk_size], *self.__content_cache)
            f.write(byte_data)
    
    def read_from_disk(self):
        """read from RAID disk
        """
        ###### read ######
        # get file storage start address and length
        start_p = int(self.files_info[self.filename][0])
        stripe_len = int(self.files_info[self.filename][1])

        enc_str = np.zeros([stripe_len, self.total_num_of_disk], dtype=int)
        for idx in range(self.total_num_of_disk):
            if not self.disk_status[idx]: # skip lost disk
                continue
            else:
                with open(self.disk_path[idx], 'rb') as f:
                    f.seek(start_p, 0)
                    byte_data = f.read(stripe_len * self.chunk_size) 
                    enc_str[:, idx] = struct.unpack('<'+str(stripe_len)+self.pack_m[self.chunk_size], byte_data)            

        ###### decode ######
        # determine whether to engage multi-processing
        if len(enc_str) % (self.thread_num * self.total_num_of_disk) == 0:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        # use single-core if file is small
        if block_size < self.block_size_thre[1]:
            self.__content_cache = self.decode(enc_str, self.disk_status, False, "")
        else: # start multi-processing
            threads = [None] * self.thread_num
            results = [None] * self.thread_num       
            queue_in = [None] * self.thread_num
            queue_out = [None] * self.thread_num
            for i in range(self.thread_num):
                queue_in[i], queue_out[i] = Pipe()
            
            for i in range(self.thread_num):
                block = enc_str[block_size*i:min(enc_str.shape[0], block_size*(i+1)), :]
                threads[i] = Process(target=self.decode, args=("", "", True, queue_out[i]), daemon=True)
                threads[i].start()
                queue_in[i].send([block, self.disk_status ])
            
            for i in range(self.thread_num):
                results[i] = queue_in[i].recv()
                threads[i].join()
                
            self.__content_cache = np.vstack([result for result in results if len(result)])
        
    
    def write_to_disk(self):
        """write encoded file into RAID
        """
        ##### encode ######
        # determine whether to engage multi-processing
        if not len(self.__content_cache) % (self.thread_num * self.total_num_of_disk):
            block_size = self.stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = self.stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        # use single-core if file is small
        if block_size < self.block_size_thre[0]:
            enc_str = self.encode(self.__content_cache, False, "")
        else: # start multi-processing
            threads = [None] * self.thread_num
            results = [None] * self.thread_num
            queue_in = [None] * self.thread_num
            queue_out = [None] * self.thread_num
            for i in range(self.thread_num):
                queue_in[i], queue_out[i] = Pipe()
                
            for i in range(self.thread_num):
                block = self.__content_cache[block_size*i:min(self.__content_cache.shape[0], block_size*(i+1)), :]
                threads[i] = Process(target=self.encode, args=("", True, queue_out[i]), daemon=True)
                threads[i].start()
                queue_in[i].send(block)
            
            
            for i in range(self.thread_num):
                results[i] = queue_in[i].recv()
                threads[i].join()
                
            enc_str = np.vstack([result for result in results if len(result)])

        
        ###### write ######
        for i in range(self.total_num_of_disk):
            with open(self.disk_path[i], 'ab+') as f:
                start_p = f.tell()
                byte_data = struct.pack('<'+str(len(enc_str[:, i]))+self.pack_m[self.chunk_size], *enc_str[:, i].tolist())
                f.write(byte_data)
        
        # save file address and length
        self.files_info[self.filename] = [str(start_p), str(self.stripe_len), str(self.content_len)]
        with open(self.files_info_path, 'a+') as f:
            f.writelines([self.filename, ',', str(start_p), ',',  str(self.stripe_len), ',', str(self.content_len), '\n'])
    

    
    def rebuild_disk(self):
        """rebuild the RAID disks
        """
        ##### re-encode the data from recovered ######
        # get file storage start address and length
        start_p = int(self.files_info[self.filename][0])
        stripe_len = int(self.files_info[self.filename][1])
        # determine whether to engage multi-processing
        if not len(self.__content_cache) % (self.thread_num * self.total_num_of_disk):
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk)
            block_size = block_size * self.total_num_of_disk
        else:
            block_size = stripe_len // (self.thread_num * self.total_num_of_disk) + 1
            block_size = block_size * self.total_num_of_disk
        # use single-core if file is small
        if block_size < self.block_size_thre[2]:
            enc_str = self.encode(self.__content_cache, False, "")
        else: # start multi-processing
            threads = [None] * self.thread_num
            results = [None] * self.thread_num
            queue_in = [None] * self.thread_num
            queue_out = [None] * self.thread_num
            for i in range(self.thread_num):
                queue_in[i], queue_out[i] = Pipe()
                
            for i in range(self.thread_num):
                block = self.__content_cache[block_size*i:min(self.__content_cache.shape[0], block_size*(i+1)), :]
                threads[i] = Process(target=self.encode, args=("", True, queue_out[i]), daemon=True)
                threads[i].start()
                queue_in[i].send(block)
            
            for i in range(self.thread_num):
                results[i] = queue_in[i].recv()
                threads[i].join()
                
            enc_str = np.vstack([result for result in results if len(result)])

        ###### rewrite the data into RAID disk ######
        die_disk = np.arange(0, self.total_num_of_disk)[~self.disk_status]
        for i in die_disk:
            with open(self.disk_path[i], 'ab+') as f:
                f.seek(start_p)
                byte_data = struct.pack('<'+str(len(enc_str[:, i]))+self.pack_m[self.chunk_size], *enc_str[:, i].tolist())
                f.write(byte_data)
    
    def splitter(self):
        """split the whole file into different disk partition
        """
        if self.content_len % self.num_data_disk == 0:
            self.stripe_len = self.content_len // self.num_data_disk
        else:
            self.stripe_len = self.content_len // self.num_data_disk + 1
        # zero padding for row parity calculation
        self.__content_cache = self.__content_cache + [0] * (self.stripe_len * self.num_data_disk - self.content_len)
        self.__content_cache = np.asarray(self.__content_cache).astype(int).reshape([self.stripe_len, self.num_data_disk])

    
    def combiner(self):
        """combine the data from different disk into the whole file
        """
        content_len = int(self.files_info[self.filename][2])
        self.__content_cache = self.__content_cache.reshape(-1)
        # remove zero padding
        self.__content_cache = self.__content_cache[:content_len].tolist()
    
    def process(self, mode, filename):
        """response to GUI command

        Args:
            mode (str): "read" "write" "rebuild"
            filename (str): process which file

        Returns:
            int: error code
        """
        if mode == "write":
            for file in filename:
                self.reset()
                self.filename = file
                if sum(self.disk_status) < self.total_num_of_disk:
                    return [1, "Disk {} failed! Place replace and rebuild it first!".format(self.disk_name[~self.disk_status])]
                if file in self.files_info:
                    print("File with same name exist.")
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
