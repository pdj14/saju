"""Calculated ten-year Daewoon and explicitly authored age-band explanations."""
from korean_saju import Daewoon, Gender, ShipsinCalculator
from korean_saju.calendar.solar_term import SolarTermType
from datetime import timezone
from api.chart_context import context, GODS, GROUP_OF, role_for, polish_particles
from api.reading_scenes import scene
from api.reader_language import ELEMENT

STAGES=[('growth','성장기',0,20),('youth','청년기',20,40),('middle','중년기',40,60),('later','노년기',60,100)]
GROUP_WORD={'비겁':'내 선택과 동료 관계','식상':'배운 것을 표현하고 만드는 일','재성':'돈·시간과 실제 결과','관성':'맡은 책임과 사회의 기준','인성':'배움과 도움받을 바탕'}
AGE_EXAMPLE={
 'growth':{'비겁':'학교나 모임에서 자기 의견을 말하고 친구와 역할을 나누는 장면','식상':'배운 내용을 발표하거나 취미로 만든 것을 보여주는 장면','재성':'용돈과 시간을 나누어 쓰며 약속을 지키는 장면','관성':'학교의 규칙이나 맡은 역할을 이해하고 지키는 장면','인성':'처음 배우는 내용에 충분한 설명과 도움을 받는 장면'},
 'youth':{'비겁':'진로를 직접 고르거나 동료와 각자의 몫을 정하는 장면','식상':'공부한 내용을 포트폴리오나 실제 업무로 보여주는 장면','재성':'첫 수입과 생활비, 하고 싶은 일의 비용을 함께 정하는 장면','관성':'직장이나 사회에서 새로운 역할을 맡고 기준에 맞추는 장면','인성':'자격 공부나 멘토의 조언으로 필요한 바탕을 쌓는 장면'},
 'middle':{'비겁':'경험을 바탕으로 자기 방향을 정하고 협업의 권한을 나누는 장면','식상':'쌓은 기술을 결과물이나 후배 교육으로 전달하는 장면','재성':'수입뿐 아니라 고정 비용과 오래 유지할 계획을 함께 살피는 장면','관성':'커진 역할에서 책임과 결정권을 함께 정리하는 장면','인성':'익숙한 일을 다시 배우고 다른 관점의 조언을 받아들이는 장면'},
 'later':{'비겁':'나의 생활 방식을 지키면서 주변 사람과 서로 돕는 장면','식상':'취미와 경험을 글·작품·이야기로 나누는 장면','재성':'생활에 쓸 시간과 비용을 무리 없이 유지하는 장면','관성':'내가 맡을 일과 다른 사람에게 넘길 일을 구분하는 장면','인성':'배우는 즐거움과 도움을 주고받는 관계를 이어가는 장면'}}

def age_label(months):
    year,month=divmod(months,12)
    return f'{year}세'+(f' {month}개월' if month else '')


def build_luck_cycles(saju,profile,terms,report):
    missing=[]
    if not profile.birth_time:missing.append('태어난 시간')
    if not profile.gender:missing.append('대운 계산 기준(남성·여성)')
    if missing:return {'available':False,'missing':missing,'reason':' · '.join(missing)+'을 입력하면 10년 대운과 나이대별 흐름을 함께 볼 수 있어요.','periods':[],'stages':[]}
    calculation=Daewoon.compute(saju=saju,gender=Gender(profile.gender),solar_terms=terms,count=10)
    # Only the first engine entry carries the month offset; retain it for every
    # subsequent period and normalize an offset rounded to 12 months.
    first=calculation.entries[0];start_months=first.start_age*12+first.start_months_offset
    c=context(report);b=report['balance'];useful=b.get('yong_element');helper=b.get('hee_element')
    periods=[]
    for i,entry in enumerate(calculation.entries):
        pillar=entry.gan_ji;stem=pillar.cheon_gan;branch=pillar.ji_ji
        sg=ShipsinCalculator.for_cheon_gan(saju.day_stem,stem).hangul
        bg=ShipsinCalculator.for_ji_ji(saju.day_stem,branch).hangul
        elements=[stem.o_haeng.hangul,branch.o_haeng.hangul]
        matched=[e for e in dict.fromkeys(elements) if e in [useful,helper]]
        if useful in elements:
            support=f"태어난 사주에서 균형을 도울 방향으로 고른 {ELEMENT[useful]}의 기운이 이 시기에 함께 보여요. 필요한 바탕을 갖추는 쪽으로 읽을 수 있지만, 이 기간의 모든 일이 잘된다고 정하는 뜻은 아니에요."
        elif helper in elements:
            support=f"전체 균형을 함께 돕는 {ELEMENT[helper]}의 기운이 보여요. 필요한 바탕을 보태는 쪽으로 읽지만, 이것만으로 모든 일이 잘되는 시기라고 정하지는 않았어요."
        else:
            support=f"이 시기에는 {GODS[bg]['gift']}을 쓰는 모습에 초점을 두어요. 균형을 돕는 방향으로 고른 {ELEMENT[useful]}의 기운은 겉에 직접 보이지 않아, 활동이 늘어나는 만큼 이를 받쳐줄 조건도 따로 필요하다고 읽습니다. 나쁜 일이 생긴다고 정한 시기는 아니에요."
        begin=start_months+120*i;end=begin+120
        calculation_text=f"{pillar.hangul}({pillar.hanja}) · 일간 {saju.day_stem.hanja}({saju.day_stem.hangul}) · 천간 {sg} · 지지 {bg} · 오행 {' · '.join(elements)}"
        paragraphs=[f"이 10년에는 {GROUP_WORD[GROUP_OF[bg]]}이 더 중요한 주제로 들어와요. {GODS[bg]['gift']}을 장점으로 읽고, 과하면 {GODS[bg]['risk']}이 나타나는지를 주의할 부분으로 보아요.",
            scene(bg),f"여기에 {GODS[sg]['gift']}도 더해집니다. {scene(sg,'work')}",support]
        periods.append({'index':i,'start_months':begin,'end_months':end,'start_age':begin//12,'start_months_offset':begin%12,'age_label':age_label(begin)+' ~ '+age_label(end)+' 전',
                        'ganji':pillar.hanja,'reading':pillar.hangul,'calculation_text':calculation_text,'stem_god':sg,'branch_god':bg,'elements':elements,'support_elements':matched,
                        'title':GROUP_WORD[GROUP_OF[bg]]+'에 초점을 두는 흐름','paragraphs':paragraphs})
    for i,p in enumerate(periods):
        if i+1<len(periods):
            nxt=periods[i+1]
            p['transition']=f"다음 {nxt['age_label']} 시기에는 {GROUP_WORD[GROUP_OF[p['branch_god']]]}에서 {GROUP_WORD[GROUP_OF[nxt['branch_god']]]} 쪽으로 강조점이 이동해요. 지금의 ‘{GODS[p['branch_god']]['need']}’과 다음의 ‘{GODS[nxt['branch_god']]['need']}’을 비교하면 차이를 이해하기 쉬워요."
        else:p['transition']='다음 시기까지 계속 좋거나 나쁘다고 연장해 단정하지 않고, 표시한 10년 범위에서 읽었어요.'
    stages=[]
    for key,label,start,end in STAGES:
        overlapping=[p for p in periods if p['start_months']<end*12 and p['end_months']>start*12]
        paras=[]
        if key=='growth' and start_months>0:
            paras.append(f"첫 대운은 {age_label(start_months)} 무렵에 시작해요. 그 전에는 10년 대운을 임의로 붙이지 않고 타고난 사주를 바탕으로 읽습니다. 이 명식에서는 {GODS[c['root']]['gift']}과 {GODS[c['private']]['private']}이 성장 과정에서도 함께 살펴볼 주제예요.")
        for p in overlapping:
            lo=max(start*12,p['start_months']);hi=min(end*12,p['end_months']);group=GROUP_OF[p['branch_god']]
            balance_text=(f"특히 균형을 돕는 {ELEMENT[useful]}의 기운이 함께 보여 필요한 바탕을 보태는 쪽으로 비교할 수 있어요." if useful in p['elements'] else
                          f"균형을 함께 돕는 {ELEMENT[helper]}의 기운이 보여요." if helper in p['elements'] else f"내 힘을 쓰는 동안 태어난 사주에서 필요한 방향으로 본 {ELEMENT[useful]}의 바탕도 함께 살펴야 하는 흐름이에요.")
            paras.append(f"{age_label(lo)}부터 {age_label(hi)} 전까지는 한 시기로 이어져요. 이때 두드러지는 주제는 {GROUP_WORD[group]}입니다. {GODS[p['branch_god']]['gift']}을 장점으로, {GODS[p['branch_god']]['risk']}을 주의할 점으로 읽을 수 있어요. 생활의 예로는 {AGE_EXAMPLE[key][group]}을 떠올리면 쉬워요. {balance_text}")
        if len(overlapping)>1:
            p,n=overlapping[0],overlapping[-1]
            paras.append(f"이 나이대 안에서도 앞부분과 뒷부분은 강조점이 달라요. {GROUP_WORD[GROUP_OF[p['branch_god']]]}을 다루던 흐름에 {GROUP_WORD[GROUP_OF[n['branch_god']]]}이라는 주제가 더해집니다. ‘나이 들면 무조건 좋아진다’는 말보다 어떤 일을 통해 힘을 쓰고 어떤 바탕을 필요로 하는지가 바뀌는 이야기로 이해하면 좋습니다.")
        stages.append({'key':key,'label':label,'age_label':f'{start}~{end-1}세' if key!='later' else '60세 이후 · 99세까지 표시','paragraphs':paras,'period_indices':[p['index'] for p in overlapping]})
    birth_utc=saju.kst_moment.astimezone(timezone.utc)
    boundary=(terms.term_after(birth_utc,type=SolarTermType.JEOL) if calculation.forward else terms.term_at_or_before(birth_utc,type=SolarTermType.JEOL))
    result={'available':True,'forward':calculation.forward,'direction':'순행' if calculation.forward else '역행','criterion':profile.gender,'year_stem_polarity':saju.year_pillar.cheon_gan.yin_yang.hangul,
            'days_to_boundary':round(calculation.days_to_boundary,6),'boundary':boundary.datetime.isoformat(),'start_months':start_months,'start_label':age_label(start_months),
            'periods':periods,'stages':stages,'source_ids':['saju-luck-cycles'],
            'method':'연간 음양과 선택한 남성·여성 기준으로 순행·역행을 정하고, 출생부터 다음 또는 직전 절기(절)까지의 일수를 3으로 나누어 첫 대운 나이를 계산합니다. 월 단위로 반올림한 뒤 10년씩 이어 표시해요.',
            'scope':'나이는 출생 후 경과한 나이이며 첫 시작은 월 단위 근사예요. 성장기·청년기·중년기·노년기는 읽기 편하게 나눈 구간입니다. 대운 글자와 일간의 십성, 원국 용신·희신의 포함 여부를 비교한 풀이이며, 대운의 합충·합화·세운과 사건 결과는 판정하지 않았어요. 100년 표시는 수명 예측이 아닙니다.'}
    for obj in periods+stages:obj['paragraphs']=[polish_particles(p) for p in obj['paragraphs']]
    for obj in periods:obj['transition']=polish_particles(obj['transition'])
    return result
