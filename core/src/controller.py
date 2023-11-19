import numpy as np
import copy
import ipdb
from GaloisField import GaloisField

class RAID6(GaloisField):
    def __init__(self, w, n, m) -> None:
        super().__init__(w = w)
        self.disk_num = n
        self.check_num = m
        self.F = np.zeros([m, n], dtype=int)
        for i in range(0, m):
            for j in range(1, n+1):
                self.F[i, j-1] = j ** i
        self.A = np.vstack([np.eye(n, dtype=int), self.F])
    
    def encode(self, bit_str):
        return self.matrix_multiply(self.A, bit_str)
    
    def decode(self, bit_str):
        # ipdb.set_trace()
        A_i = self.matrix_inverse(self.A[:self.disk_num, :])
        return self.matrix_multiply(A_i, bit_str[:self.disk_num, :])
    
class Controller:
    def __init__(self) -> None:
        pass
    
    def splitter(self):
        pass
    
    def combiner(self):
        pass
    
    
if __name__ == "__main__":
    # test case
    rd6 = RAID6(w=8, n=6, m=2)
    # test_arr = np.array([[1, 0, 0], [1, 1, 1], [1, 2, 3]], dtype=int)
    # result = rd6.matrix_inverse(test_arr) # [[1, 0, 0], [2, 3, 1], [3, 2, 1]]
    pw = rd6.encode(np.array([[32, 12, 24, 47, 10, 22]], dtype=int).T)
    result = rd6.decode(pw)
    print(result)