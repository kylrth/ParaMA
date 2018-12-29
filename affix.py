"""
Created on 2018-12-15

@author: kylrth
"""

class Affix(object):
    """Defines an affix, and rules about how it is applied."""

    def __init__(self, affix, kind, trans='$'):
        """Save the string and the type (either prefix or suffix), along with any transformation that occurs to the stem
        along the morpheme boundary.

        Default affix is no affix, expressed as '$'.
        Default transformation is no transformation, expressed as '$'.
        """
        self.affix = affix

        # ensure kind is either prefix or suffix
        if kind.lower() not in ['pref', 'suf']:
            raise ValueError('kind must be one of (\'pref\', \'suf\')')
        self.kind = kind.lower()

        # validate transition string
        if trans != '$':
            if len(trans) < 5:
                raise ValueError('syntax error in transformation "{}"'.format(trans))
            if trans[:4] == 'SUB-':
                parts = '+'.join(trans.split('-')[1:]).split('+')
                if len(parts) != 2:
                    raise ValueError('syntax error in substitution "{}"'.format(trans))
                if not parts[0] or not parts[1]:
                    raise ValueError('syntax error in substitution "{}"'.format(trans))
            elif trans[:4] not in ['DEL-', 'DUP+']:
                raise ValueError('unrecognized transformation string "{}"'.format(trans))

        self.trans = trans

    def __str__(self):
        """Print using __repr__."""
        return self.__repr__()

    def __repr__(self):
        """Print out the attributes in a tuple."""
        return 'Affix({}, {}, {})'.format(self.affix, self.kind, self.trans)

    def __eq__(self, oth):
        """Return the equality of self to oth."""
        return isinstance(oth, Affix) and self.affix == oth.affix and self.kind == oth.kind and self.trans == oth.trans

    def __key(self):
        """Return a unique identifier for use of the class in sets."""
        return (self.affix, self.kind, self.trans)

    def __hash__(self):
        return hash(self.__key())

    def apply(self, in_string):
        """Apply the affix to a string, along with the specified transformation."""
        # apply the transformation
        if self.trans != '$':
            if self.kind == 'pref':
                if self.trans[:4] == 'DEL-':
                    if in_string[:len(self.trans[4:])] != self.trans[4:]:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = in_string[len(self.trans[4:]):]
                elif self.trans[:4] == 'SUB-':
                    start, end = self.trans[4:].split('+')
                    if in_string[:len(start)] != start:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = end + in_string[len(start):]
                else:  # 'DUP+'
                    if in_string[:len(self.trans[4:])] != self.trans[4:]:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = self.trans[4:] + in_string
            else:  # 'suf'
                if self.trans[:4] == 'DEL-':
                    if in_string[-len(self.trans[4:]):] != self.trans[4:]:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = in_string[:len(self.trans[4:])]
                elif self.trans[:4] == 'SUB-':
                    start, end = self.trans[4:].split('+')
                    if in_string[-len(start):] != start:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = in_string[:-len(start)] + end
                else:  # 'DUP+'
                    if in_string[-len(self.trans[4:]):] != self.trans[4:]:
                        raise ValueError('"{}" ({}) doesn\'t apply to "{}"'.format(self.trans, self.kind, in_string))
                    in_string = in_string + self.trans[4:]

        # apply the affix
        if self.affix != '$':
            if self.kind == 'pref':
                return self.affix + in_string
            else:
                return in_string + self.affix

        return in_string
