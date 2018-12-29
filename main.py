"""Command line utility to run morphological segmentation on specified files, with specified parameters. Created on Jun
12, 2018.

@author: xh
"""


import argparse
from param import Parameter
from morphanalyzer import MorphAnalyzer


def read_word_freq_list(infile):
    """Read a file where each line contains a word and its frequency count, tab-separated.

    Returns a list of tuples of the form (word, freq).
    """
    fin = open(infile, 'r', -1, 'utf-8')
    wordlist = []
    for line in fin:
        splitline = line.strip().split()
        if not line:
            continue
        word = splitline[0]
        freq = int(splitline[1])
        wordlist.append((word, freq))
    fin.close()
    return wordlist


def save_segmentations(word_segs, outfile):
    """Write segmentations to a file."""
    fout = open(outfile, 'w', -1, 'utf-8')
    for word, (seg, components) in word_segs:
        seg_str = ' '.join(seg)
        component_str = ' '.join([' '.join(component) for component in components])
        fout.write('%s\t%s\t%s\n' % (word, seg_str, component_str))
    fout.close()


def run(infile, outfile, params):
    """Run morphological segmentation on frequency data in `infile`, and save results in `outfile`."""
    print('| Reading data...')
    word_freq_list = read_word_freq_list(infile)
    print('| Analyzing...')
    morph_analyzer = MorphAnalyzer(params)
    morph_analyzer.train(word_freq_list)
    print('| Segmenting...')
    word_list = [word for word, _freq in word_freq_list]
    word_segs = morph_analyzer.segment_token_list(word_list)
    print('| Saving result...')
    save_segmentations(zip(word_list, word_segs), outfile)
    print('| Done!')


if __name__ == '__main__':
    parameters = Parameter()
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument('infile', help='The input file containing a word list with line format: <word> <freq>')
    arg_parser.add_argument('outfile', help='The output file to save the segmentation result')
    arg_parser.add_argument(
        '-p', '--prune', help='Whether use pruning (1|0, default:%s)' % parameters.DoPruning, type=bool,
        default=parameters.DoPruning)
    arg_parser.add_argument(
        '-t', '--trans', help='Whether use transformation rules (1|0, default:%s)' % parameters.UseTransRules,
        type=bool, default=parameters.UseTransRules)
    arg_parser.add_argument(
        '-c', '--comp', help='Whether process compounding (1|0, default:%s)' % parameters.DoCompound, type=bool,
        default=parameters.DoCompound)
    arg_parser.add_argument(
        '-e', '--excl', help='Whether exclude unreliable roots (1|0, default:%s)' % parameters.ExcludeUnreliable,
        type=bool, default=parameters.ExcludeUnreliable)
    arg_parser.add_argument(
        '-n', '--hyphen', help='Whether explicitly deal with hyphen words (1|0, default:%s)' % parameters.DoHyphen,
        type=bool, default=parameters.DoHyphen)
    arg_parser.add_argument(
        '-a', '--apos', help='Whether explicitly deal with apostrophes (1|0, default:%s)' % parameters.DoApostrophe,
        type=bool, default=parameters.DoApostrophe)
    arg_parser.add_argument(
        '-r', '--root',
        help='Minimal length of roots that will be possibly segmented (default:%s)' % parameters.MinStemLen,
        type=int, default=parameters.MinStemLen)
    arg_parser.add_argument(
        '-s', '--suff', help='Maximal length of suffixes (default:%s)' % parameters.MaxSuffixLen, type=int,
        default=parameters.MaxSuffixLen)
    args = arg_parser.parse_args()
    parameters.DoPruning = args.prune
    parameters.UseTransRules = args.trans
    parameters.DoCompound = args.comp
    parameters.ExcludeUnreliable = args.excl
    parameters.DoHyphen = args.hyphen
    parameters.DoApostrophe = args.apos
    parameters.MinStemLen = args.root
    parameters.MaxSuffixLen = args.suff
    parameters.print_all()
    run(args.infile, args.outfile, parameters)
