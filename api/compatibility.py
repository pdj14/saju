"""Directional comparisons of two existing charts, with traceable limits."""
from api.chart_context import context, GROUP_OF, GODS, polish_particles, describe
from api.saju_report import build_chapters
from api.reader_language import ELEMENT, MANNER, PRIVATE, capacity, work_story

# Pairwise tables match korean-saju 0.3.0. Three-member formations and
# transformation are intentionally not inferred by merging two people.
BRANCH_TABLES={'육합':['子丑','寅亥','卯戌','辰酉','巳申','午未'],
               '육충':['子午','丑未','寅申','卯酉','辰戌','巳亥'],
               '파':['子酉','午卯','巳申','寅亥','辰丑','戌未'],
               '해':['子未','丑午','寅巳','卯辰','申亥','酉戌'],
               '형':['子卯']}
ADVERSE={'육충','파','해','형'}
KINDS={'육합':'연결과 조율의 관계','육충':'서로 마주 서는 충돌 관계','파':'유지와 조율의 마찰 관계',
       '해':'기대가 어긋나는 관계','형':'기준과 긴장을 살피는 관계'}
SOURCE_IDS=['saju-compatibility-rules','saju-relations','saju-yong']


def branch_relations(left,right):
    if left==right:
        return ['형'] if left in '辰午酉亥' else []
    pair=frozenset([left,right])
    return [kind for kind,pairs in BRANCH_TABLES.items() if pair in map(frozenset,pairs)]


def personal_review_points(report):
    c=context(report);b=c['b'];points=[]
    def add(key,title,text,basis):
        points.append({'id':key,'title':title,'text':polish_particles(text),'basis':basis,'source_id':'saju-interpretation-rules'})
    if b['available'] and '약' in b['strength'] and (c['root_group']=='식상' or GROUP_OF[c['outside']]=='재성'):
        add('output-with-weak-support','기회보다 감당할 범위를 먼저 볼 구성',
            f"잘 만들고 성과를 내려는 힘은 보이지만, 책임과 비용까지 계속 넓히는 데는 불리한 조건으로 읽어요. {c['work_risk']}이 구체적인 주의점입니다. 예를 들어 새 일을 하나 더 맡을 때 예상 수입만 보고 이미 맡은 일의 마감과 필요한 도움을 놓치면 부담이 커질 수 있어요. 일을 못한다는 뜻보다, 잘한다는 이유로 모든 일을 맡지 않는 것이 중요한 사주예요.",
            f"억부 분류 {b['strength']} · 월지 {c['root']} · 월간 {c['outside']}")
    officers=[g for g in report['ten_gods'] if GROUP_OF[g['name']]=='관성']
    if b['available'] and '약' in b['strength'] and officers:
        add('responsibility-with-weak-support','책임만 늘어나는 자리에 주의',
            '까다로운 요구를 해결하려면 준비 시간과 도움도 필요한 사주로 읽어요. 할 일은 늘었는데 결정권은 없는 상황이 특히 불리할 수 있습니다. 부탁을 잘 들어주려다 책임을 혼자 떠안는 순간이 주의점이에요. 맡을 역할이 커지는 만큼 무엇을 결정할 수 있는지도 함께 봐야 합니다.',
            b['strength']+' · '+ ' · '.join(g['name'] for g in officers))
    if b['available'] and '강' in b['strength'] and c['root_group']=='비겁':
        add('self-direction-with-strong-support','자기 기준이 협업의 마찰로 바뀌는 지점',
            '내 방향을 지키는 힘이 동료와 함께 움직이는 모습에 더해져요. 그 힘은 든든하지만, 역할과 보상까지 혼자 정하는 태도로 바뀌면 마찰이 생길 수 있습니다. 이미 결론을 낸 뒤 동의를 구하는 것과, 상대의 선택을 실제로 함께 반영하는 것은 다른 대화예요.',
            b['strength']+' · 월지 '+c['root'])
    add('monthly-overreach','일에서 먼저 확인할 약점',c['work_risk']+'을 주의할 모습으로 읽어요. '+c['a']['test']+'가 실제 경험에서 확인할 질문입니다.',
        '월지 '+c['root']+' · 월간 '+c['outside'])
    add('private-expectation','가까운 사이에서 어긋나기 쉬운 표현',c['p']['risk']+'가 관계의 주의점이에요. '+c['p']['example'],
        describe(c['day'],'branch'))
    return points


def _support(receiver,other,receiver_name,other_name):
    b=receiver['balance'];known=other['element_total']==8
    result={'receiver':receiver_name,'other':other_name,'available':bool(b['available'] and b.get('yong_element')),
            'other_hour_known':known,'matches':[]}
    if not result['available']:
        result.update(status='unknown',text=f"{receiver_name}의 태어난 시간이 없어 전체 균형을 아직 비교할 수 없어요. {other_name}에게 어떤 도움이 되는 기운이 있는지 판단은 남겨두었지만, 아래의 애정 표현과 생활 방식은 확인한 정보로 비교했습니다.")
        return result
    e=b['yong_element'];matches=[{'position':row['label'],'part':'천간' if part=='stem' else '지지 본기',
                                 'character':row[part]['hanja'],'element':e}
                                for row in other['pillars'] if row['known'] for part in ['stem','branch'] if row[part]['element']==e]
    count=len(matches)
    if count:
        rc,oc=context(receiver),context(other);style,example=MANNER[e]
        text=f"{receiver_name}에게는 {ELEMENT[e]}의 기운이 균형을 돕는 방향으로 계산됐고, {other_name}의 사주에서도 그 기운이 확인돼요. 전통 상징을 생활에 옮기면 {style}를 떠올릴 수 있습니다. {receiver_name}은 {rc['p']['private']}이 중요한 사람이므로, {example}인지 함께 살펴볼 수 있어요. 한편 {other_name}에게는 {oc['p']['need']}도 중요합니다. 도움을 주려는 행동이 서로 원하는 방식으로 받아들여지는지는 별개의 문제예요."
        status='candidate_present'
    else:
        rc,oc=context(receiver),context(other)
        text=f"{receiver_name}에게 도움이 되는 방향으로 계산된 {ELEMENT[e]}의 기운은 {other_name}의 확인한 겉 구성에서 근거를 찾지 못했어요. 그래서 이 부분을 서로 채워준다고 설명하지 않았습니다. {receiver_name}에게는 {rc['p']['need']}, {other_name}에게는 {oc['p']['need']}이 중요해요. 함께 지내며 두 조건을 어떻게 지킬지 따로 맞춰보아야 하는 방향입니다. "+('겉에 안 보인다는 것이 숨은 구성까지 모두 없다는 뜻은 아니에요.' if known else '상대의 시간을 몰라, 전체를 비교한 결과는 아직 아니에요.')
        status='no_visible_candidate' if known else 'partial_no_visible_candidate'
    result.update(status=status,element=e,method=b['yong_method'],matches=matches,visible_count=count,
                  receiver_strength=b['strength'],other_strength=other['balance'].get('strength'),other_season=other['month']['season'],text=text)
    if count and not known:result['text']+=' 상대의 시간을 몰라 전체를 비교한 결과는 아직 아니에요.'
    return result


def build_compatibility(left,right):
    l,r=context(left),context(right)
    names=[left['profile']['name'],right['profile']['name']]
    if names[0]==names[1] or names[0]=='나':names[0]='첫 번째 사람'+(' · '+names[0] if names[0]!='나' else '')
    if names[0]==names[1] or names[1]=='나':names[1]='두 번째 사람'+(' · '+names[1] if names[1]!='나' else '')
    ln,rn=names
    directions=[_support(left,right,ln,rn),_support(right,left,rn,ln)]
    cross=[]
    for a in left['pillars']:
        if not a['known']:continue
        for b in right['pillars']:
            if not b['known']:continue
            for kind in branch_relations(a['branch']['hanja'],b['branch']['hanja']):
                cross.append({'left_position':a['position'],'right_position':b['position'],'left_label':a['label'],'right_label':b['label'],
                              'left':a['branch']['hanja'],'right':b['branch']['hanja'],'kind':kind,'primary':a['position']==b['position']=='day'})
    primary=[x for x in cross if x['primary']];adverse=[x for x in primary if x['kind'] in ADVERSE]
    harmony=[x for x in primary if x['kind']=='육합']
    risks=[];strengths=[]
    def finding(items,key,title,text,basis):
        items.append({'id':key,'title':title,'text':polish_particles(text),'basis':basis,'source_ids':SOURCE_IDS})
    if adverse:
        kinds=' · '.join(x['kind'] for x in adverse)
        finding(risks,'day-branch-tension','도움이 되는 점이 있어도, 가까워질수록 부딪힐 조건은 남아요',
                f"친밀한 관계를 읽는 두 사람의 글자에서는 충돌이나 긴장으로 분류하는 관계가 확인됐어요. 그래서 도움이 되는 기운이 있다는 말만으로 편안한 궁합이라고 설명하지 않습니다. {ln}은 {l['p']['private']}을 기대하고, {rn}은 {r['p']['private']}을 기대해요. "+(f"같은 기대를 가졌어도 {l['p']['risk']}을 서로에게 요구하면 다툼이 커질 수 있습니다." if l['private']==r['private'] else '한쪽이 원하는 배려를 내 방식으로 대신하면, 잘해주고도 서운하다는 말을 들을 수 있는 조합이에요.')+' 실제 다툼이나 이별이 정해졌다는 뜻은 아니에요.',
                '두 사람의 일지 · '+kinds)
    if harmony:
        finding(strengths,'day-branch-combination','서로를 연결하는 조건이 있지만, 기대까지 같지는 않아요',
                f"두 사람의 친밀함을 읽는 글자에는 연결과 조율로 분류하는 관계가 보여요. 다만 {ln}에게 편안함은 {l['p']['need']}, {rn}에게는 {r['p']['need']}에서 찾습니다. 가까워지기 좋은 조건과, 실제로 잘 맞추어 지내는 방법을 함께 봐야 해요.",
                l['day']['branch']['hanja']+'·'+r['day']['branch']['hanja']+' 육합')
    if l['private']==r['private']:
        finding(strengths,'shared-private-role','친밀함에서 중요하게 읽는 기준이 같아요',
                f"두 사람 모두 {l['p']['private']}을 중요하게 읽어요. {l['p']['example']} 이런 순간의 의미를 서로 비슷하게 받아들일 수 있다는 것이 장점입니다. 다만 같은 기대가 있다는 이유로 말하지 않아도 알 거라고 여기면, 둘 다 같은 배려를 기다릴 수 있어요.",
                '각 일지 십성 '+l['private'])
        finding(risks,'shared-private-risk','같은 약점을 서로에게 요구하는 경우',
                f"두 사람에게 공통으로 읽는 주의점은 {l['p']['risk']}예요. 예를 들어 둘 다 같은 방식의 배려를 기다리면서 먼저 표현하지 않으면, 같은 기준이 있어도 서운함이 쌓일 수 있습니다. 실제 경험에서 확인할 질문은 ‘{l['p']['test']}’입니다.",
                '각 일지 '+l['private'])
    else:
        finding(risks,'different-private-expectations','애정 표현의 기준이 서로 달라요',
                f"{ln}은 {l['p']['private']}을, {rn}은 {r['p']['private']}을 중요하게 읽어요. 서로의 방식이 다르므로 한쪽이 배려했다고 느낀 행동이 다른 쪽의 기대를 채우지 못할 수 있습니다. 예를 들어 {l['p']['example']} 반면 {rn}의 관점에서는 {r['p']['example']} 그래서 내 방식으로 챙기는 것과 상대가 원하는 것을 구분하는 지점이 마찰 조건이에요.",
                describe(l['day'],'branch')+' / '+describe(r['day'],'branch'))
    if l['root']!=r['root']:
        finding(strengths,'different-work-strengths','함께할 때 쓸 수 있는 강점이 서로 달라요',
                f"{ln}은 {l['a']['gift']}, {rn}은 {r['a']['gift']}을 강점으로 읽어요. 같은 일을 두 사람이 똑같이 잘해야 하는 조합보다는, 각자가 필요한 조건을 인정하며 역할을 나눌 때 차이를 쓸 수 있어요. 예를 들어 함께 여행을 준비한다면 누가 더 옳은 계획을 세우는지 겨루기보다, {ln}에게는 {l['a']['need']}, {rn}에게는 {r['a']['need']}이 남는지 보는 방식입니다.",
                '두 월지 역할 '+l['root']+' / '+r['root'])
    if {l['outside'],r['outside']}=={'편재','정재'}:
        finding(risks,'resource-expansion-maintenance','새 기회를 넓히는 마음과 유지하려는 마음이 달라요',
                f"{ln}에게는 {l['o']['need']}, {rn}에게는 {r['o']['need']}이 중요해요. 여행이나 공동 지출을 정할 때 한쪽의 즉흥 제안이 다른 쪽에는 계획의 흔들림으로 느껴질 수 있습니다. 한쪽은 즐거움을 더하려고 한 말인데 다른 쪽은 기존 약속을 무시했다고 느낄 수 있다는 차이예요. 돈을 잘 벌고 못 버는 평가보다 공동 생활의 합의에서 주의할 지점입니다.",
                '두 월간의 편재·정재 차이')
    status='도움이 되는 점과 충돌하는 조건이 함께 있어요' if adverse else '마음이 맞는 부분과 다른 부분을 함께 읽어요'
    chapters=[]
    def chapter(topic,title,paras):
        clean=[polish_particles(p) for p in paras];chapters.append({'topic':topic,'title':title,'paragraphs':clean,'body':'\n\n'.join(clean),'source_ids':SOURCE_IDS})
    chapter('support','서로에게 도움이 되는 방향은 같지 않을 수 있어요',[d['text'] for d in directions])
    chapter('strengths',('같은 배려를 알아보는 두 사람' if l['private']==r['private'] else '다른 강점을 함께 쓸 수 있는 순간'),[x['text'] for x in strengths] or [f"두 사람에게 직접 공통으로 확인한 애정의 기준이나 연결 관계는 이번 계산에서 뚜렷하지 않았어요. {ln}에게 중요한 {l['p']['need']}과 {rn}에게 중요한 {r['p']['need']}을 함께 지키는 방법은 생활에서 별도로 맞춰볼 부분이에요."])
    chapter('risks','안 맞을 수 있는 점을 숨기지 않고',[x['text'] for x in risks])
    chapter('affection','사랑과 대화에서 엇갈리는 장면',[
        f"{ln}: {PRIVATE[l['private']]} {l['p']['example']} 주의점은 {l['p']['risk']}입니다.",
        f"{rn}: {PRIVATE[r['private']]} {r['p']['example']} 주의점은 {r['p']['risk']}입니다.",
        '같은 사건을 두 입장에서 보면 이해하기 쉬워요. 한 사람이 고민을 말했을 때 원하는 것이 해결책인지, 설명인지, 함께 편을 들어주는 말인지가 다를 수 있습니다. 위에 적힌 두 사람의 기대를 각각 물어보고 비교할 장면이지, 이미 그런 다툼을 겪었다고 추정한 내용은 아니에요.'])
    chapter('money','돈·일정·공동생활을 같이 정할 때',[
        f"{ln}에게는 {l['a']['money']}이 중요해요. {work_story(l)} 돈을 함께 쓰더라도 {l['o']['need']}이 남아 있는지를 살펴볼 수 있습니다.",
        f"{rn}에게는 {r['a']['money']}이 중요해요. {work_story(r)} {r['o']['need']}이 빠지면 같은 비용을 두고도 불편함을 다르게 느낄 수 있습니다.",
        f"공동의 일을 맡는 경우 {ln}에게는 {l['a']['need']}, {rn}에게는 {r['a']['need']}이 있는지 비교할 수 있어요. 같은 목표를 정해도 먼저 필요한 조건이 다르면 일정을 짜거나 비용을 늘리는 과정에서 합의가 필요합니다. 한 사람은 아이디어, 다른 사람은 돈을 반드시 맡아야 한다고 역할을 고정하지는 않아요."])
    chapter('individual_risks','각자의 주의점이 관계에 더해질 때',[
        f"{ln}: "+' '.join(x['text'] for x in left.get('review_points',personal_review_points(left))[:2]),
        f"{rn}: "+' '.join(x['text'] for x in right.get('review_points',personal_review_points(right))[:2])])
    warnings=[]
    for name,report in zip(names,[left,right]):
        if not report['balance']['available']:warnings.append(name+'의 시간이 없어 전체 균형 비교는 아직 일부만 확인했어요.')
        if report.get('input_basis',{}).get('comparison',{}).get('changes_pillars'):warnings.append(name+'은 시간 보정 방식에 따라 일주·시주가 달라질 수 있어요. 현재 궁합은 경도 보정 명식을 사용했어요.')
    summary=(f"{ln}과 {rn}은 도움이 되는 방향이 있어도, 가까운 관계에서 충돌로 읽는 조건이 사라지지 않아요. "+('서로 같은 기대를 말하지 않고 기다리는 순간을 주의해요.' if l['private']==r['private'] else '배려했다고 느낀 행동이 상대에게는 서운할 수 있다는 차이를 함께 짚었어요.') if adverse else
             f"{ln}에게 중요한 것은 {l['p']['need']}, {rn}에게는 {r['p']['need']}이에요. 둘이 함께할 때 편안한 점과 어긋날 수 있는 장면을 나누어 풀었어요.")
    individuals=[]
    for name,report in zip(names,[left,right]):
        individual={**report,'partner_comparison_available':True}
        individuals.append({'name':name,'report':{**individual,'chapters':build_chapters(individual)}})
    return {'version':'1.1','title':'우리 궁합, 서로에게 편한 점과 부딪히는 점','summary':polish_particles(summary),'status':status,
            'people':individuals,
            'directions':directions,'cross_relations':cross,'primary_relations':primary,'strengths':strengths,'risks':risks,
            'chapters':chapters,'warnings':warnings,'source_ids':SOURCE_IDS,
            'scope':'각자의 명식·계절·강약·용신, 양방향 겉 오행의 대응, 일지와 지지의 두 글자 관계를 비교합니다. 숨은 글자의 가중치·합화·삼합·삼형 성립·공통 대운·궁합 점수·결혼이나 이별 결과는 판정하지 않았어요. 생활의 장면은 자체 해석의 예입니다.'}
