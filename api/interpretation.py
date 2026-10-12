"""Explicit traditional interpretation rules, with modern applications kept distinct."""
GROUPS={'비겁':['비견','겁재'],'식상':['식신','상관'],'재성':['편재','정재'],'관성':['편관','정관'],'인성':['편인','정인']}
HANJA={'비겁':'比劫','식상':'食傷','재성':'財星','관성':'官星','인성':'印星','비견':'比肩','겁재':'劫財',
       '식신':'食神','상관':'傷官','편재':'偏財','정재':'正財','편관':'偏官','정관':'正官','편인':'偏印','정인':'正印'}
ELEMENT_HANJA={'목':'木','화':'火','토':'土','금':'金','수':'水'}

def pattern_basis_meaning(basis):
    if basis=='월지 본기 (투간 없음)':
        return '태어난 달 안에 배정된 글자가 사주의 위쪽 글자에 드러나지 않아, 달을 대표하는 글자의 관계를 참고해 분류했어요.'
    if '차용' in basis:
        return '달을 대표하는 글자가 자기 기준·동료 관계에 해당해, 계산 규칙에 따라 달 안의 다른 글자 관계를 함께 참고했어요.'
    if '지지합화' in basis:
        return '달의 글자가 다른 아래쪽 글자들과 연결되는 배치를 확인하고, 계산 규칙이 읽은 연결 결과를 기준으로 분류했어요.'
    if basis.endswith('투간'):
        role='대표' if '본기' in basis else '보조'
        return f'태어난 달 안의 {role} 글자가 사주의 위쪽 글자에도 드러나, 그 글자의 역할을 기준으로 분류했어요.'
    if '록(祿)' in basis:
        return '달의 글자가 나의 기준 글자를 받쳐주는 특정 위치에 해당하는지 확인해 분류했어요.'
    if '양인(제왕)' in basis:
        return '달의 글자가 나의 기준 글자를 강하게 받쳐주는 것으로 배정된 특정 위치에 해당해 분류했어요.'
    return '태어난 달과 기준 글자의 관계를 계산 규칙에 따라 분류했어요. 원래 선택 근거는 계산 근거에서 확인할 수 있습니다.'

def _chapter(topic,title,paragraphs,focus,evidence,rule):
    return {'topic':topic,'title':title,'paragraphs':paragraphs,'body':'\n\n'.join(paragraphs),
            'focus':focus,'reflection':focus,'evidence_ids':evidence,'rule_ids':[rule],
            'source_ids':['saju-interpretation-rules','saju-classical-framework']}

from api.reading_voice import STEM_VOICE, ROLE_VOICE, GOD_VOICE, ELEMENT_VOICE, MONEY_DETAIL
from api.chart_context import context, GODS, GROUP_OF, elemental_details, person_fit, relation_detail, describe


def build_narrative(report):
    from api.reader_language import build_readable_chapters
    return build_readable_chapters(report)
