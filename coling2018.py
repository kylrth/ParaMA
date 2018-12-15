'''
Created on Jun 11, 2018

@author: xh
'''
from param import Parameter
from evaluation import evaluate_seg
from morphanalyzer import MorphAnalyzer

def read_word_freq_list(infile):
    """Read a file where each line contains a word and its frequency count, tab-separated.
    
    Returns a list of tuples of the form (word, freq).
    """
    fin = open(infile, 'r', -1, 'utf-8')
    wordlist = []
    for line in fin:
        splitline = line.strip().split()
        if len(line) == 0: continue
        word = splitline[0]
        freq = int(splitline[1])
        wordlist.append((word, freq))
    fin.close()
    return wordlist

def read_test_gold(infile):
    """Read the gold-standard morphological segmentation from a file.
    
    Each line contains a word, followed by a colon, and then a space-separated list of allowable morphological segments
    where the segments are separated by dashes.

    Returns a list of words, and a list of lists of segmentations. Should be of the same length.
    """
    fin = open(infile, 'r', -1, 'utf-8')
    wordlist = []
    goldseglist = []
    for line in fin:
        line = line.strip()
        token_segs = line.split(':')
        # get the full list of segmentations
        seg_candidates = token_segs[1].strip().split(' ')
        original_word = token_segs[0].strip()
        word = ''
        segs_morphs = []
        for seg in seg_candidates:
            # break each segmentation into segments
            seg_morphs = seg.strip().split('-')
            mainword = ''.join(seg_morphs)
            if word != '' and mainword != word:  # ensure the segmentations are spelled the same as the word itself
                print('Inconsistent segmentations: %s - %s' % (word, mainword))
            word = mainword
            # save the segmentation as a tuple of segments
            segs_morphs.append(tuple(seg_morphs))
        wordlist.append(original_word)
        goldseglist.append(segs_morphs)
    fin.close()
    return wordlist, goldseglist

def add_test_to_train(train_word_freq_list, test_list):
    """Add words from the test data to the frequency list, assuming a frequency of 10."""
    # turn it into a dictionary
    word_dict = dict(train_word_freq_list)
    for word in test_list:
        if word in word_dict:
            word_dict[word] += 10
        else:
            word_dict[word] = 10
    # change back to a list of tuples and return
    return sorted(word_dict.items(), key=lambda x: -x[1])

def run_experiment(infile_train, infile_test_gold, params):
    """Run an experiment by reading data from a training file and testing on the gold standard data."""
    print('| Reading data...')
    # read the frequency list data
    train_word_freq_list = read_word_freq_list(infile_train)
    # read the gold standard data into a test list of words and the answers
    test_list, test_gold = read_test_gold(infile_test_gold)
    # print the length of the training and test data
    print('--Training data: %s' % (len(train_word_freq_list)))
    print('--Testing data: %s' % (len(test_list)))

    # add the test data to the training data. This is to ensure all words in the test data are listed with freq > 0.
    train_word_freq_list = add_test_to_train(train_word_freq_list, test_list)

    print('| Training...')
    # create the analyzer using the specified parameters
    morph_analyzer = MorphAnalyzer(params)
    # train
    morph_analyzer.train(train_word_freq_list)

    print('| Segmenting test tokens...')
    # segment the test data
    test_segs_components = morph_analyzer.segment_token_list(test_list)
    # get the segmentation listed for each word
    test_segs = [x[0] for x in test_segs_components]
    print('| Evaluation...')
    # get precision, recall, and F1 scores
    evaluate_seg(test_gold, test_segs)

def run_english():
    """Runs an experiment on English data against gold standard results."""
    params = Parameter()
    params.UseTransRules = True
    params.DoPruning = True
    params.DoCompound = True
    params.ExcludeUnreliable = True
    params.BestNCandSuffix = 70
    infile_train = r'data/wordlist.2010.eng.utf8.txt'
    infile_test_gold = r'data/mit/gold.eng.txt'
    run_experiment(infile_train, infile_test_gold, params)

def run_turkish():
    """Runs an experiment on Turkish data against gold standard results."""
    params = Parameter()
    params.UseTransRules = True
    params.DoPruning = False
    params.DoCompound = False
    params.ExcludeUnreliable = False
    params.BestNCandSuffix = 150
    infile_train = r'data/wordlist.2010.tur.utf8.txt'
    infile_test_gold = r'data/mit/gold.tur.txt'
    run_experiment(infile_train, infile_test_gold, params)

def run_finnish():
    """Runs an experiment on Finnish data against gold standard results."""
    params = Parameter()
    params.UseTransRules = False
    params.DoPruning = True
    params.DoCompound = True
    params.ExcludeUnreliable = True
    params.BestNCandSuffix = 150
    infile_train = r'data/wordlist.2010.fin.utf8.txt'
    infile_test_gold = r'data/mit/gold.fin.txt'
    run_experiment(infile_train, infile_test_gold, params)

if __name__ == '__main__':
    run_english()
    #run_turkish()
    #run_finnish()














