'''
Created on Jun 11, 2018

@author: xh
'''

def get_seg_points(seg):
    """Get the indices where the word was split in `seg`.
    
    For example: get_seg_points(('beauti', 'ful', 'ly')) -> [6, 9]
    """
    seg_points = []
    indx = 0
    for i in range(len(seg) - 1):
        indx += len(seg[i])
        seg_points.append(indx)
    return seg_points

def get_best_seg(seg_test, segs_gold):
    """Choose the gold standard segmentation that matches most closely with `seg_test`.
    
    If none match at any indices, return the one with the least number of segments.
    """
    seg_points_test = set(get_seg_points(seg_test))
    best_correct, best_total, min_best_total = 0.0, 0.0, 100.0
    best_gold = None
    min_gold_seg = None
    for gold in segs_gold:
        seg_points_gold = set(get_seg_points(gold))  # get indices of segmentation
        gold_size = len(seg_points_gold)  # number of segments
        correct = len(seg_points_gold & seg_points_test)  # number of indices in gold and test
        if (correct > best_correct) or (correct == best_correct and gold_size < best_total):
            # if it's either more correct or similarly correct but with fewer segments, it's the new best
            best_correct = correct
            best_total = gold_size
            best_gold = gold
        if gold_size < min_best_total:  # also find gold with smallest size, in case none have any indices that match
            min_best_total = gold_size
            min_gold_seg = gold
    if best_total == 0:  # if no gold shared any indices with seg_test, then choose by least number of segments
        best_total = min_best_total
        best_gold = min_gold_seg
    return best_gold


def eval_seg_points(seg_gold, seg_test):
    """Return precision, recall, and F1-score of each predicted segmentation from `seg_test` compared with its closest
    match from the corresponding segmentations in `seg_gold`.
    
    If no gold segmentation matches at any indices, compare with the gold segmentation with the least number of
    segments.
    """
    if len(seg_gold) != len(seg_test): return 0.0, 0.0, 0.0
    correct_total, gold_total, pred_total = 0, 0, 0
    # choose the closest gold standard segmentation
    for i in range(len(seg_gold)):
        goldsegs = seg_gold[i]
        test = seg_test[i]
        word = ''.join(test)
        seg_points_test = set(get_seg_points(test))
        pred_size = len(seg_points_test)
        best_correct, best_total, min_best_total = 0.0, 0.0, 100.0
        for gold in goldsegs:
            gold_word = ''.join(gold)
            if word != gold_word:
                print('Warning: test word different from gold: %s | %s' % (word, gold_word))
            seg_points_gold = set(get_seg_points(gold))
            gold_size = len(seg_points_gold)
            correct = len(seg_points_gold & seg_points_test)  # the number of points in test and gold
            if (correct > best_correct) or (correct == best_correct and gold_size < best_total):
                # if it's either more correct or similarly correct but with fewer segments, it's the new best
                best_correct = correct
                best_total = gold_size
            if gold_size < min_best_total:
                # also find gold with smallest size, in case none have any indices that match
                min_best_total = gold_size
        if best_total == 0:  # if no gold shared any indices with seg_test, then choose by least number of segments
            best_total = min_best_total
        correct_total += best_correct
        gold_total += best_total
        pred_total += pred_size
    
    # calculate precision, recall, and F1-score
    if pred_total == 0:
        prec = 0.0
    else:
        prec = correct_total * 1.0 / pred_total
    if gold_total == 0:
        rec = 0.0
    else:
        rec = correct_total * 1.0 / gold_total
    if prec + rec == 0.0:
        f1 = 0.0
    else:
        f1 = 2 * prec * rec / (prec + rec)
    return (prec, rec, f1)

def get_seg_morphemes(seg):
    """Return a list of tuples where each tuple contains the starting and ending indices for a morpheme."""
    seg_morphemes = []
    sIndx = 0
    for i in range(len(seg)):
        # get index of the end of this morpheme by adding its length to the starting index
        eIndx = sIndx + len(seg[i])
        seg_morphemes.append((sIndx, eIndx))
        sIndx = eIndx  # the end of this morpheme is the start of the next
    return seg_morphemes

def calc_performance(tp, fp, fn):
    """Calculate precision, recall, and F1-score based on true positives, false positives, and false negatives."""
    # ensure no division by zero by returning zeros if tp (the numerator) is zero
    prec, rec, f1 = 0.0, 0.0, 0.0
    if tp > 0: 
        prec = tp * 1.0 / (tp + fp)
        rec = tp * 1.0 / (tp + fn)
        f1 = 2 * prec * rec / (prec + rec)
    return prec, rec, f1

def eval_seg_morphemes(seg_gold, seg_test):
    """Get the precision, recall, and F1-score of the predictions for each morpheme in each word."""
    if len(seg_gold) != len(seg_test): return 0.0, 0.0, 0.0
    tp, fp, fn = 0, 0, 0
    for i in range(len(seg_gold)):
        goldsegs = seg_gold[i]
        test = seg_test[i]
        # get the starting and ending indices of each morpheme
        seg_morphemes_test = set(get_seg_morphemes(test))
        _prec_best, _rec_best, f1_best = 0.0, 0.0, -1.0
        tp_best, fp_best, fn_best = 0, 0, 0
        for gold in goldsegs:
            # for each gold-standard segmentation, get the indices for the last gold-standard morpheme and calculate the
            # F1-score. Find the segmentation producing the best F1-score, and save the (true/false)(positive/negative)
            # results
            seg_morphemes_gold = set(get_seg_morphemes(gold))
            tp_local = len(seg_morphemes_gold & seg_morphemes_test)  # the number of tuples in common
            fp_local = len(seg_morphemes_test - seg_morphemes_gold)  # the number of predicted tuples not in gold
            fn_local = len(seg_morphemes_gold - seg_morphemes_test)  # the number of gold tuples not predicted
            _prec_local, _rec_local, f1_local = calc_performance(tp_local, fp_local, fn_local)
            if f1_local > f1_best or (f1_local == f1_best and fp_local + fn_local < fp_best + fn_best): 
                tp_best, fp_best, fn_best = tp_local, fp_local, fn_local
                f1_best = f1_local
        tp += tp_best
        fp += fp_best
        fn += fn_best
    return calc_performance(tp, fp, fn)

def eval_last_morphemes(seg_gold, seg_test):
    """Get the precision, recall, and F1-score of the predictions of the last morpheme for each word."""
    if len(seg_gold) != len(seg_test): return 0.0, 0.0, 0.0
    tp, fp, fn = 0, 0, 0
    for i in range(len(seg_gold)):
        goldsegs = seg_gold[i]
        test = seg_test[i]
        # get the starting and ending indices of the last predicted morpheme
        last_morph_indx = {get_seg_morphemes(test)[-1]}
        _prec_best, _rec_best, f1_best = 0.0, 0.0, -1.0
        tp_best, fp_best, fn_best = 0, 0, 0
        for gold in goldsegs:
            # for each gold-standard segmentation, get the indices for the last gold-standard morpheme and calculate the
            # F1-score. Find the segmentation producing the best F1-score, and save the (true/false)(positive/negative)
            # results
            seg_morphemes_gold_indx = {get_seg_morphemes(gold)[-1]}
            tp_local = len(seg_morphemes_gold_indx & last_morph_indx)  # 1 if the indices are the same
            fp_local = len(last_morph_indx - seg_morphemes_gold_indx)  # 1 if the indices are different
            fn_local = len(seg_morphemes_gold_indx - last_morph_indx)  # 1 if the indices are different
            _prec_local, _rec_local, f1_local = calc_performance(tp_local, fp_local, fn_local)
            if f1_local > f1_best or (f1_local == f1_best and fp_local + fn_local < fp_best + fn_best): 
                tp_best, fp_best, fn_best = tp_local, fp_local, fn_local
                f1_best = f1_local
        tp += tp_best
        fp += fp_best
        fn += fn_best
    return calc_performance(tp, fp, fn)

def evaluate_seg(gold_segs, test_segs):
    """Evaluate the predicted segmentations against the gold standard."""
    prec1, rec1, f11 = eval_last_morphemes(gold_segs, test_segs)
    prec2, rec2, f12 = eval_seg_morphemes(gold_segs, test_segs)
    prec3, rec3, f13 = eval_seg_points(gold_segs, test_segs)
    print('--Result----------Prec.   Rec.    F1-----------')
    print('Seg Points:      (%.4f, %.4f, %.4f)' % (prec3, rec3, f13))
    print('All Morphemes:   (%.4f, %.4f, %.4f)' % (prec2, rec2, f12))
    print('Last Morpheme:   (%.4f, %.4f, %.4f)' % (prec1, rec1, f11))










