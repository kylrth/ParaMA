'''
Created on Jun 11, 2018

@author: xh
'''

from reliableroot import is_reliable_root
from tqdm import tqdm

def get_suffix_type_score(suffix_tuples):
    """Get the total number of roots where each suffix can apply."""
    suffix_type_dict = {}
    for suffix_tuple, root_list in suffix_tuples.items():
        for suffix in suffix_tuple:
            if suffix in suffix_type_dict: suffix_type_dict[suffix] += len(root_list)
            else: suffix_type_dict[suffix] = len(root_list)
    return suffix_type_dict

def prune_suffix_tuple(suffix_tuple, suffix_tuple_dict, suffix_type_score):
    """Prunes unlikely suffixes from suffix_tuple.
    
    Keeps known sets of suffixes, or if the suffix_tuple is unknown, returns a combination of the three top-scoring
    known paradigms containing suffixes from suffix_tuple."""
    # if suffix_tuple is a known suffix tuple, keep it.
    if suffix_tuple in suffix_tuple_dict: return suffix_tuple
    
    # if suffix_tuple only has one element, prune the whole paradigm.
    if len(suffix_tuple) == 1: return tuple()
    
    # get the list of known suffix sets containing suffixes from our suffix_tuple
    satisfied_tuples = []
    suffix_set = set(suffix_tuple)
    for suffix_tuple in suffix_tuple_dict:
        satisfied_suffix = []
        for suffix in suffix_tuple:
            if suffix in suffix_set:
                satisfied_suffix.append(suffix)
        if len(satisfied_suffix) < 1: continue
        satisfied_tuples.append(satisfied_suffix)
    
    # if there are no known suffixes in suffix_tuple, prune the whole paradigm.
    if len(satisfied_tuples) == 0: return tuple()
    
    # collect the scores of each known suffix from the paradigms
    suffix_tuple_score = []
    for suffix_list in satisfied_tuples:
        score = 0
        for suffix in suffix_list:
            score += suffix_type_score[suffix]
        suffix_tuple_score.append((suffix_list, score))
    
    # return the set of known suffixes from the top three scoring suffix tuples
    sorted_suffix_tuple_score = sorted(suffix_tuple_score, key=lambda x: -x[1])
    e_indx = min(3, len(sorted_suffix_tuple_score))
    suffix_tuple_final = []
    for i in range(e_indx):
        suffix_tuple_final.extend(sorted_suffix_tuple_score[i][0])
    return tuple(sorted(set(suffix_tuple_final)))

def prune_paradigms(paradigm_dict, reliable_suffix_tuples, suffix_type_score, single_suffix_tuples, tokens_prob_segs_dict, word_dict, exclude_unreliable):
    """Prune paradigms based on specified conditions.
    
    Conditions to prune include:
        1. The word isn't in the list of known words.
        2. The word has an unreliable root.
        3. The paradigm only has one suffix, but the suffix isn't in the list of single_suffix_tuples.
    """
    pruned_paradigm_dict = {}  # to stored paradigms that survive pruning
    root_suffix_set_dict = {}  # to store roots with their suffix set if they survive pruning
    pruned_words = []  # the "garbage can" of pruned words
    for word, derived_word_list in tqdm(paradigm_dict.items()):
        suffix_set = set([x[2] for x in derived_word_list])
        suffix_tuple = tuple(sorted(suffix_set))

        # if the word isn't in the known list of words,
        if not word in word_dict:
            # prune it.
            for x in derived_word_list:
                pruned_word, root, suffix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, suffix))
            continue
        freq = word_dict[word]

        # if this is an unreliable root,
        root_unreliable = not is_reliable_root(word, freq)
        if exclude_unreliable and root_unreliable:
            # prune it.
            for x in derived_word_list:
                pruned_word, root, suffix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, suffix))
            continue
        if len(suffix_tuple) == 1:  # if this paradigm only has one suffix,
            # and if this paradigm was found in single_suffix_tuples and the root is unreliable,
            if suffix_tuple in single_suffix_tuples and ((not exclude_unreliable) or root_unreliable):
                # keep it.
                pruned_paradigm_dict[word] = derived_word_list.copy()
                root_suffix_set_dict[word] = suffix_set
                continue
            # Otherwise, prune it.
            # get the only possible derived word (since there's only one suffix to add)
            pruned_word, root, suffix = derived_word_list[0][0], word, derived_word_list[0][2]
            pruned_words.append((pruned_word, root, suffix))
            continue
        
        # prune unlikely suffixes
        rem_tuple = prune_suffix_tuple(suffix_tuple, reliable_suffix_tuples, suffix_type_score)
        rem_set = set(rem_tuple)
        # if there were no likely suffixes in the set,
        if (len(rem_set) < 1):
            # prune it.
            for x in derived_word_list:
                pruned_word, root, suffix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, suffix))
            continue
        
        # Otherwise, some suffixes were likely. Create a new derived_word_list using only the pruned suffixes.
        derived_word_list_1 = []
        for derived_word, trans, suffix, morph in derived_word_list:
            if suffix in rem_set:  # If the suffix was likely,
                # add it.
                derived_word_list_1.append((derived_word, trans, suffix, morph))
                continue
            # Otherwise, prune it.
            pruned_words.append((derived_word, word, suffix))
        
        if len(derived_word_list_1) > 0:
            # record the transformations that survived,
            pruned_paradigm_dict[word] = derived_word_list_1
            # as well as the set of likely suffixes.
            root_suffix_set_dict[word] = rem_set
    return pruned_paradigm_dict










