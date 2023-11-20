import numpy as np
import copy
import ipdb

class GaloisField:
    def __init__(self, w) -> None:
        """_summary_

        Args:
            w (int): word bit length
        """
        self.w = w
        self.max_mask = 2**w
        if self.w == 4:
            # x^4 + x + 1
            self.prim_poly = 0b10011
            self.gflog = np.zeros(self.max_mask)
            self.gfilog = np.zeros(self.max_mask)            
        elif self.w == 8:
            # x^8 + x^4 + x^3 + x^2 + 1
            self.prim_poly = 0b100011101
            self.gflog = np.zeros(self.max_mask, dtype=int)
            self.gfilog = np.zeros(self.max_mask, dtype=int)
        elif self.w == 16:
            # x^16 + x^12 + x^3 + x + 1
            self.prim_poly = 0b10001000000001011
            self.gflog = np.zeros(self.max_mask, dtype=int)
            self.gfilog = np.zeros(self.max_mask, dtype=int)
        self.gen_tables()

    def gen_tables(self):
        """generate logarithm look-up table for speed-up
        """
        dec = 1
        for log in range(0, self.max_mask-1):
            self.gflog[dec] = int(log)
            self.gfilog[log] = int(dec)
            dec <<= 1
            if(dec >= self.max_mask): dec = (dec ^ self.prim_poly) & (self.max_mask - 1)
           
    def add(self, a, b):
        """GF add

        Args:
            a (int): input a
            b (int): input b

        Returns:
            int: return c
        """
        return a ^ b # add is XOR
    
    def sub(self, a, b):
        """GF sub

        Args:
            a (int): input a
            b (int): input b
            
        Returns:
            int: return c
        """
        return self.add(a, b) # same to add
        
    def multiply(self, a, b):
        """GF multiply

        Args:
            a (int): input a
            b (int): input b

        Returns:
            int: return c
        """
        if a == 0 or b == 0:
            return 0
        
        log_sum = int((self.gflog[a] + self.gflog[b]) % (self.max_mask - 1)) # in case value overflow
        # ipdb.set_trace()
        return int(self.gfilog[log_sum]) # lookup table method
    
    def division(self, a, b):
        """GF division

        Args:
            a (int): input a
            b (int): input b

        Returns:
            int: return c
        """
        if a == 0:
            return 0
        if b == 0:
            return -1
        # try:
        # ipdb.set_trace()
        log_minus = int((self.gflog[a] - self.gflog[b]) % (self.max_mask - 1)) # in case value overflow
        # except:
        #     ipdb.set_trace()
        return int(self.gfilog[log_minus])
    
    def pow(self, a, i):
        """GF power

        Args:
            a (int): input power base
            i (int): input power index

        Returns:
            int: output s_out
        """
        if a == 0 and i != 0:
            return 0
        
        s_out = 1
        for k in range(i):
            s_out = self.multiply(s_out, a)
        return s_out
    
    def vec_sum(self, v_a):
        """GF sum of vector

        Args:
            v_a (list or nparray): input v_a

        Returns:
            int: output s_out
        """
        s_out = 0
        for i in v_a:
            s_out = self.add(s_out, i)
        return s_out
    
    def vec_dot(self, v_a, v_b):
        """GF vector inner product

        Args:
            i_a (list or nparray): input vector a
            i_b (list or nparray): input vector b

        Returns:
            int: output c
        """
        # v_a = copy.deepcopy(i_a)
        # v_b = copy.deepcopy(i_b)
        assert len(v_a) == len(v_b)
        if type(v_a) == list:
            v_a = np.array(v_a)
        if type(v_b) == list:
            v_b = np.array(v_b)
        log_sum = ((self.gflog[v_a] + self.gflog[v_b]) % (self.max_mask - 1)).astype(int)
        v_c = (self.gfilog[log_sum]).astype(int)
        if any(v_a * v_b == 0): # filter out zero multiply
            zero_idx = ~v_a.astype(bool) | ~v_b.astype(bool)
            v_c[zero_idx] = 0
        return np.bitwise_xor.reduce(v_c)
     
    def matrix_multiply(self, m_a, m_b):
        """GF matrix multiply

        Args:
            m_a (nparray): NxM input m_a
            m_b (nparray): MxK input m_b

        Returns:
            nparray: NxK output m_c
        """
        # ipdb.set_trace()
        assert m_a.shape[1] == m_b.shape[0]
        m_c = np.zeros([m_a.shape[0], m_b.shape[1]], dtype=int)
        for i in range(m_a.shape[0]):
            for j in range(m_b.shape[1]):
                # ipdb.set_trace()
                m_c[i, j] = self.vec_dot(m_a[i, :], m_b[:, j])
        return m_c
    
    def matrix_inverse(self, i_a): 
        """GF matrix invers using Gauss-Jordan Method
        Matrix singularity is not checked here coz Vandermonde Matrix
        is designed to be non-singular

        Args:
            i_a (nparray): NxN input i_a

        Returns:
            nparray: NxN output m_i
        """
        m_a = copy.deepcopy(i_a)
        assert m_a.shape[0] == m_a.shape[1]
        len_a = len(m_a)
        m_i = np.eye(len_a, dtype=int)
        row_idx = list(range(len_a))
        for d_idx in row_idx: # now use the idx_th row
            # print(m_a)
            while m_a[d_idx, d_idx] == 0:
                m_a = np.vstack([m_a, m_a[d_idx, :]])
                m_a = np.delete(m_a, d_idx, 0)
                m_i = np.vstack([m_i, m_i[d_idx, :]])
                m_i = np.delete(m_i, d_idx, 0)
            # print(m_a)
            # ipdb.set_trace()
            div_ratio = m_a[d_idx, d_idx]
            for j in range(len_a): # scale this row
                # print(m_a[d_idx, j], div_ratio)
                # print(m_i[d_idx, j], div_ratio)
                m_a[d_idx, j] = self.division(m_a[d_idx, j], div_ratio) 
                m_i[d_idx, j] = self.division(m_i[d_idx, j], div_ratio) 
            for i in row_idx[:d_idx]+row_idx[d_idx+1:]: # scale other row
                sub_ratio = m_a[i, d_idx]
                for j in range(len_a):
                    m_a[i, j] = self.sub(m_a[i, j], self.multiply(sub_ratio, m_a[d_idx, j])) 
                    m_i[i, j] = self.sub(m_i[i, j], self.multiply(sub_ratio, m_i[d_idx, j]))                   
            
        # check inverse consistency
        if (self.matrix_multiply(m_i, i_a) != np.eye(len(m_a))).any():
            print("Inverse result not consist. Input array may be singular!")
        return m_i   
            
if __name__ == "__main__":
    # test case
    gf = GaloisField(w = 4)
    print(gf.gflog)
    print(gf.gfilog)
    print(gf.multiply(3, 7)) # =9
    print(gf.multiply(13, 10)) # =11
    print(gf.division(13, 10)) # =3
    print(gf.division(3, 7)) # =10
    print(gf.vec_sum([9, 11, 0, 0]))
    print(gf.vec_dot([3, 13, 0, 3], [7, 10, 7, 0])) # =[9, 11, 0, 0]
    print(gf.matrix_inverse(np.array([[1, 0, 0], [1, 1, 1], [1, 2, 3]], dtype=int))) # [[1, 0, 0], [2, 3, 1], [3, 2, 1]]
    
    # gf = GaloisField(w = 8)
    # print(gf.gflog)
    # print(gf.gfilog)
    # # print(gf.division(0, 4)) # =3
    # print(gf.division(1, 4)) # =10