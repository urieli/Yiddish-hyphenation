# Script to find and add Yiddish syllable boundaries
# Author: Isaac L. Bleaman <bleaman@berkeley.edu>
# Date: 2019-09-04
# Modified by Assaf Urieli to:
# - take into account Hassidic Yiddish
# - transform into a class
# - add text hyphenation

# How to run script:
# python yiddish_syllable_boundaries.py -i WORD_LIST.txt -o WORD_LIST_SYLLABIFIED.txt -s jacobs

# sample input (new-line separated): אױסגעמוטשעט אַרױסגעלאָפֿן אָװנטברױט
# sample output: אױס|גע|מו|טשעט אַרױס|גע|לאָ|פֿן אָ|װנט|ברױט

# Note: This script will also standardize Yiddish Unicode representations
# to avoid using precombined characters (except װ, ױ, ײ).

# See further documentation in the README.

import argparse
import re
import itertools
import syllabifier  # from: https://sourceforge.net/p/p2tk/code/HEAD/tree/python/syllabify/syllabifier.py
                    # tweaked for python3

class YiddishSyllabifier:
    def __init__(self, system):
        self.system = system
        self.yiddish_patterns = YiddishSyllabifier.__generate_yiddish_patterns(system)

    # combine multi Yiddish characters (אַ) into single Unicode chars (אַ)
    @staticmethod
    def __combine_chars(string):
        combinations = [
            ('אַ', 'אַ'),
            ('אָ', 'אָ'),
            ('בֿ', 'בֿ'),
            ('וּ', 'וּ'),
            ('וו', 'װ'),
            ('וי', 'ױ'),
            ('יִ', 'יִ'),
            ('יי', 'ײ'),
            ('ײַ', 'ײַ'),
            ('כּ', 'כּ'),
            ('פּ', 'פּ'),
            ('פֿ', 'פֿ'),
            ('שׂ', 'שׂ'),
            ('תּ', 'תּ')
        ]
        for letter in combinations:
            string = re.sub(letter[0], letter[1], string)
        return string

    # separate single Yiddish characters (אַ) into multiple Unicode chars (אַ)
    # except װ, ױ, ײ
    @staticmethod
    def __separate_chars(string):
        combinations = [
            ('אַ', 'אַ'),
            ('אָ', 'אָ'),
            ('בֿ', 'בֿ'),
            ('וּ', 'וּ'),
            ('יִ', 'יִ'),
            ('ײַ', 'ײַ'),
            ('כּ', 'כּ'),
            ('פּ', 'פּ'),
            ('פֿ', 'פֿ'),
            ('שׂ', 'שׂ'),
            ('תּ', 'תּ')
        ]
        for letter in combinations:
            string = re.sub(letter[0], letter[1], string)
        return string

    # pre-process Yiddish strings in order to do correct syllabification
    # replace consonantal yud with 'j'
    # replace syllabic nun/lamed with 'ņ'/'Ņ'/'ļ'
    # For hassidic: replace Shtumer Alef with ạ
    @staticmethod
    def __replace_consonant_j_syllabic_nl(string):
        string = re.sub(r'\bאי', 'ạי', string) # Added for hassidic
        string = re.sub(r'\bאו', 'ạו', string) # Added for hassidic
        string = re.sub(r'\bאײ', 'ạײ', string) # Added for hassidic
        string = re.sub(r'\bאױ', 'ạױ', string) # Added for hassidic
        string = re.sub(r'\bאײַ', 'ạײַ', string) # Added for hassidic
        string = re.sub(r'\bאוּ', 'ạוּ', string) # Added for hassidic
        string = re.sub(r'װא([וױוּ])', r'װạ\1', string) # Shtumer alef after tsvey vovn for hassidic
        string = re.sub('יאַ', 'jאַ', string)
        string = re.sub('יאָ', 'jאָ', string)
        string = re.sub('יא', 'jא', string) # Added for hassidic
        string = re.sub('יו', 'jו', string)
        string = re.sub('יע', 'jע', string)
        string = re.sub('ייִ', 'jיִ', string)
        string = re.sub('יײַ', 'jײַ', string)
        string = re.sub('יײ', 'jײ', string)
        string = re.sub('יױ', 'jױ', string)

        # regex to find *syllabic* nun and lamed
        # any nun/lamed that isn't adjacent to a vowel
        # Added Shtumer alef for hassidic
        string = re.sub(r'(?<!\s|אַ|ע|י|א|אָ|ו|ײ|ײַ|ױ|יִ|וּ)נ(?!אַ|ע|י|א|אָ|ו|ײ|ײַ|ױ|יִ|וּ)', 'ņ', string)
        string = re.sub(r'(?<!\s|אַ|ע|י|א|אָ|ו|ײ|ײַ|ױ|יִ|וּ)ן', 'Ņ', string)
        string = re.sub(r'(?<!\s|אַ|ע|י|א|אָ|ו|ײ|ײַ|ױ|יִ|וּ)ל(?!אַ|ע|י|א|אָ|ו|ײ|ײַ|ױ|יִ|וּ)', 'ļ', string)

        # undo that last step if we accidentally replaced word-initial nun/lamed
        if string.startswith('ņ'):
            string = 'נ' + string[1:]
        elif string.startswith('ļ'):
            string = 'ל' + string[1:]

        return ''.join(list(string))

    # generate the Yiddish patterns that will feed into syllabification algorithm
    @staticmethod
    def __generate_yiddish_patterns(system):

        ### STEP 1: create a a list of all possible syllable onsets (in Yiddish alphabet)

        # mapping from transliterations to Yiddish (combined) characters
        # this will be used to map onsets in Latin chars to Yiddish chars
        # NOTE: non-final letters only
        # NOTE: 'Y' mapped to 'j'; important later on
        transliterations = {
            'A': ['אַ'],
            'Ay': ['ײַ'],
            'B': ['ב'],
            'D': ['ד'],
            'E': ['ע'],
            'Ey': ['ײ'],
            'F': ['פֿ', 'פ'], # Added fey without nikud for Hassidic
            'G': ['ג'],
            'H': ['ה'],
            'I': ['יִ', 'יִ', 'י'], # Added yud without nikud for Hassidic
            'K': ['ק', 'כּ'],
            'Kh': ['כ', 'ח'],
            'L': ['ל'],
            'M': ['מ'],
            'N': ['נ'],
            'O': ['אָ'],
            'Oy': ['ױ'],
            'P': ['פּ'],
            'R': ['ר'],
            'S': ['ס', 'שׂ', 'ת'],
            'Sh': ['ש'],
            'T': ['ט', 'תּ'],
            'Ts': ['צ'],
            'U': ['ו', 'וּ'],
            'V': ['װ', 'בֿ'],
            'Y': ['j'],
            'Z': ['ז'],
            'Zh': ['ז ש']
        }

        # list of all Yiddish vowels and list of singleton consonants
        vowels = [ # nuclei, really
            'א', # Added for hassidic
            'אַ',
            'ע',
            'י',
            'אָ',
            'ו',
            'ײ',
            'ײַ',
            'ױ',
            'יִ',
            'וּ',
            'ņ', # not nun
            'Ņ', # not langer nun
            'ļ', # not lamed
        ]

        consonants = [
            #'א', Removed for hassidic
            'ạ', # Hassidic: shtumer alef
            'ב',
            'בֿ',
            'ג',
            'ד',
            'ה',
            'װ',
            'ז',
            'ח',
            'ט',
            'j', # not yud
            'כּ',
            'כ',
            'ך',
            'ל', # this is never syllabic, since we'll have caught that and replaced earlier
            'מ',
            'ם',
            'נ', # this is never syllabic
            'ן', # this is never syllabic
            'ס',
            'ע',
            'פּ',
            'פֿ',
            'פ', # Hassidic: fey without nikud
            'ף',
            'צ',
            'ץ',
            'ק',
            'ר',
            'ש',
            'שׂ',
            'תּ',
            'ת'
        ]

        onsets = []
        if system == 'jacobs':
            # all allowable syllable onsets in Yiddish (to feed into Maximum Onset Principle)
            # adapted from Jacobs (2005:115-7)
            onsets = ['P T', 'P L', 'P R', 'P N', 'P S', 'P Sh', 'P Kh', 'P L', 'P K', 'T R', 'T M', 'B D', 'B L', 'B R', 'B G',
                        'D L', 'D N', 'T N', 'T L', 'T K', 'T V', 'T F', 'T Kh', 'D R', 'D V', 'K N', 'K T', 'K D', 'K L', 'K S',
                        'K R', 'K V', 'G N', 'G L', 'G R', 'G V', 'G Z', 'F L', 'F R', 'V L', 'V R', 'S M', 'S F', 'S V', 'S N',
                        'S T', 'S D', 'S K', 'S P', 'S Kh', 'S R', 'S L', 'Z M', 'Z N', 'Z G', 'Z R', 'Z L', 'Z B', 'Sh M', 'Sh V',
                        'Sh F', 'Sh N', 'Sh T', 'Sh P', 'Sh K', 'Sh Kh', 'Sh R', 'Sh L', 'Sh T Sh', 'Zh M', 'Zh L', 'Kh M', 'Kh V', 'Kh Sh', 'Kh S',
                        'Kh L', 'Kh K', 'Kh Ts', 'Kh N', 'Kh R', 'Ts L', 'Ts N', 'Ts D', 'Ts V', 'T Sh V', 'M R', 'M L', 'Sh P R', 'Sh T R', 'Sh K R',
                        'Sh P L', 'Sh K L', 'S P R', 'S T R', 'S K R', 'S P L', 'S K L',
                        'T Sh', 'D Zh']

        elif system == 'viler':
            # onsets according to the syllabification rule of Yankev Viler, cited by Jacobs (2005:125)
            # but with additional infrequent onsets removed (like 'P N')
            onsets = ['P L', 'P R', 'T L', 'T R',
                        'B L', 'B R', 'D R', 'K L', 'K N',
                        'K R', 'G L', 'G R', 'F L', 'F R',
                        'S M', 'S N', 'S T', 'S K', 'S P',
                        'S L', 'Sh M', 'Sh N', 'Sh T', 'Sh P', 'Sh K',
                        'Sh R', 'Sh L', 'Sh P R', 'Sh T R',
                        'Sh K R', 'Sh P L', 'Sh K L', 'S P R',
                        'S T R', 'S K R', 'S P L', 'S K L',
                        'T Sh', 'D Zh']

        # convert/expand 'S T' into all possibilities: ס ט, ס תּ, שׂ תּ, etc. for all other onsets
        all_onsets = []
        for onset in onsets:
            phonemes = onset.split(' ')
            onset_list = [transliterations[phoneme] for phoneme in phonemes]
            all_onsets.append(list(itertools.product(*onset_list)))
        all_onsets = [y for x in all_onsets for y in x] # flatten list

        all_onsets = [' '.join(onset) for onset in all_onsets]

        # onsets can include a null onset, and all singleton consonants
        all_onsets.append('')
        all_onsets += consonants

        prefixes = [
            'אַדורכ',
            'אדורכ',
            'דורכ',
            'אַהינ',
            'אהינ',
            'אַהער',
            'אהער',
            'אַװעק',
            'אװעק',
            'אױס',
            'אומ',
            'אונטער',
            'אױפֿ',
            'אױפ',
            'אַנטקעגנ',
            'אנטקעגנ',
            'אַקעגנ',
            'אקעגנ',
            'קעגנ',
            'איבער',
            'אײַנ',
            'אײנ',
            'אָנ',
            'אנ',
            'אַנידער',
            'אנידער',
            'אָפּ',
            'אפ',
            'אַראָפּ',
            'אראָפ',
            'אראפ',
            'אַרױס',
            'ארױס',
            'אַרומ',
            'ארומ',
            'אַרױפֿ',
            'אַרױפ',
            'ארױפ',
            'אַריבער',
            'אריבער',
            'אַרײַנ',
            'אַרײנ',
            'ארײנ',
            'בײַ',
            'בײ',
            'מיט',
            'נאָכ',
            'נאכ',
            'פֿונאַנדער',
            'פונאַנדער',
            'פונאנדער',
            'פֿאַנאַנדער',
            'פאַנאַנדער',
            'פאנאנדער',
            'פֿאָר',
            'פאָר',
            'פאר',
            'פֿאָרױס',
            'פאָרױס',
            'פארױס',
            'אַפֿער',
            'אַפער',
            'אפער',
            'אַפֿיר',
            'אַפיר',
            'אפיר',
            'פֿיר',
            'פיר',
            'צוזאַמענ',
            'צוזאמענ',
            'צונױפֿ',
            'צונױפ',
            'צוריק',
            'צו',
            'קריק',
            'קאַריק',
            'קאריק',
            'פֿאַרבײַ',
            'פאַרבײ',
            'פארבײ',
            'אַנט',
            'אנט',
            'באַ',
            'בא',
            'גע',
            'דער',
            'פֿאַר',
            'פאַר',
            'פאר',
            'צע',
        ]
        prefixes = tuple(map(lambda s: YiddishSyllabifier.__combine_chars(s), prefixes))

        ### STEP 2: compile Yiddish patterns to feed into syllabification algorithm

        yiddish_patterns = dict()
        yiddish_patterns['consonants'] = consonants
        yiddish_patterns['vowels'] = vowels
        yiddish_patterns['onsets'] = all_onsets
        yiddish_patterns['prefixes'] = prefixes

        return yiddish_patterns

    def add_syllable_boundaries(self, word):
        if any(x in word for x in ('בֿ', 'ח', 'כּ', 'שׂ', 'תּ', 'ת')):
            return word
        
        subwords_syllabified = []

        # split on punctuation, but retain punctuation marks
        subwords = re.findall(r'\w+|\W+', word)
        wordPattern = re.compile(r'\w+')
        prefixes = self.yiddish_patterns['prefixes']

        for subword in subwords:
            if wordPattern.match(subword):
                try:
                    my_prefix = None
                    if subword.startswith(prefixes):
                        for prefix in prefixes:
                            if subword.startswith(prefix) and not subword == prefix:
                                my_prefix = prefix
                                subword = subword.removeprefix(prefix)
                                break

                    # syllabify word
                    subword = YiddishSyllabifier.__replace_consonant_j_syllabic_nl(subword)
                    syllables = syllabifier.syllabify(self.yiddish_patterns, subword)
                    result = ''
                    for syllable in syllables:
                        for item in syllable:
                            if isinstance(item, list):
                                if len(item) > 0:
                                    result += ''.join(item)
                        # Don't allow a one character syllable at start of word
                        if len(result) > 1:
                            result += '|'

                    if my_prefix:
                        result = my_prefix + '|' + result

                    # change the special Latin chars back to Yiddish chars
                    result = re.sub('j', 'י', result)
                    result = re.sub('ņ', 'נ', result)
                    result = re.sub('Ņ', 'ן', result)
                    result = re.sub('ļ', 'ל', result)
                    result = re.sub('ạ', 'א', result) # for hassidic
                    result = re.sub(r'\|$', '', result)

                    subwords_syllabified.append(result)
                except:
                    subwords_syllabified = list(subword) # if there's a non-phoneme char in word, just add the word as-is
            else:
                subwords_syllabified.append(subword)

        return subwords_syllabified

    # Return the word with | on syllable boundaries
    def syllabify(self, word):
        word = YiddishSyllabifier.__combine_chars(word)
        syllabified_words = self.add_syllable_boundaries(word)
        word = ''.join(syllabified_words)
        word = YiddishSyllabifier.__separate_chars(word)
        return word
    
    def hyphenate(self, text, line_length):
        lines = text.splitlines()
        chunks = []
        
        for line in lines:
            words = line.split()
            current_chunk = ""
            
            for word in words:
                if len(current_chunk) + len(word) + 1 <= line_length:
                    current_chunk += " "
                    current_chunk += word
                else:
                    syllables = self.syllabify(word).split('|')
                    lengths = []
                    total_length = 0
                    for syllable in syllables:
                        total_length += len(syllable)
                        lengths.append(total_length)
                    
                    last_index = next((i for i in range(len(lengths) - 1, -1, -1) if len(current_chunk) + lengths[i] + 2 <= line_length), None)

                    if last_index is not None:
                        current_chunk += ' ' + ''.join(syllables[:last_index+1]) + '־'
                        chunks.append(current_chunk)
                        current_chunk = ''.join(syllables[last_index+1:])
                    else:
                        chunks.append(current_chunk)
                        current_chunk = word
            
            if current_chunk:
                chunks.append(current_chunk)
        
        return chunks

def readfile(filename):
    with open(filename, 'r') as textfile:
        data = textfile.readlines()
    data = [word.strip() for word in data]
    return data

def writefile(filename, wordlist):
    with open(filename, 'w') as textfile:
        for word in wordlist:
            textfile.write(word + '\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script to add syllable boundaries to a Yiddish word list.')
    parser.add_argument('-i', '--input', help='Path to a text file with one word per line for command "syllabify" and any text for command "hyphenate"', required=True)
    parser.add_argument('-o', '--output', help='Path to a text file that will be written, with one syllabified word per line', required=True)
    parser.add_argument('-s', '--system', choices=['jacobs', 'viler'], help='Syllabification system: "jacobs" follows Maximum Onset Principle using all the onsets from Jacobs (2005:115-7); "viler" follows syllabification of Yankev Viler, cited by Jacobs (2005:125)', default='jacobs')
    parser.add_argument('-c', '--command', choices=['syllabify', 'hyphenate'], help='Which command to run', required=True)
    parser.add_argument('-l', '--length', help="Maximum line-length for hyphenation.", default=66, type=int)
    args = parser.parse_args()

    yiddish_syllabifier = YiddishSyllabifier(args.system)

    if args.command=='syllabify':
        wordlist = readfile(args.input)
        syllabified_wordlist = []
        for word in wordlist:
            word = yiddish_syllabifier.syllabify(word)
            syllabified_wordlist.append(word)

        writefile(args.output, syllabified_wordlist)
    else:
        lines = readfile(args.input)
    
        with open(args.output, 'w') as textfile:
            for line in lines:
                hyphenated_lines = yiddish_syllabifier.hyphenate(line, args.length)
                for hyphenated_line in hyphenated_lines:
                    textfile.write(hyphenated_line + "\n")
                textfile.flush()
