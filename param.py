'''
Created on Jun 11, 2018

@author: xh
'''


class Parameter():
    """Class containing parameters to be passed to the experiment function."""

    def __init__(self):
        """Set default parameters."""
        # Main Parameters
        self.UseTransRules = True
        self.DoPruning = True
        self.ExcludeUnreliable = True
        self.DoCompound = False

        self.MinStemLen = 3
        self.MaxAffixLen = 6

        self.DoHyphen = True
        self.DoApostrophe = True
        self.ApostropheChar = '\''

        self.BestNCandAffix = 100
        self.MinAffixFreq = 3
        self.MinParadigmSupport = 2
        self.MinParadigmAffix = 2

    def print_all(self):
        """Print the contents of some important parameters."""
        print('--------------Parameters-------------')
        print('UseTransRules: %s' % self.UseTransRules)
        print('DoPruning: %s' % self.DoPruning)
        print('DoCompound: %s' % self.DoCompound)
        print('ExcludeUnreliable: %s' % self.ExcludeUnreliable)
        print('MinStemLen: %s' % self.MinStemLen)
        print('MaxAffixLen: %s' % self.MaxAffixLen)
        print('DoHyphen: %s' % self.DoHyphen)
        print('DoApostrophe: %s' % self.DoApostrophe)
        print('-------------------------------------')
