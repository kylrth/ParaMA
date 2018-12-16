"""
Created on 2018-12-15

@author: kylrth
"""

class Affix(object):
    """Defines an affix, and rules about how it is applied."""

    def __init__(self, string, kind):
        """Save the string and the type (either prefix or suffix)."""
        self.string = string

        if kind.lower() not in ['pref', 'suf']:
            raise ValueError('kind must be one of (\'pref\', \'suf\')')
        self.kind = kind.lower()
    
    def apply(self, in_string):
        """Apply the affix to a string."""
        if self.kind == 'pref':
            return self.string + in_string
        else:
            return in_string + self.string
