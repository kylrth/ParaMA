'''
Created on Jun 11, 2018

@author: xh
'''


class SegStructure():
    """A class for storing an analysis of a certain token."""

    def __init__(self, token, morph, root, trans, suffix):
        """Save parameters."""
        self.token = token
        self.morph = morph
        self.root = root
        self.trans = trans
        self.suffix = suffix
        self.key = (root, trans, suffix)  # the triple described in the paper
    
    def is_atomic(self):
        """Determine whether the word is atomic, as defined in section 3 of the paper."""
        return self.token == self.root


class TokenAnalyzer:
    """Class for analyzing tokens."""

    def __init__(self, word_dict, affix_dict, min_stem_len, max_suffix_len, use_trans_rules):
        """Save parameters."""
        self.word_dict = word_dict
        self.affix_dict = affix_dict
        self.morph_dict = get_morph_dict(word_dict, min_stem_len)
        self.min_stem_len = min_stem_len
        self.max_suffix_len = max_suffix_len
        self.use_trans_rules = use_trans_rules

    def analyze_token(self, token):
        """Get possible segmentations for each possible division of the token into a morph and a suffix.
        
        Use rules to determine the simplest transformation accounting for any differences between underlying and surface
        representations.
        """
        segs = []
        if len(token) <= self.min_stem_len:
            # this word is morphologically simple, so it is atomic. Store it as such.
            root = token
            morph = token
            trans = '$'
            affix = '$'
            ts = SegStructure(token, morph, root, trans, affix)
            segs.append(ts)
            return segs
        # The word is long enough to be morphologically complex, so check for possible affixes.
        s_indx = max(self.min_stem_len, len(token)-self.max_suffix_len)
        for indx in range(s_indx, len(token)):
            suffix = token[indx:]
            if not suffix in self.affix_dict: continue
            morph = token[:indx]
            root = morph
            trans = '$'
            # avoid the single character suffix with a large number of non-occurring roots, by starting with a small
            # stem and increasing until a word is encountered
            if root in self.word_dict:
                ts = SegStructure(token, morph, root, trans, suffix)
                segs.append(ts)
                continue
            
            if not self.use_trans_rules: continue
            
            # Always account for a word with the simplest transformation rules
            # avoid -> pains = paint - t + s
            # avoid -> passes = pas + DUP-s + es
            # lost -> borned = borne -e +ing |*born + ing
            # To do this, we compute possibilities in order of likelihood, and stop we find a possible transformation.
            if len(suffix) < 2: continue
            # --------------------------------Hypothesize deletion rules
            found_possible_root = False
            if morph in self.morph_dict:
                for root in self.morph_dict[morph]:
                    if (root + suffix) in self.word_dict: continue
                    found_possible_root = True
                    if root[-1] == suffix[0]:
                        # : voiced = voic(voice-e)+ed
                        trans = 'DEL-' + root[-1]
                        ts = SegStructure(token, morph, root, trans, suffix)
                        segs.append(ts)
                    else:
                        trans = 'DEL-' + root[-1]
                        # : voiced = voic(voice-e)+ed
                        ts = SegStructure(token, morph, root, trans, suffix)
                        segs.append(ts)
            if found_possible_root: continue
            # --------------------------------Hypothesize replacement rules
            # : carried = carry -y+i + ed; morph = carri
            if (morph[:-1] in self.morph_dict) and (not morph in self.word_dict):
                # avoid painting = paint REP-t+t +ing
                for root in self.morph_dict[morph[:-1]]:
                    if root == morph: continue
                    if (root + suffix) in self.word_dict: continue
                    found_possible_root = True
                    trans = 'REP-%s+%s' % (root[-1], morph[-1])
                    ts = SegStructure(token, morph, root, trans, suffix)
                    segs.append(ts)
            if found_possible_root: continue
            # --------------------------------Hypothesize duplication rules
            # avoid passes = pas + DUP+s +es, since pass is already a word
            if (len(morph) > max(2, self.min_stem_len)) and (morph[-1] == morph[-2]):
                root = morph[:-1]
                if (root in self.word_dict) and (not (root + suffix) in self.word_dict):
                    trans = 'DUP-' + morph[-1]
                    ts = SegStructure(token, morph, root, trans, suffix)
                    segs.append(ts)
        if len(segs) == 0:  # produce at least one possible segmentation if none were found
            root = token
            morph = token
            trans = '$'
            suffix = '$'
            ts = SegStructure(token, morph, root, trans, suffix)
            segs.append(ts)
        return segs

    def analyze_token_list(self, token_list):
        """Apply self.analyze_token to each token in the list."""
        token_segs = []
        for token in token_list:
            segs = self.analyze_token(token)
            token_segs.append(segs)
        return token_segs


def get_morph_dict(word_dict, min_stem_len):
    """Create a dictionary mapping words without the last character to the possible words represented."""
    morph_dict = {}
    for word in word_dict:
        if len(word) <= min_stem_len:
            continue
        morph = word[:-1]
        #---------------------------------------------------------------------
        # pain != paint - t, as itself is a word
        # lost: X = Xe - e, while X is word, Xe is a verb; will be largely affected by noise
        # process in analyzed token
        # (This is done in analyze_token method)
        #---------------------------------------------------------------------
        if morph in morph_dict: morph_dict[morph].append(word)
        else: morph_dict[morph] = [word]
    return morph_dict
