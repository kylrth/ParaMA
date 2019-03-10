'''
Created on Jun 11, 2018

@author: xh
'''


from affix import Affix


class SegStructure():
    """A class for storing an analysis of a certain token."""

    def __init__(self, token, morph, root, affix):
        """Save parameters."""
        self.token = token
        self.morph = morph
        self.root = root
        self.affix = affix  # an affix object
        self.key = (root, affix)  # the triple described in the paper
        # (an Affix object describes the transformation and the affix)

    def is_atomic(self):
        """Determine whether the word is atomic, as defined in section 3 of the paper."""
        return self.token == self.root

    def __repr__(self):
        """Produce a description of the object."""
        return 'SegStructure({}, {}, {}, {})'.format(
            self.token,
            self.morph,
            self.root,
            self.affix
        )


class TokenAnalyzer:
    """Class for analyzing tokens."""

    def __init__(self, word_dict, affix_dict, min_stem_len, max_suffix_len, use_trans_rules):
        """Save parameters."""
        self.word_dict = word_dict
        self.affix_dict = affix_dict
        self.prefix_morph_dict, self.suffix_morph_dict = get_morph_dicts(word_dict, min_stem_len)
        self.min_stem_len = min_stem_len
        self.max_suffix_len = max_suffix_len
        self.use_trans_rules = use_trans_rules

    def get_trans_rules(self, token, morph, affix, kind):
        """Get the transformation rules that occur when `affix` is applied to `root` to get `token`, and return the
        SegStructure.

        Always account for a word using the simplest transformation rules. Some bad examples:
            avoid -> pains = paint - t + s
            avoid -> passes = pas + DUP+s + es
            lost -> borned = borne -e +ing |*born + ing
        To do this, we compute possibilities in order of likelihood, and stop when we find a possible transformation.
        """
        if kind == 'pref':
            morph_dict = self.prefix_morph_dict
        else:
            morph_dict = self.suffix_morph_dict

        tses = []

        # Deletion
        if morph in morph_dict:
            for root in morph_dict[morph]:
                if kind == 'suf' and root + affix in self.word_dict:
                    continue
                if kind == 'pref' and affix + root in self.word_dict:
                    continue

                if kind == 'suf':  # and root[-1] == affix[0]
                    # : voiced = voic(voice-e)+ed
                    trans = 'DEL-' + root[-1]
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))
                if kind == 'pref':  # and root[0] == affix[-1]
                    trans = 'DEL-' + root[0]
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))
        if tses:
            return tses

        # Substitution
        # : carried = carry -y+i + ed; morph = carri
        if kind == 'suf':
            if morph[:-1] in morph_dict and morph not in self.word_dict:
                # avoid painting = paint SUB-t+t +ing
                for root in morph_dict[morph[:-1]]:
                    if root == morph:
                        continue
                    if root + affix in self.word_dict:
                        continue

                    trans = 'SUB-%s+%s' % (root[-1], morph[-1])
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))
        else:  # 'pref'
            if morph[1:] in morph_dict and morph not in self.word_dict:
                # avoid painting = paint SUB-t+t +ing
                for root in morph_dict[morph[1:]]:
                    if root == morph:
                        continue
                    if affix + root in self.word_dict:
                        continue

                    trans = 'SUB-%s+%s' % (root[0], morph[0])
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))
        if tses:
            return tses

        # Duplication
        # avoid passes = pas + DUP+s +es, since pass is already a word
        if kind == 'suf':
            if len(morph) > max(2, self.min_stem_len) and morph[-1] == morph[-2]:
                root = morph[:-1]
                if root in self.word_dict and root + affix not in self.word_dict:
                    trans = 'DUP+' + morph[-1]
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))
        else:  # 'pref'
            if len(morph) > max(2, self.min_stem_len) and morph[0] == morph[1]:
                root = morph[1:]
                if root in self.word_dict and affix + root not in self.word_dict:
                    trans = 'DUP+' + morph[0]
                    tses.append(SegStructure(token, morph, root, Affix(affix, kind, trans)))

        return tses

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
            ts = SegStructure(token, morph, root, Affix('$', 'pref', '$'))
            segs.append(ts)
            return segs

        # The word is long enough to be morphologically complex, so check for possible affixes.
        edge = max(self.min_stem_len, len(token) - self.max_suffix_len)
        for indx in range(1, len(token)):
            # avoid the single character suffix with a large number of non-occurring roots, by starting with a small
            # stem and increasing until a word is encountered
            left = token[:indx]
            right = token[indx:]

            if len(right) >= edge and Affix(left, 'pref') in self.affix_dict:  # if `left` is a valid prefix
                morph = right
                root = right
                if root in self.word_dict:  # if the remaining part is a known word
                    ts = SegStructure(token, morph, root, Affix(left, 'pref', '$'))
                    segs.append(ts)
                    continue
                if len(left) < 2:
                    continue
                if self.use_trans_rules:
                    # get the most likely transition rule if there is one
                    tses = self.get_trans_rules(token, morph, left, 'pref')
                    if tses:
                        segs.extend(tses)
            if indx >= edge and Affix(right, 'suf') in self.affix_dict:  # if `right` is a valid suffix
                morph = left
                root = left
                if root in self.word_dict:  # if the remaining part is a known word
                    ts = SegStructure(token, morph, root, Affix(right, 'suf', '$'))
                    segs.append(ts)
                    continue
                if len(right) < 2:
                    continue
                if self.use_trans_rules:
                    # get the most likely transition rule if there is one
                    tses = self.get_trans_rules(token, morph, right, 'suf')
                    if tses:
                        segs.extend(tses)

        if not segs:  # produce at least one possible segmentation if none were found
            root = token
            morph = token
            ts = SegStructure(token, morph, root, Affix('$', 'pref'))
            segs.append(ts)
        return segs

    def analyze_token_list(self, token_list):
        """Apply self.analyze_token to each token in the list."""
        token_segs = []
        for token in token_list:
            segs = self.analyze_token(token)
            token_segs.append(segs)
        return token_segs


def get_morph_dicts(word_dict, min_stem_len):
    """Create a dictionary mapping words without the last character to the possible words represented, and a dictionary
    mapping words without the first character to the possible words represented.

    Examples of things to avoid
        pain != paint - t, as itself is a word
        lost: X = Xe - e, while X is word, Xe is a verb; will be largely affected by noise
        process in analyzed token
    This is taken care of by the `analyze_token` method.
    """
    prefix_morph_dict = {}
    suffix_morph_dict = {}
    for word in word_dict:
        if len(word) <= min_stem_len:
            continue
        # prefixes
        morph = word[1:]
        if morph in prefix_morph_dict:
            prefix_morph_dict[morph].append(word)
        else: prefix_morph_dict[morph] = [word]

        # suffixes
        morph = word[:-1]
        if morph in suffix_morph_dict:
            suffix_morph_dict[morph].append(word)
        else: suffix_morph_dict[morph] = [word]
    return prefix_morph_dict, suffix_morph_dict
