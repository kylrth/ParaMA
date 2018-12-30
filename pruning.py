'''
Created on Jun 11, 2018

@author: xh
'''


from tqdm import tqdm
from reliableroot import is_reliable_root


def get_suffix_type_score(affix_tuples):
    """Get the total number of roots where each affix can apply."""
    affix_type_dict = {}
    for affix_tuple, root_list in affix_tuples.items():
        for affix in affix_tuple:
            if affix in affix_type_dict:
                affix_type_dict[affix] += len(root_list)
            else: affix_type_dict[affix] = len(root_list)
    return affix_type_dict


def prune_affix_tuple(affix_tuple, affix_tuple_dict, affix_type_score):
    """Prunes unlikely affixes from affix_tuple.

    Keeps known sets of affixes, or if the affix_tuple is unknown, returns a combination of the three top-scoring known
    paradigms containing affixes from affix_tuple."""
    # if affix_tuple is a known affix tuple, keep it.
    if affix_tuple in affix_tuple_dict:
        return affix_tuple

    # if affix_tuple only has one element, prune the whole paradigm.
    if len(affix_tuple) == 1:
        return tuple()

    # get the list of known affix sets containing affixes from our affix_tuple
    satisfied_tuples = []
    affix_set = set(affix_tuple)
    for affix_tuple in affix_tuple_dict:
        satisfied_affix = []
        for affix in affix_tuple:
            if affix in affix_set:
                satisfied_affix.append(affix)
        if not satisfied_affix:
            continue
        satisfied_tuples.append(satisfied_affix)

    # if there are no known affixes in affix_tuple, prune the whole paradigm.
    if not satisfied_tuples:
        return tuple()

    # collect the scores of each known affix from the paradigms
    affix_tuple_score = []
    for affix_list in satisfied_tuples:
        score = 0
        for affix in affix_list:
            score += affix_type_score[affix]
        affix_tuple_score.append((affix_list, score))

    # return the set of known affixes from the top three scoring affix tuples
    sorted_affix_tuple_score = sorted(affix_tuple_score, key=lambda x: -x[1])
    e_indx = min(3, len(sorted_affix_tuple_score))
    affix_tuple_final = []
    for i in range(e_indx):
        affix_tuple_final.extend(sorted_affix_tuple_score[i][0])
    return tuple(sorted(set(affix_tuple_final)))


def prune_paradigms(paradigm_dict, reliable_affix_tuples, affix_type_score, single_affix_tuples, word_dict,
                    exclude_unreliable):
    """Prune paradigms based on specified conditions.

    Conditions to prune include:
        1. The word isn't in the list of known words.
        2. The word has an unreliable root.
        3. The paradigm only has one affix, but the affix isn't in the list of single_affix_tuples.
    """
    pruned_paradigm_dict = {}  # to stored paradigms that survive pruning
    root_affix_set_dict = {}  # to store roots with their affix set if they survive pruning
    pruned_words = []  # the "garbage can" of pruned words
    for word, derived_word_list in tqdm(paradigm_dict.items()):
        affix_set = set([x[1] for x in derived_word_list])
        affix_tuple = tuple(sorted(affix_set, key=lambda x: x.affix))

        # if the word isn't in the known list of words,
        if not word in word_dict:
            # prune it.
            for x in derived_word_list:
                pruned_word, root, affix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, affix))
            continue

        freq = word_dict[word]
        # if this is an unreliable root,
        root_unreliable = not is_reliable_root(word, freq)
        if exclude_unreliable and root_unreliable:
            # prune it.
            for x in derived_word_list:
                pruned_word, root, affix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, affix))
            continue
        if len(affix_tuple) == 1:  # if this paradigm only has one affix,
            # and if this paradigm was found in single_affix_tuples and the root is unreliable,
            if affix_tuple in single_affix_tuples and ((not exclude_unreliable) or root_unreliable):
                # keep it.
                pruned_paradigm_dict[word] = derived_word_list.copy()
                root_affix_set_dict[word] = affix_set
                continue
            # Otherwise, prune it.
            # get the only possible derived word (since there's only one suffix to add)
            pruned_word, root, affix = derived_word_list[0][0], word, derived_word_list[0][2]
            pruned_words.append((pruned_word, root, affix))
            continue

        # prune unlikely affixes
        rem_tuple = prune_affix_tuple(affix_tuple, reliable_affix_tuples, affix_type_score)
        rem_set = set(rem_tuple)
        # if there were no likely affixes in the set,
        if not rem_set:
            # prune it.
            for x in derived_word_list:
                pruned_word, root, affix = x[0], word, x[2]
                pruned_words.append((pruned_word, root, affix))
            continue

        # Otherwise, some affixes were likely. Create a new derived_word_list using only the pruned affixes.
        derived_word_list_1 = []
        for derived_word, affix, morph in derived_word_list:
            if affix in rem_set:  # If the affix was likely,
                # add it.
                derived_word_list_1.append((derived_word, affix, morph))
                continue
            # Otherwise, prune it.
            pruned_words.append((derived_word, word, affix))

        if derived_word_list_1:
            # record the transformations that survived,
            pruned_paradigm_dict[word] = derived_word_list_1
            # as well as the set of likely affixes.
            root_affix_set_dict[word] = rem_set
    return pruned_paradigm_dict
