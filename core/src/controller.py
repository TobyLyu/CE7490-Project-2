import numpy as np
import copy
import ipdb
from GaloisField import GaloisField

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
        assert self.A.shape[1] == len(bit_str)
        return self.matrix_multiply(self.A, bit_str)
    
    def decode(self, bit_str, use_disk):
        """decode the input bit string from data or checksum

        Args:
            bit_str (Nx1): encoded input string
            use_disk (list or nparray): 1xN list of disk available

        Returns:
            nparray: decoded output
        """
        A_i = self.matrix_inverse(self.A[use_disk, :])
        return self.matrix_multiply(A_i, bit_str[use_disk, :])
    
class Controller:
    def __init__(self) -> None:
        pass
    
    def splitter(self):
        pass
    
    def combiner(self):
        pass
    
    
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