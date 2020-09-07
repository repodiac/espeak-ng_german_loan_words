#
# This work is licensed under the Creative Commons Attribution 4.0 International License.
# To view a copy of this license, visit http://creativecommons.org/licenses/by/4.0/
# or send a letter to Creative Commons, PO Box 1866, Mountain View, CA 94042, USA.
#
# Copyright 2020 by repodiac
# (see https://github.com/repodiac, also for information how to provide attribution to this work)
#

import xml.etree.ElementTree as XML
import re
import sys
import os
from ipapy.kirshenbaummapper import KirshenbaumMapper

# constants
NS = {'wiktionary': 'http://www.mediawiki.org/xml/export-0.10/'}
REGEX_SECTION_LABEL_PRONOUNCIATION = re.compile('\\{\\{Aussprache\\}\\}')
REGEX_SECTION_LABEL_CATEGORY_LOAN_WORD = re.compile('\\[\\[Kategorie\\:Entlehnung aus dem (.+) \\(Deutsch\\)\\]\\]')
ATTRIBUTE_IPA = ':{{IPA}} {{Lautschrift|'

# since full text is parsed, this global list of "has been processed already" of labels is used to prevent duplicates
idx_list = set()

def extract_loan_words(wiktionary_xml_file):
    """
    Given a valid XML file from Wiktionary, relevant loan words in German are extracted with their IPA code
    and word provenance (key=category_loan_word)

    :param wiktionary_xml_file: the input XML file from Wiktionary

    :return: list of dict with keys {'label, 'category_loan_word', 'IPA'} per loan word
    """

    # raw parse XML file
    tree = XML.parse(wiktionary_xml_file)
    root = tree.getroot()

    terms = []
    issue_terms = []
    term = {}
    # iterate over Wiktionary (per term)
    for c, page in enumerate(root.iter(tag='{' + NS['wiktionary'] + '}page')):

        content = page.find('./wiktionary:revision/wiktionary:text', NS)
        raw_text = content.text

        # scan the full text for loan words (not only links etc.)
        if raw_text:

            category_loan_word_section_pos = REGEX_SECTION_LABEL_CATEGORY_LOAN_WORD.search(raw_text)
            if category_loan_word_section_pos:

                title = page.find('./wiktionary:title', NS)
                # NOTE: we have to enforce lowercase since espeak-ng can only deal with lowercase terms to be imported,
                # otherwise we need explicit flags for first capital letters (@capital),
                # see https://github.com/espeak-ng/espeak-ng/blob/master/docs/dictionary.md#flags!
                label_list = title.text.lower().split(' ')

                category_loan_word = category_loan_word_section_pos.groups()[0][:-2].lower()

                pronounciation_section_pos = REGEX_SECTION_LABEL_PRONOUNCIATION.search(raw_text)
                ipa_code = ''
                if pronounciation_section_pos:
                    ipa_code_start = raw_text.find(ATTRIBUTE_IPA)
                    if ipa_code_start > -1:
                        ipa_code_start += len(ATTRIBUTE_IPA)
                        ipa_code_end = ipa_code_start + raw_text[ipa_code_start:].find('}}')
                        ipa_code = raw_text[ipa_code_start:ipa_code_end]

                # espeak-ng allows up to 4 words as a term
                if len(label_list) > 4:
                    print('Multiword term detected -- Exceeds limit of 4 words, length =', len(label_list))
                    print('   term =', ' '.join(label_list))
                    print('   IPA codes =', ipa_code)
                    print('-- EXCLUDING term!\n')
                    # add multiword term to list for logging
                    issue_terms.append([' '.join(label_list), ipa_code, 'excluded'])
                    # skip to next term
                    continue

                ipa_code_list = ipa_code.split(' ') if ipa_code else []
                label = ' '.join(label_list)
                if len(label_list) > 1:

                    if len(ipa_code_list) > 0 and len(ipa_code_list) < len(label_list):
                        print('Multiword term detected -- Number of single IPA codes is shorter than number of words:')
                        print('   term =', label)
                        print('   IPA codes =', ipa_code)
                        print('-- IGNORING (proceed as if were single word term, instead.)\n')
                        # add multiword term to list for logging
                        # Note: espeak-ng requires/recommends using '||' for word break betweeen phonemes
                        issue_terms.append([label, '||'.join(ipa_code_list), 'included'])

                    # espeak-ng requires brackets if the term consists of more than one word
                    label = '(' + label + ')'

                if label not in idx_list:
                    idx_list.add(label)
                    term['label'] = label
                    term['category_loan_word'] = category_loan_word
                    term['IPA'] = ipa_code
                    terms.append(term)
                    term = {}

    return terms, issue_terms


def _ipa_code_corrections(ipa_code):
    """
    Manually curated list of replacements for specific IPA codes
    which ipapy library does not process as expected otherwise

    :param ipa_code: a single IPA code string
    :return: the IPA code with replacements in case
    """
    ipa_code = ipa_code \
        .replace('aːɐ̯', 'ɑːɾ') \
        .replace('ɐ', 'ɜ') \
        .replace('i̯', 'i') \
        .replace('ʁ', 'ɾ') \
        .replace('ɜ̯', 'a') \
        .replace('ʊ̯', 'ʊ') \
        .replace('o̯', 'o') \
        .replace('ɪ̯', 'ɪ') \
        .replace('y̯', 'y') \
        .replace('y̑', 'y') \
        .replace('ˑ', 'ː') \
        .replace('-', '') \
        .replace("‿", "ː") \
        .replace("͡", "ː") \
        .replace('(ː)', 'ː') \
        .replace('(r)', 'r') \
        .replace('(ə)', 'ə') \
        .replace('õ', 'ɔ') \
        .replace('ɔ̃', 'ɔ') \
        .replace('ā', 'ei') \
        .replace('a͂', 'ɔ') \
        .replace('i̊', 'i') \
        .replace('e̝', 'e') \
        .replace('r̺', 'ɾ') \

    return ipa_code


def _espeak_code_corrections(espeak_code):
    """
    Manually curated list of replacements for specific espeak-ng encodings
    which espeak-ng does not process as expected otherwise

    :param espeak_code: a single espeak_code code string
    :return: the espeak_code code with replacements in case
    """
    return espeak_code \
        .replace('Y', 'Y:') \
        .replace('V"', '@r') \
        .replace('V', '@') \
        .replace('#', ' ') \
        .replace('&', 'E') \
        .replace('<trl>', '') \
        .replace('<o>', '') \
        .replace('.', '') \
        .replace('E~', 'W') \
        .replace(' ', '||') # espeak-ng requires/recommends using '||' for word break betweeen phonemes


def convert_ipa_2_espeak_phoneme(ipa_code, correct_phonemes=True):
    """
    Converts IPA codes (https://en.wikipedia.org/wiki/International_Phonetic_Alphabet)
    to espeak-ng compatible phonemic encodings (based on ASCII encoding table, https://en.wikipedia.org/wiki/Kirshenbaum)

    * uses internal correction methods for both IPA and espeak-ng codes to compensate variation in the used
      method from KirshenbaumMapper() in the ipapy package (https://github.com/pettarin/ipapy), see parameter
      `correct_phonemes`

    :param ipa_code: plain IPA code to be converted to espeak-ng encoding
    :param correct_phonemes: if True (default), IPA codes are corrected if necessary for spurious encodings
    not to be processed properly by ipapy otherwise

    :return: converted espeak-ng encoding from given IPA code
    """

    espeak_code = None

    if correct_phonemes:
        ipa_code = _ipa_code_corrections(ipa_code)
    try:
        km_list = KirshenbaumMapper().map_unicode_string(
            unicode_string=ipa_code,
            ignore=False,
            single_char_parsing=None,
            return_as_list=True)

        espeak_code = _espeak_code_corrections(''.join(km_list))

    except ValueError as exc:
        print('   FAILING IPA code:', ipa_code)
        espeak_code = 'failed'

    return espeak_code


if __name__ == "__main__":
    # execute default usage if run as script
    import datetime

    if len(sys.argv) < 5:
        print('Help: generate_espeak-ng_import')
        print()
        print('-i <input, Wiktionary XML file>')
        print()
        print('-o <output, folder to file "de_extra"> for espeak-ng import')
        print()
        sys.exit(-1)

    if not os.path.isdir(sys.argv[4]):
        print('ERROR: -o output folder must not be a path to a file, but an existing folder (file name is fixed to "de_extra")')
        sys.exit(-1)
    elif not os.path.isfile(sys.argv[2]):
        print('ERROR: -i input file', sys.argv[2] , 'does not exist or is the wrong path')
        sys.exit(-1)

    # parse Wiktionary file
    print('EXTRACTING loan words from wiktionary file...')
    terms, issue_terms = extract_loan_words(sys.argv[2])
    # write to espeak-ng import file as "de_extra"
    with open(os.path.join(sys.argv[4], 'de_extra'), 'w', encoding='utf8') as fo:
        fo.write('//\n// This work/these contents are derived from/based on Wiktionary contents, input file: '
                 + os.path.basename(sys.argv[2]) + '\n// and created using code copyright 2020 by repodiac'
                 + ' (see https://github.com/repodiac, also for information how to provide attribution to this work)'
                 + '\n//\n// DATE OF CREATION: ' + datetime.date.today().strftime('%d.%m.%Y') + '\n//\n\n')

        print('CONVERTING IPA codes to espeak-ng encodings...')
        for t in terms:
            # convert IPA codes from Wiktionary to espeak-ng compatible encodings
            converted_espeak = convert_ipa_2_espeak_phoneme(t['IPA'])
            if not converted_espeak:
                issue_terms.append([t['label'], 'not available', 'excluded'])
            elif converted_espeak == 'failed':
                issue_terms.append([t['label'], t['IPA'], 'excluded'])
            else:
                t['ESPEAK'] = _espeak_code_corrections(converted_espeak)
                fo.write('\t'.join([t['label'], t['ESPEAK']]) + '\n')

    # write log file for terms with issues, either INCLUDED (multiword terms) or
    # EXCLUDED from the output (failing IPA codes)
    if issue_terms:
        with open(os.path.join(sys.argv[4], 'issue_terms.tab'), 'w', encoding='utf8') as ito:
            ito.write('\t'.join(['loan_word', 'IPA_code','status']) + '\n')
            for it in issue_terms:
                ito.write('\t'.join(it) + '\n')

        print()
        print('**** PLEASE NOTE ****')
        print('terms causing possible issues with espeak-ng have been stored to file issue_terms.tab -- please check back when importing into espeak-ng')
        print()