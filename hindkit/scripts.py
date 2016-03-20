#!/usr/bin/env AFDKOPython
# encoding: UTF-8
from __future__ import division, absolute_import, print_function, unicode_literals

import re, collections

import hindkit as kit

def prepare_features_devanagari(do_mark_positioning, builder, style):

    light, bold = builder.devanagari_offset_matrix
    light_min, light_max = light
    bold_min, bold_max = bold

    axis_start = builder.family.masters[0].weight_location
    axis_end = builder.family.masters[-1].weight_location
    axis_range = axis_end - axis_start
    if axis_range == 0:
        ratio = 1
    else:
        ratio = (style.weight_location - axis_start) / axis_range
    offset_tuple = (
        light_min + (bold_min - light_min) * ratio,
        light_max + (bold_max - light_max) * ratio,
    )

    match_matra_i_alts(
        do_mark_positioning,
        builder,
        style,
        offset_range = offset_tuple
    )

def match_mI():
    pass
def position_marks():
    pass

MATRA_I_NAME_STEM = 'mI.'
MATRA_I_ANCHOR_NAME = 'abvm.i'

STEM_ANCHOR_NAMES = ['abvm.e', 'abvm']

ALIVE_CONSONANTS = [i + 'A' for i in kit.misc.CONSONANT_STEMS] + \
                   'GAbar JAbar DDAbar BAbar ZHA YAheavy DDAmarwari'.split()
DEAD_CONSONANTS = kit.misc.CONSONANT_STEMS

def get_script_prefix(script_name):
    return kit.misc.SCRIPTS[script_name.lower()]['abbreviation']

def glyph_filter_matra_i_alts(family, glyph):
    match = re.match(
        get_script_prefix(family.script) + MATRA_I_NAME_STEM + r'\d\d$',
        glyph.name,
    )
    return bool(match)

def glyph_filter_bases_for_matra_i(family, glyph):
    return glyph_filter_bases_alive(family, glyph)

def get_end(family, glyph):
    name = glyph.name
    end = ''
    if name.startswith(get_script_prefix(family.script)):
        main, sep, suffix = name[2:].partition('.')
        end = main.split('_')[-1]
        if end.endswith('xA'):
            end = end[:-2] + 'A'
        elif end.endswith('x'):
            end = end[:-1]
    return end

def glyph_filter_bases_alive(family, glyph):
    return get_end(family, glyph) in ALIVE_CONSONANTS

def glyph_filter_bases_dead(family, glyph):
    return get_end(family, glyph) in DEAD_CONSONANTS

def glyph_filter_bases_for_wide_matra_ii(family, glyph):
    name = glyph.name
    if name.startswith(
        kit.misc.SCRIPTS['devanagari']['abbreviation']
    ):
        name = name[2:]
    return name in POTENTIAL_BASES_FOR_WIDE_MATRA_II

def get_stem_position(glyph, stem_right_margin):
    for anchor in glyph.anchors:
        if anchor.name in STEM_ANCHOR_NAMES:
            stem_position = anchor.x
            break
    else:
        stem_position = glyph.width - stem_right_margin
    return stem_position

def restore_abvm_content(abvm_content):

    if re.search(
        r'# lookup MARK_BASE_{} \{{'.format(MATRA_I_ANCHOR_NAME),
        abvm_content
    ):

        abvm_content = re.sub(
            r'(?m)\n\n\n^lookup MARK_BASE_{0} \{{\n(^.+\n)+^\}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
            r'',
            abvm_content
        )

        commented_abvm_lookup = re.search(
            r'(?m)^# lookup MARK_BASE_{0} \{{\n(^# .+\n)+^# \}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
            abvm_content
        ).group()

        uncommented_abvm_lookup = '\n'.join([
            line[2:] for line in commented_abvm_lookup.splitlines()
        ])

        original_abvm_content = abvm_content.replace(
            commented_abvm_lookup,
            uncommented_abvm_lookup
        )

    else:
        original_abvm_content = abvm_content

    return original_abvm_content

def write_mI_matches_to_files(do_mark_positioning, builder, directory, mI_table, long_base_names):

    script_prefix = get_script_prefix(builder.family.script)

    if do_mark_positioning:

        with open(kit.temp(directory + '/abvm.fea'), 'r') as f:
            abvm_content = f.read()

        original_abvm_content = restore_abvm_content(abvm_content)

        original_abvm_lookup = re.search(
            r'(?m)^lookup MARK_BASE_{0} \{{\n(.+\n)+^\}} MARK_BASE_{0};'.format(MATRA_I_ANCHOR_NAME),
            original_abvm_content
        ).group()

        modified_abvm_lookup = original_abvm_lookup.replace(
            'pos base {}{}'.format(script_prefix, MATRA_I_NAME_STEM),
            'pos base @MATRA_I_BASES_'
        )

    Reph_positioning_offset = mI_table[0].glyph.width

    class_def_lines = []
    class_def_lines.extend(
        kit.compose_glyph_class_def_lines('MATRA_I_BASES_TOO_LONG', long_base_names)
    )

    substitute_rule_lines = []
    lookup_name = 'matra_i_matching'

    substitute_rule_lines.append('lookup {} {{'.format(lookup_name))

    for mI in mI_table:

        mI_number = mI.glyph.name[-2:]
        to_comment_substitute_rule = False

        if not mI.matches:
            print('\t       `%s` is not used.' % mI.glyph.name)
            to_comment_substitute_rule = True

            if do_mark_positioning:

                modified_abvm_lookup = modified_abvm_lookup.replace(
                    '\tpos base @MATRA_I_BASES_' + mI_number,
                    '#\tpos base @MATRA_I_BASES_' + mI_number
                )

        if do_mark_positioning:

            locator = '@MATRA_I_BASES_%s <anchor ' % mI_number

            search_result = re.search(
                locator + r'\-?\d+',
                modified_abvm_lookup
            )

            if search_result:
                x = search_result.group().split(' ')[-1]
                modified_x = str(int(x) - Reph_positioning_offset)
                modified_abvm_lookup = modified_abvm_lookup.replace(
                    locator + x,
                    locator + modified_x,
                )

            else:
                print("\t[!] `%s` doesn't have the anchor for Reph." % mI.glyph.name)

        class_def_lines.extend(
            kit.compose_glyph_class_def_lines(
                'MATRA_I_BASES_' + mI_number,
                mI.matches
            )
        )

        substitute_rule_lines.append(
            "{}sub {}mI' @MATRA_I_BASES_{} by {};".format(
                '# ' if to_comment_substitute_rule else '  ',
                script_prefix,
                mI_number,
                mI.glyph.name
            )
        )

    substitute_rule_lines.append('}} {};'.format(lookup_name))

    if do_mark_positioning:

        commented_original_abvm_lookup = '# ' + original_abvm_lookup.replace('\n', '\n# ')

        modified_abvm_content = original_abvm_content.replace(
            original_abvm_lookup,
            commented_original_abvm_lookup + '\n\n\n' + modified_abvm_lookup
        )

        with open(kit.temp(directory + '/abvm.fea'), 'w') as f:
            f.write(modified_abvm_content)

    with open(kit.temp(directory + '/matra_i_matching.fea'), 'w') as f:
        result_lines = (
            ['# CLASSES', ''] + class_def_lines +
            ['# RULES', ''] + substitute_rule_lines
        )
        f.write('\n'.join(result_lines) + '\n')

def match_matra_i_alts(do_mark_positioning, builder, style, offset_range = (0, 0)):

    script_prefix = get_script_prefix(builder.family.script)

    font = style.open_font(is_temp=True)

    mI_list   = [font[glyph_name] for glyph_name in sorted(font.groups['MATRA_I_ALTS'])]
    base_list = [font[glyph_name] for glyph_name in font.groups['BASES_ALIVE']]

    MatchRow = collections.namedtuple('MatchRow', 'glyph, stretch, matches')

    mI_table = [
        MatchRow(
            glyph   = mI,
            stretch = abs(mI.rightMargin),
            matches = []
        ) for mI in mI_list
    ]

    for anchor in font[script_prefix + 'mE'].anchors:
        if anchor.name in ['_' + name for name in STEM_ANCHOR_NAMES]:
            stem_right_margin = abs(anchor.x)
            break
    else:
        raise SystemExit("[WARNING] Can't find the stem anchor in glyph `mE`!")

    tolerance_of_mI_stretch_shormI_numbere = (font[script_prefix + 'VA'].width - stem_right_margin) / 2
    long_base_names = []

    stem_positions = [get_stem_position(b, stem_right_margin) for b in base_list]
    stem_position_min = min(stem_positions)
    stem_position_max = max(stem_positions)

    stem_positions_with_offset = []
    for stem_position in stem_positions:
        ratio = (stem_position - stem_position_min) / (stem_position_max - stem_position_min)
        adjusted_offset = offset_range[0] + (offset_range[-1] - offset_range[0]) * ratio
        stem_position_with_offset = stem_position + int(adjusted_offset)
        stem_positions_with_offset.append(stem_position_with_offset)

    for i, base in enumerate(base_list):

        base_name = base.name
        stem_position = stem_positions_with_offset[i]

        if stem_position < mI_table[0].stretch:
            mI_table[0].matches.append(base_name)

        elif stem_position >= mI_table[-1].stretch:
            if stem_position < mI_table[-1].stretch + tolerance_of_mI_stretch_shormI_numbere:
                mI_table[-1].matches.append(base_name)
            else:
                long_base_names.append(base_name)

        else:
            for index, mI in enumerate(mI_table):
                if stem_position < mI.stretch:
                    if mI.stretch - stem_position < abs(mI_table[index - 1].stretch - stem_position):
                        mI.matches.append(base_name)
                    else:
                        mI_table[index - 1].matches.append(base_name)
                    break

    write_mI_matches_to_files(do_mark_positioning, builder, style.directory, mI_table, long_base_names)

POTENTIAL_BASES_FOR_WIDE_MATRA_II = '''
KA PHA KxA PHxA K_RA PH_RA Kx_RA PHx_RA
J_KA K_KA K_PHA Kx_KxA Kx_PHA Kx_PHxA L_KA L_PHA
N_KA N_PHA N_PH_RA PH_PHA PHx_PHxA P_PHA SH_KA SH_KxA
SS_KA SS_K_RA SS_PHA S_KA S_K_RA S_PHA T_KA T_K_RA T_PHA
K_TA.traditional
'''.split()
