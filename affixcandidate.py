'''
Created on Jun 11, 2018

@author: xh
'''


import math
from tqdm import tqdm
from affix import Affix


def filter_affixes_by_freq(affix_dict, min_afx_freq):
    """Filter affix dictionary by a minimum affix frequency, where the frequency is a count of distinct stem-lengths."""
    if min_afx_freq <= 1:  # don't filter anything
        return affix_dict

    new_dict = {}
    for affix, stem_len_dist in affix_dict.items():
        count = sum(stem_len_dist.values())
        if count >= min_afx_freq:
            new_dict[affix] = stem_len_dist
    return new_dict


def group_affixes_by_stem_length(affixes):
    """Group the affixes by stem length, and find the length of the largest and smallest roots in the entire set."""
    min_root_len = 100
    max_root_len = 0
    groups = {}

    # sort through
    for afx, stem_len_dist in affixes.items():
        afx_len = len(afx.affix)
        if afx_len in groups:
            groups[afx_len].append((afx, stem_len_dist))
        else:
            groups[afx_len] = [(afx, stem_len_dist)]
        min_root_len, max_root_len = min(min_root_len, min(stem_len_dist)), max(max_root_len, max(stem_len_dist))

    return groups, min_root_len, max_root_len


def generate_candidates(words, min_stem_len, max_aff_len, min_affix_freq=1):
    """Collect possible affix candidates with a dictionary of stem lengths and frequencies (counts of distinct stem
    lengths).

    Optionally filter suffix candidates by minimum frequency.
    """
    affixes = {}
    for word in words:
        if len(word) <= min_stem_len:
            continue

        # test all possible prefix-stem combinations
        edge = max(min_stem_len, len(word) - max_aff_len)
        for i in range(1, len(word)):
            left = word[:i]
            right = word[i:]

            # if the right side is a word, save the prefix along with the length of the stem
            if len(right) >= edge and right in words:
                stem_len = len(right)
                left = Affix(left, 'pref')
                if left in affixes:
                    pref_len_dict = affixes[left]  # frequency dictionary of stem lengths for this prefix
                    if stem_len in pref_len_dict:
                        pref_len_dict[stem_len] += 1
                    else:
                        pref_len_dict[stem_len] = 1
                else:
                    affixes[left] = {stem_len: 1}

            # if the left side is a word, save the suffix along with the length of the stem
            if i >= edge and left in words:
                stem_len = len(left)
                right = Affix(right, 'suf')
                if right in affixes:
                    suf_len_dict = affixes[right]  # frequency dictionary of stem lengths for this suffix
                    if stem_len in suf_len_dict:
                        suf_len_dict[stem_len] += 1
                    else:
                        suf_len_dict[stem_len] = 1
                else:
                    affixes[right] = {stem_len: 1}

    # filter infrequent affixes
    return filter_affixes_by_freq(affixes, min_affix_freq)


def calc_expected_stem_len(affix_stem_len_dist, min_stem_len, max_stem_len):
    """Calculate the expected stem length (confidence value) of a suffix.

    This is equation (1) in the paper.
    """
    # smoothing by plus .001
    epi = 0.001
    afx_len_exp = []
    for afx, stem_len_dist in affix_stem_len_dist:
        count_sum = 0.0
        len_sum = 0.0
        for stem_len in range(min_stem_len, max_stem_len+1):
            count = epi
            if stem_len in stem_len_dist:
                count += stem_len_dist[stem_len]
            count_sum += count
            len_sum += stem_len * count
        len_exp = len_sum / count_sum
        afx_score = math.log10(1 + count_sum) * len_exp
        afx_len_exp.append((afx, afx_score, count_sum, len_exp))
    return afx_len_exp


def calc_affix_score_by_dist(paradigm_dict):
    """Get the score for each affix by calculating the expected length of its root."""
    affix_root_len_dist = {}
    min_root_len = 100
    max_root_len = 0
    # get the root length distribution for each affix
    for root, derived_word_list in paradigm_dict.items():
        root_len = len(root)
        min_root_len = min(min_root_len, root_len)  # eventually get the length of the smallest root
        max_root_len = max(max_root_len, root_len)  # eventually get the length of the longest root
        for _word, affix, _morph in derived_word_list:
            if (affix.affix, affix.kind) in affix_root_len_dist:
                # use the len_dist already calculated for this affix
                root_len_dist = affix_root_len_dist[(affix.affix, affix.kind)]
                if root_len in root_len_dist:
                    root_len_dist[root_len] += 1
                else:
                    root_len_dist[root_len] = 1
                # This wasn't here before, but I think it should be. (???)
                affix_root_len_dist[(affix.affix, affix.kind)] = root_len_dist
            else:
                # use a len_dist of 1 for this affix
                root_len_dist = {root_len:1}
                affix_root_len_dist[(affix.affix, affix.kind)] = root_len_dist

    # sort by affix
    affix_root_len_dist = sorted(affix_root_len_dist.items(), key=lambda x: x[0][0])
    # calculate the expected stem length
    affix_len_exp = calc_expected_stem_len(affix_root_len_dist, min_root_len, max_root_len)
    # use the stem length as a score for each affix
    affix_score_dict = dict([(affix, score) for affix, score, _count_sum, _len_exp in affix_len_exp])
    # return the score for each affix
    return affix_score_dict


def filter_affixes(affixes, top_N=50):
    """Return the `top_N` most likely affixes for each affix length.

    The list should be at most of length `top_N` * len(same_len_affix_dist).
    """
    filtered_affixes = []

    # get a dictionary mappings lengths to affixes of that length
    # also get the length of the largest and smallest roots
    affix_groups, min_root_len, max_root_len = group_affixes_by_stem_length(affixes)

    len_min = min(affix_groups.keys())
    len_max = max(affix_groups.keys())
    print('Root length range: (%s, %s)' % (len_min, len_max))

    pbar = tqdm(total=len_max - len_min)
    for _, affixes_and_dists in sorted(affix_groups.items(), key=lambda x: x[0]):
        # calculate affix confidence for each affix (equation 1 from the paper)
        affix_len_exp = calc_expected_stem_len(affixes_and_dists, min_root_len, max_root_len)
        affix_len_exp = sorted(affix_len_exp, key=lambda x: -x[1])  # sort by affix confidence
        top_N_afx = affix_len_exp[:min(top_N, len(affix_len_exp))]  # get the top_N most likely affixes
        filtered_affixes.extend(top_N_afx)
        pbar.update(1)
    pbar.close()

    # get just the affix and the confidence, and sort by confidence
    filtered_affixes = sorted([(afx, afx_score) for afx, afx_score, _, _ in filtered_affixes], key=lambda x: -x[1])
    return filtered_affixes


def gen_N_best_affixes(word_dict, min_stem_len=3, max_suf_len=4, min_suf_freq=10, best_N=50):
    """Get the `best_N` best suffixes according to maximum likelihood."""
    affixes = generate_candidates(word_dict, min_stem_len, max_suf_len, min_suf_freq)
    best_affixes = filter_affixes(affixes, best_N)
    return best_affixes
