'''
Created on Jun 11, 2018

@author: xh
'''

def is_reliable_root(root, freq):
    """Determines whether a root is reliable given its frequency and length.
    
    Works on the idea that roots tend to have a minimum length (referred to in section 4.1 paragraph 1 in the paper),
    and that longer proposed roots are more likely to be real. Thus, we require less evidence to support their reality.
    """
    root_len = len(root)
    if root_len < 3: return False
    if root_len == 3 and freq < 2000: return False
    if root_len == 4 and freq < 200: return False
    if root_len == 5 and freq < 20: return False
    if root_len == 6 and freq < 10: return False
    if freq < 3: return False
    return True















