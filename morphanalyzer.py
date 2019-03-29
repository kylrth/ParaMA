'''
Created on Jun 11, 2018

@author: xh
'''


from test_util import dump_repr

from segcandidate import TokenAnalyzer
from bayesian import get_initial_parameters, estimate_affix_probability, do_step1_segmention
from bayesian import calc_seg_prob  # calc_seg_probs
from segmentation import get_seg_dict_by_paradigms
from pruning import prune_paradigms
from affixcandidate import gen_N_best_affixes, calc_affix_score_by_dist
from paradigm import create_paradigms, get_paradigm_affix_sets, get_reliable_affix_tuples
from reliableroot import is_reliable_root
from affix import Affix


class MorphAnalyzer():
    """Class for morphology analysis."""

    def __init__(self, param):
        """Save given parameters."""
        self.param = param
        self.__word_dict = None
        self.__seg_dict = None
        self.__ta = None
        self.__probroots = None
        self.__probaffix = None
        self.__probtrans = None

    def __get_frequent_long_words(self, word_dict):
        """Collect a word frequency dictionary of words of length greater than 4 and appearing more than 3 times."""
        new_word_dict = {}
        for word, freq in word_dict.items():
            word_len = len(word)
            if word_len <= 4:
                continue
            if freq < 3:
                continue
            new_word_dict[word] = freq
        return new_word_dict

    def __get_reliable_paradigm_affixes(self, word_dict):
        """Use long and frequent words to generate an initial set of suffixes."""
        print('--get reliable words')
        reliable_word_dict = self.__get_frequent_long_words(word_dict)
        print('--create token analyzer')
        affix_dict = dict(gen_N_best_affixes(
            word_dict, min_stem_len=self.param.MinStemLen, max_suf_len=self.param.MaxAffixLen,
            best_N=self.param.BestNCandAffix))

        for _ in range(2):  # 2 epochs
            ta = TokenAnalyzer(
                reliable_word_dict, affix_dict, self.param.MinStemLen, self.param.MaxAffixLen, self.param.UseTransRules
            )
            print('--analyze possible segmentations for tokens')
            token_segs = ta.analyze_token_list(reliable_word_dict.keys())
            dump_repr(token_segs, 'token_segs{}'.format(_))

            print('--get initial parameters')  # initial probabilities for roots, suffixes, and transitions
            probroots, probaffix, probtrans = get_initial_parameters(token_segs)
            dump_repr(probroots, 'probroots{}'.format(_))
            dump_repr(probaffix, 'probaffix{}'.format(_))
            dump_repr(probtrans, 'probtrans{}'.format(_))

            print('--segment tokens')  # get the most likely segmentation from those listed as possible in `token_segs`
            resolved_segs = do_step1_segmention(token_segs, probroots, probaffix, probtrans)
            dump_repr(resolved_segs, 'resolved_segs{}'.format(_))

            print('--create paradigms')
            paradigm_dict, _atomic_word_dict = create_paradigms(resolved_segs)
            dump_repr(paradigm_dict, 'paradigm_dict{}'.format(_))
            dump_repr(_atomic_word_dict, '_atomic_word_dict{}'.format(_))

            print('--get paradigm suffix sets')  # get a set of suffixes for each root
            root_affix_set_list = get_paradigm_affix_sets(paradigm_dict)
            dump_repr(root_affix_set_list, 'root_affix_set_list{}'.format(_))

            print('--prune paradigms')
            reliables, singles, affix_dict = get_reliable_affix_tuples(
                root_affix_set_list,
                word_dict,
                self.param.MinParadigmSupport,
                self.param.MinParadigmAffix,
                self.param.MinAffixFreq
            )
            dump_repr(reliables, 'reliables{}'.format(_))
            dump_repr(singles, 'singles{}'.format(_))
            dump_repr(affix_dict, 'affix_dict{}'.format(_))

            # use these suffix probabilities at the next iteration
            # prior_prob_affix = estimate_affix_probability(affix_dict)

        return reliables, singles, affix_dict

    def __strip_apostrophe(self, token):
        """Split before an apostrophe, ensuring it appears after any hyphen."""
        apostrophe = ''
        left_part = token
        indx = token.rfind(self.param.ApostropheChar)
        indx_hyphen = token.rfind('-')
        if indx > indx_hyphen:
            apostrophe = token[indx:]
            left_part = token[:indx]
        return left_part, apostrophe

    def __split_compound(self, token, word_dict):
        """Split a token into its compound components, based on a dictionary of known words."""
        # if the word is less than 7 characters, we'll assume it's not compound.
        if len(token) < 7:
            return [token]

        # collect possible splits
        candidate_analyses = []
        for i in range(3, len(token) - 2):
            # split at index i
            word0 = token[:i]
            word1 = token[i:]

            # the split is invalid if word0 or word1 isn't a known word
            if not (word0 in word_dict and word1 in word_dict):
                continue

            # the split is invalid if word0 or word1 isn't a reliable root
            freq0 = word_dict[word0]
            freq1 = word_dict[word1]
            if not (is_reliable_root(word0, freq0) and is_reliable_root(word1, freq1)):
                continue

            # save the split
            candidate_analyses.append([[word0, word1], abs(len(token) - 2 * i), -i])

        # if no split was probable, return the word itself
        if not candidate_analyses:
            return [token]

        # otherwise, choose the split that splits closest to the edge [maximizes abs(len(token) - 2 * i)]
        return sorted(candidate_analyses, key=lambda x: (x[1], x[2]))[0][0]

    def __get_subtokens(self, token, word_dict):
        """Split along hyphens, and optionally call self.__split_compound."""
        subtokens = token.split('-')
        subtoken_compound = []
        for subtoken in subtokens:
            if self.param.DoCompound:
                compound_components = self.__split_compound(subtoken, word_dict)
                subtoken_compound.extend(compound_components)
            else:
                subtoken_compound.append(subtoken)
        return subtoken_compound

    def __process_hyphen(self, word_dict):
        """Return a morpheme frequency dictionary using the word frequency dictionary provided.

        Split along hyphens to collect morphemes, and use the total word's frequency as the frequency of each morpheme.
        """
        processed_word_dict = {}
        for word, freq in word_dict.items():
            subwords = word.split('-')
            for subword in subwords:
                if not subword:
                    continue
                if subword in processed_word_dict:
                    processed_word_dict[subword] += freq
                else: processed_word_dict[subword] = freq
        return processed_word_dict

    def __process_apostrophe(self, word_dict):
        """Remove apostrophes (and everything following) from each word in a word frequency dictionary.

        Won't remove apostrophes at the beginning of a word.
        """
        processed_word_dict = {}
        for word, freq in word_dict.items():
            indx = word.find(self.param.ApostropheChar)
            if indx >= 0:
                word = word[:indx]
            if word in processed_word_dict:
                processed_word_dict[word] += freq
            else: processed_word_dict[word] = freq
        return processed_word_dict

    def __process_tokens(self, token_freq_list):
        """Convert word frequency list to dictionary.

        If selected by params, call self.__process_hyphen and/or self.__process_apostrophe as well.
        """
        word_dict = dict(token_freq_list)
        if self.param.DoHyphen:
            word_dict = self.__process_hyphen(word_dict)
        if self.param.DoApostrophe:
            word_dict = self.__process_apostrophe(word_dict)
        return word_dict

    def __segment_simple_token(self, token, seg_dict, ta, probroots, probaffix, probtrans):
        """Segment a token assumed to have no hyphens or apostrophes, using the model specified in the parameters."""
        # if the token is recognized, segment it according to the model
        if token in seg_dict:
            return seg_dict[token]

        # get possible segmentations
        segs = ta.analyze_token(token)
        # print(segs)
        # input()

        # find the segment with the highest probability
        max_prob = 0.0
        best_ts = None
        for ts in segs:
            prob = calc_seg_prob(ts, probroots, probaffix, probtrans)
            if prob > max_prob:
                max_prob = prob
                best_ts = ts

        if best_ts:
            root = best_ts.root
            affix = best_ts.affix
            morph = best_ts.morph

            # if the word is simple, return it that way
            if affix.affix == '$':
                return ((token,), ((token, Affix('$', 'pref', '$')),))

            morphs = []
            components = []
            # if the root has been segmented before, then use that segmentation too
            if root in seg_dict:
                root_seg = seg_dict[root]
                seg_morphs = list(root_seg[0])
                seg_components = root_seg[1]
                indx = 0
                for i in range(len(seg_morphs) - 1):
                    root_morph = seg_morphs[i]
                    morphs.append(root_morph)
                    indx += len(root_morph)
                morphs.append(morph[indx:])
                components.extend(seg_components)
            else:  # otherwise, assume it's simple
                morphs.append(morph)
                components.append((root, Affix('$', 'pref', '$')))
            # add the final transformation to the lists of morphs and components
            morphs.append(affix)
            components.append((root, affix))

            return (tuple(morphs), tuple(components))

        # if there was no best segmentation, assume it's simple
        return ((token,), ((token, Affix('$', 'pref', '$')),))

    def __segment_token(self, token, word_dict, seg_dict, ta, probroots, probaffix, probtrans):
        """Segment the token using the model objects from the parameters."""
        # strip apostrophe if there, and split along hyphens
        token, apostrophe_0 = self.__strip_apostrophe(token)
        subtokens = self.__get_subtokens(token, word_dict)

        morphs = []
        components = []
        for subtoken in subtokens:
            # strip apostrophes from each subtoken
            subtoken, apostrophe = self.__strip_apostrophe(subtoken)

            if not subtoken:
                continue

            # segment the subtoken, and add the morphs and components to the list
            seg_subtoken_morphs, seg_subtoken_components = self.__segment_simple_token(
                subtoken, seg_dict, ta, probroots, probaffix, probtrans)
            morphs.extend(seg_subtoken_morphs)
            components.extend(seg_subtoken_components)

            # add the apostrophe part of the subtoken
            if apostrophe:
                morphs.append(apostrophe)
                components.append((apostrophe, Affix('$', 'pref', '$')))

        # account for the apostrophe part, if there
        if apostrophe_0:
            morphs.append(apostrophe_0)
            components.append((apostrophe_0, Affix('$', 'pref', '$')))

        return tuple(morphs), tuple(components)

    def __segment_tokens(self, token_list, seg_dict, word_dict, ta, probroots, probsuffix, probtrans):
        """Apply __segment_token to each token in the list."""
        token_segs = []
        for token in token_list:
            morphs, components = self.__segment_token(token, word_dict, seg_dict, ta, probroots, probsuffix, probtrans)
            token_segs.append((morphs, components))
        return token_segs

    def train(self, train_word_freq_list):
        """Create a model from the given word frequency list."""
        # create the word frequency dictionary, parsing hyphens and apostrophes as determined by self.params
        train_dict = self.__process_tokens(train_word_freq_list)
        dump_repr(train_dict, 'train_dict')

        # get paradigms with reliable affixes
        reliable_affix_tuples, single_affix_tuples, affix_dict = self.__get_reliable_paradigm_affixes(train_dict)
        dump_repr(reliable_affix_tuples, 'reliable_affix_tuples')
        dump_repr(single_affix_tuples, 'single_affix_tuples')
        dump_repr(affix_dict, 'affix_dict')

        print('| Generate tokens candidate segmentations')
        token_analyzer = TokenAnalyzer(
            train_dict,
            affix_dict,
            self.param.MinStemLen,
            self.param.MaxAffixLen,
            self.param.UseTransRules
        )
        token_segs = token_analyzer.analyze_token_list(train_dict.keys())
        dump_repr(token_segs, 'token_segs')

        print('| Obtain statistics')
        probroots, _probaffix, probtrans = get_initial_parameters(token_segs)
        probaffix = estimate_affix_probability(affix_dict)  # estimate probability based on new data
        dump_repr(probroots, 'probroots')
        dump_repr(_probaffix, '_probaffix')
        dump_repr(probtrans, 'probtrans')
        dump_repr(probaffix, 'probaffix')

        print('| Segment tokens')
        resolved_segs = do_step1_segmention(token_segs, probroots, probaffix, probtrans)
        dump_repr(resolved_segs, 'resolved_segs')

        print('| Create paradigms')
        paradigm_dict, atomic_word_dict = create_paradigms(resolved_segs)
        dump_repr(paradigm_dict, 'paradigm_dict')
        dump_repr(atomic_word_dict, 'atomic_word_dict')

        # print('| Recalculate seg probability')
        # token_seg_probs = calc_seg_probs(token_segs, probroots, probaffix, probtrans)
        # token_seg_prob_dict = dict(token_seg_probs) !!!!!!!

        print('| Calculate affix score')  # using the distribution of root lengths
        affix_type_score = calc_affix_score_by_dist(paradigm_dict, debug=False)
        dump_repr(affix_type_score, 'affix_type_score')

        if self.param.DoPruning:
            print('| Prune paradigms')
            paradigm_dict = prune_paradigms(
                paradigm_dict,
                reliable_affix_tuples,
                affix_type_score,
                single_affix_tuples,
                train_dict,
                self.param.ExcludeUnreliable)
            dump_repr(paradigm_dict, 'pruned_paradigm_dict')

        print('| Get segmentation dictionary')
        # use the paradigms to get a map from words to their segmentation structure
        seg_dict = get_seg_dict_by_paradigms(paradigm_dict)
        # add the atomic words to the list
        seg_dict.update(atomic_word_dict)
        dump_repr(seg_dict, 'seg_dict')

        # combine reliable affix tuples and single affix tuples into one dictionary (Why???)
        affix_tuple_dict = {}
        affix_tuple_dict.update(reliable_affix_tuples)
        affix_tuple_dict.update(single_affix_tuples)
        dump_repr(affix_tuple_dict, 'affix_tuple_dict')

        self.__word_dict = train_dict
        self.__seg_dict = seg_dict
        self.__ta = token_analyzer
        self.__probroots = probroots
        self.__probaffix = probaffix
        self.__probtrans = probtrans

    def segment_token(self, token):
        """Use the currently trained model to segment the token."""
        segs = list(self.__segment_token(
            token,
            self.__word_dict,
            self.__seg_dict,
            self.__ta,
            self.__probroots,
            self.__probaffix,
            self.__probtrans))

        # convert affix objects to strings
        for i, seg in enumerate(segs):
            seg = list(seg)
            for j, element in enumerate(seg):
                if isinstance(element, Affix):
                    # if element.trans != '$':
                    #     raise ValueError('wow! {}'.format(seg))
                    seg[j] = element.affix
            segs[i] = tuple(seg)

        return tuple(segs)

    def segment_token_list(self, token_list):
        """Apply segment_token to each token in the list."""
        token_seg_list = []
        for token in token_list:
            token_seg_list.append(self.segment_token(token))
        return token_seg_list
