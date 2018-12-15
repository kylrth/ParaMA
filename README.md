# ParaMA

A Paradigm-based morphological analyzer

## Description

This is a semi-supervised tool for analyzing suffixation morphology for any language given a list of words and their frequencies. The details of the algorithm can be found in the following paper:

Hongzhi Xu, Mitch Marcus, Charles Yang, and Lyle Ungar. 2018. Unsupervised Morphology Learning with Statistical Paradigms. In *Proceedings of the 27th International Conference on Computational Linguistics (COLING 2018)*. pages 44-54. Santa Fe, New Mexico, USA.

## Segment a word list

Use the following command to segment a word list (with each line formatted: \<word\> \<freq\>), and save it to a file. Use `-h` for more information.

```bash
python3 main.py my_data.txt my_data_seg.txt
```

The output also gives the derivational chain information. For example, the word _sterilizing_ is derived by taking _sterilize_, deleting _e_ and adding _-ing_; _sterilize_ is in turn derived from _sterile_, deleting _e_ and adding _-ize_. The result will be the following:

```text
sterilized    steril iz ed    sterile $ $ sterile DEL-e ize sterilize DEL-e ed
```

## Rerun the COLING paper's experiments

See `coling2018.py` for details.

## The purpose of this fork

The number one reason to create this fork is that the original code didn't have very many comments and was hard to read. I wanted to modify the code for a research project, so I had to start from the top and make sense of what I could. I've made comments to try to explain everything as well as possible, in the hope that it will be easier for others who want to understand it.

One limitation I see with this algorithm is that it appears to only handle suffixes, while the paper seems to talk about prefixes and suffixes. As far as I can tell this limitation is a problem; there are lots of paradigms that are impossible to describe purely by suffixation, and so the algorithm will completely miss those. For my project, I'd like to modify this code so it can find paradigms in a more generalized way. I'd like to:

- Let it handle infixes, circumfixes, vowel harmonies.
- Consider transformations under a "phonologically-aware" edit distance metric, instead of thinking about affixes.

More on this coming down the pipe.

## Other improvements

Here's a list of other improvements I'd like to make, outside the scope of what was mentioned earlier.

- Not assume words from the test data have frequency of 10.
- Increase speed of add_test_to_train by not converting to and from a dictionary.
- Increase speed of get_seg_points by simply returning list(range(1, len(seg))).
- Use calc_performance at the end of eval_seg_points.
- Improve speed of get_reliable_suffix_tuples by not iterating over the list so much.
- Improve speed of MorphAnalyzer.train by returning probabilities that have already been calculated, instead of freqs.
- Improve speed by cleaning up prune_paradigms.
- Improve speed by refactoring the code a lot.
- Give objects semantically meaningful names. (E.g. "prune_suffix_tuple" -> "prune_suffixes")
- Rewrite segmentation.py.
