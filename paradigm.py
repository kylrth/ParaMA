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
        affix = ts.affix
        morph = ts.morph
        word = ts.token
        root = ts.root
        if affix.affix == '$':  # this is an atomic word
            atomic_word_dict[word] = ((word,), ((word, '$', '$'),))
            continue
        # this is a morphologically complex word
        if root in paradigm_dict:
            paradigm_dict[root].append((word, affix, morph))
        else:
            paradigm_dict[root] = [(word, affix, morph)]
    return paradigm_dict, atomic_word_dict


def get_paradigm_affix_sets(paradigm_dict):
    """For each root, collect the set of possible suffixes."""
    root_suffix_tuple_list = []
    for root, derived_word_list in paradigm_dict.items():
        # affixes are the second element; see create_paradigms.
        # we want to be transition-agnostic.
        affix_set = {x[1].copy(with_transition=False) for x in derived_word_list}
        root_suffix_tuple_list.append((root, affix_set))
    return root_suffix_tuple_list


def filter_rare_affix_from_affix_set(root_affix_set_list, min_freq):
    """Find affixes that occur with frequency less than `min_freq`, and remove them from all paradigms."""
    # collect the number of occurrences of each affix
    affix_dict = {}
    for root, affix_set in root_affix_set_list:
        for affix in affix_set:
            if affix in affix_dict:
                affix_dict[affix] += 1
            else: affix_dict[affix] = 1

    # filter the affixes with frequency less than `min_freq`
    filtered_affix_dict = {}
    for affix, freq in affix_dict.items():
        if freq < min_freq:
            continue
        filtered_affix_dict[affix] = freq

    # trim all of the infrequent affixes from each set
    filtered_root_affix_set_list = []
    for root, affix_set in root_affix_set_list:
        affix_list = []
        for affix in affix_set:
            if affix in filtered_affix_dict:
                affix_list.append(affix)
        if affix_list:
            filtered_root_affix_set_list.append((root, set(affix_list)))

    return filtered_root_affix_set_list


def stats_affix_sets(root_affix_set_list, word_dict):
    """Create a map from tuples of affixes in a paradigm to lists of roots supporting the paradigm, along with their
    frequencies. Discard roots that are deemed unreliable by is_reliable_root."""
    affix_tuple_dict = {}
    for root, affix_set in root_affix_set_list:
        freq = word_dict[root] if root in word_dict else 1
        if not is_reliable_root(root, freq):
            continue  # ensure we trust the root to be a root
        affix_tuple = tuple(sorted(affix_set))
        if affix_tuple in affix_tuple_dict:
            affix_tuple_dict[affix_tuple].append((root, freq))
        else:
            affix_tuple_dict[affix_tuple] = [(root, freq)]
    return affix_tuple_dict


def filter_affix_tuple(affix_tuple_dict, min_support, min_tuple_size):
    """Remove affix sets that don't meet the robustness or productivity requirements.

    Robustness requires the set of affixes to be greater than min_tuple_size, and productivity requires the support of
    the paradigm to be greater than min_support.
    """
    filtered_affix_tuple_dict = {}
    for affix_tuple, root_list in affix_tuple_dict.items():
        tuple_size = len(affix_tuple)
        if tuple_size < min_tuple_size:
            continue  # robustness requirement
        support = len(root_list)
        if support < min_support:
            continue  # productivity requirement
        long_affix_count = 0
        for affix in affix_tuple:
            if len(affix) > 1:
                long_affix_count += 1
        filtered_affix_tuple_dict[affix_tuple] = root_list
    return filtered_affix_tuple_dict


def stats_single_affix_type_freq(affix_tuple_dict):
    """Collect a frequency dictionary for affixes, where the frequency is the number of unique words the affix applies
    to."""
    affix_dict = {}
    for affix_tuple, root_list in affix_tuple_dict.items():
        freq = len(root_list)
        for affix in affix_tuple:
            if affix in affix_dict:
                affix_dict[affix] += freq
            else: affix_dict[affix] = freq
    return affix_dict


def get_single_affix_tuples(affix_type_dict, affix_tuple_dict):
    """Get just the paradigms with a single affix."""
    valid_singleton_dict = {}
    for affix_tuple in affix_tuple_dict:
        if len(affix_tuple) != 1:
            continue
        affix = affix_tuple[0]
        if affix not in affix_type_dict:
            continue
        valid_singleton_dict[affix_tuple] = affix_tuple_dict[affix_tuple]
    return valid_singleton_dict


def get_reliable_affix_tuples(root_affix_set_list, word_dict, min_support, min_tuple_size, min_affix_freq):
    """Get affix tuples (sets of affixes of a particular paradigm) where the requirements for reliability are met.

    Specifically, reliability requires:
        1. that the support of the paradigm be greater than or equal to `min_support` (productivity)
        2. that the number of affixes in the paradigm be greater than or equal to `min_tuple_size` (robustness)
        3. that the affix frequency be greater than or equal to `min_affix_freq` (frequency)

    Returns:
        (dict): the filtered affix tuple dict
        (dict): the paradigms with a single affix
        (dict): the productivity of each affix.
    """
    # filter for frequency
    root_affix_set_list = filter_rare_affix_from_affix_set(root_affix_set_list, min_affix_freq)

    # get the affix tuples along with the roots they modify
    affix_tuple_dict = stats_affix_sets(root_affix_set_list, word_dict)

    # filter for robustness and productivity
    filtered_affix_tuple_dict = filter_affix_tuple(affix_tuple_dict, min_support, min_tuple_size)

    # get the paradigms with a single affix
    affix_type_dict = stats_single_affix_type_freq(filtered_affix_tuple_dict)
    single_affix_tuple_dict = get_single_affix_tuples(affix_type_dict, affix_tuple_dict)

    return filtered_affix_tuple_dict, single_affix_tuple_dict, affix_type_dict
