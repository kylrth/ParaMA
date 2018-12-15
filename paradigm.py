'''
Created on Jun 11, 2018

@author: xh
'''


from reliableroot import is_reliable_root


def create_paradigms(token_structs):
    """Create a dictionary of paradigms (maps from roots to their possible affixated forms).
    
    Also collect a dictionary of atomic words.
    """
    atomic_word_dict = {}
    paradigm_dict = {}
    for ts in token_structs:
        suffix = ts.suffix
        morph = ts.morph
        word = ts.token
        root = ts.root
        trans = ts.trans
        if suffix == '$':  # this is an atomic word
            atomic_word_dict[word] =  ((word,),((word, '$', '$'),))
            continue
        # this is a morphologically complex word
        if root in paradigm_dict: paradigm_dict[root].append((word, trans, suffix, morph))
        else: paradigm_dict[root] = [(word, trans, suffix, morph)]
    return paradigm_dict, atomic_word_dict


def get_paradigm_suffix_sets(paradigm_dict):
    """For each root, collect the set of possible suffixes."""
    root_suffix_tuple_list = []
    for root, derived_word_list in paradigm_dict.items():
        suffix_set = set([x[2] for x in derived_word_list])  # suffixes are the second element; see create_paradigms
        root_suffix_tuple_list.append((root, suffix_set))
    return root_suffix_tuple_list


def filter_rare_suffix_from_suffix_set(root_suffix_set_list, min_freq):
    """Find suffixes that occur with frequency less than `min_freq`, and remove them from all paradigms."""
    # collect the number of occurrences of each suffix
    suffix_dict = {}
    for root, suffix_set in root_suffix_set_list:
        for suffix in suffix_set: 
            if suffix in suffix_dict: suffix_dict[suffix] += 1
            else: suffix_dict[suffix] = 1
    
    # filter the suffixes with frequency less than `min_freq`
    filtered_suffix_dict = {}
    for suffix, freq in suffix_dict.items():
        if freq < min_freq: continue
        filtered_suffix_dict[suffix] = freq
    
    # trim all of the infrequent suffixes from each set
    filtered_root_suffix_set_list = []
    for root, suffix_set in root_suffix_set_list:
        suffix_list = []
        for suffix in suffix_set:
            if suffix in filtered_suffix_dict: suffix_list.append(suffix)
        if len(suffix_list) > 0:
            filtered_root_suffix_set_list.append((root, set(suffix_list)))
    
    return filtered_root_suffix_set_list


def stats_suffix_sets(root_suffix_set_list, word_dict):
    """Create a map from tuples of suffixes in a paradigm to lists of roots supporting the paradigm, along with their
    frequencies. Discard roots that are deemed unreliable by is_reliable_root."""
    suffix_tuple_dict = {}
    for root, suffix_set in root_suffix_set_list:
        freq = word_dict[root] if root in word_dict else 1
        if not is_reliable_root(root, freq): continue  # ensure we trust the root to be a root
        suffix_tuple = tuple(sorted(suffix_set))
        if suffix_tuple in suffix_tuple_dict: suffix_tuple_dict[suffix_tuple].append((root, freq))
        else: suffix_tuple_dict[suffix_tuple] = [(root, freq)]
    return suffix_tuple_dict


def filter_suffix_tuple(suffix_tuple_dict, min_support, min_tuple_size):
    """Remove suffix sets that don't meet the robustness or productivity requirements.
    
    Robustness requires the set of suffixes to be greater than min_tuple_size, and productivity requires the support of
    the paradigm to be greater than min_support.
    """
    filtered_suffix_tuple_dict = {}
    for suffix_tuple, root_list in suffix_tuple_dict.items():
        tuple_size = len(suffix_tuple) 
        if tuple_size < min_tuple_size: continue  # robustness requirement
        support = len(root_list)
        if support < min_support: continue  # productivity requirement
        long_suffix_count = 0
        for suffix in suffix_tuple:
            if len(suffix) > 1: long_suffix_count += 1
        filtered_suffix_tuple_dict[suffix_tuple] = root_list
    return filtered_suffix_tuple_dict


def stats_single_suffix_type_freq(suffix_tuple_dict):
    """Collect a frequency dictionary for suffixes, where the frequency is the number of words the suffix applies to."""
    suffix_dict = {}
    for suffix_tuple, root_list in suffix_tuple_dict.items():
        freq = len(root_list)
        for suffix in suffix_tuple:
            if suffix in suffix_dict: suffix_dict[suffix] += freq
            else: suffix_dict[suffix] = freq
    return suffix_dict


def get_single_suffix_tuples(suffix_type_dict, suffix_tuple_dict):
    """Get just the paradigms with a single suffix."""
    valid_singleton_dict = {}
    for suffix_tuple in suffix_tuple_dict:
        if len(suffix_tuple) != 1: continue
        suffix = suffix_tuple[0]
        if not suffix in suffix_type_dict: continue
        valid_singleton_dict[suffix_tuple] = suffix_tuple_dict[suffix_tuple]
    return valid_singleton_dict


def get_reliable_suffix_tuples(root_suffix_set_list, word_dict, min_support, min_tuple_size, min_suffix_freq):
    """Gets suffix tuples (sets of suffixes of a particular paradigm) where the requirements for reliability are met.
    
    Specifically, reliability requires:
        1. that the support of the paradigm be greater than or equal to `min_support` (productivity)
        2. that the number of suffixes in the paradigm be greater than or equal to `min_tuple_size` (robustness)
        3. that the suffix frequency be greater than or equal to `min_suffix_freq` (frequency)
    
    Returns:
        (dict): the filtered suffix tuple dict
        (dict): just the paradigms with a single suffix
        (dict): the productivity of each suffix.
    """
    # filter for frequency
    root_suffix_set_list = filter_rare_suffix_from_suffix_set(root_suffix_set_list, min_suffix_freq)

    # get the suffix tuples along with the roots they modify
    suffix_tuple_dict = stats_suffix_sets(root_suffix_set_list, word_dict)

    # filter for robustness and productivity
    filtered_suffix_tuple_dict = filter_suffix_tuple(suffix_tuple_dict, min_support, min_tuple_size)

    # get the paradigms with a single suffix
    suffix_type_dict = stats_single_suffix_type_freq(filtered_suffix_tuple_dict)
    single_suffix_tuple_dict = get_single_suffix_tuples(suffix_type_dict, suffix_tuple_dict)

    return filtered_suffix_tuple_dict, single_suffix_tuple_dict, suffix_type_dict
