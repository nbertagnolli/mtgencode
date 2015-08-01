#!/usr/bin/env python
import sys
import os

libdir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'lib')
sys.path.append(libdir)
import utils
import jdecode
import cardlib
from cbow import CBOW

def main(fname, oname = None, verbose = True, 
         gatherer = False, for_forum = False, creativity = False, norarity = False):
    cards = []
    valid = 0
    invalid = 0
    unparsed = 0

    if norarity:
        decode_fields = [
            cardlib.field_name,
            cardlib.field_supertypes,
            cardlib.field_types,
            cardlib.field_loyalty,
            cardlib.field_subtypes,
            #cardlib.field_rarity,
            cardlib.field_pt,
            cardlib.field_cost,
            cardlib.field_text,
        ]
    else:
        decode_fields = cardlib.fmt_ordered_default

    if fname[-5:] == '.json':
        if verbose:
            print 'This looks like a json file: ' + fname
        json_srcs = jdecode.mtg_open_json(fname, verbose)
        for json_cardname in sorted(json_srcs):
            if len(json_srcs[json_cardname]) > 0:
                jcards = json_srcs[json_cardname]
                card = cardlib.Card(json_srcs[json_cardname][0], fmt_ordered = decode_fields)
                if card.valid:
                    valid += 1
                elif card.parsed:
                    invalid += 1
                else:
                    unparsed += 1
                cards += [card]

    # fall back to opening a normal encoded file
    else:
        if verbose:
            print 'Opening encoded card file: ' + fname
        with open(fname, 'rt') as f:
            text = f.read()
        for card_src in text.split(utils.cardsep):
            if card_src:
                card = cardlib.Card(card_src, fmt_ordered = decode_fields)
                if card.valid:
                    valid += 1
                elif card.parsed:
                    invalid += 1
                else:
                    unparsed += 1
                cards += [card]

    if verbose:
        print (str(valid) + ' valid, ' + str(invalid) + ' invalid, ' 
               + str(unparsed) + ' failed to parse.')

    good_count = 0
    bad_count = 0
    for card in cards:
        if not card.parsed and not card.text.text:
            bad_count += 1
        else:
            good_count += 1
        if good_count + bad_count > 15: 
            break
    # random heuristic
    if bad_count > 10:
        print 'Saw a bunch of unparsed cards with no text:'
        print 'If this is a legacy format, try rerunning with --norarity'

    if creativity:
        cbow = CBOW()

    def writecards(writer):
        for card in cards:
            writer.write((card.format(gatherer = gatherer, for_forum = for_forum)).encode('utf-8'))
            if creativity:
                writer.write('~~ closest cards ~~\n'.encode('utf-8'))
                nearest = cbow.nearest(card)
                for dist, cardname in nearest:
                    if for_forum:
                        cardname = '[card]' + cardname + '[/card]'
                    writer.write((cardname + ': ' + str(dist) + '\n').encode('utf-8'))
            writer.write('\n'.encode('utf-8'))

    if oname:
        if verbose:
            print 'Writing output to: ' + oname
        with open(oname, 'w') as ofile:
            writecards(ofile)
    else:
        writecards(sys.stdout)
        sys.stdout.flush()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    
    parser.add_argument('infile', #nargs='?'. default=None,
                        help='encoded card file or json corpus to encode')
    parser.add_argument('outfile', nargs='?', default=None,
                        help='output file, defaults to stdout')
    parser.add_argument('-g', '--gatherer', action='store_true',
                        help='emulate Gatherer visual spoiler')
    parser.add_argument('-f', '--forum', action='store_true',
                        help='use pretty mana encoding for mtgsalvation forum')
    parser.add_argument('-c', '--creativity', action='store_true',
                        help='use CBOW fuzzy matching to check creativity of cards')
    parser.add_argument('--norarity', action='store_true',
                        help='the card format has no rarity field; use for legacy input')
    parser.add_argument('-v', '--verbose', action='store_true', 
                        help='verbose output')
    
    args = parser.parse_args()
    main(args.infile, args.outfile, verbose = args.verbose, 
         gatherer = args.gatherer, for_forum = args.forum, creativity = args.creativity,
         norarity = args.norarity)
    exit(0)