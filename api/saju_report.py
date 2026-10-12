"""Structured saju observations; explanations retain their calculation provenance."""
from collections import Counter
from korean_saju.solar_time.solar_time_correction import SolarTimeCorrection
from korean_saju import HapChungAnalyzer, IlganStrengthAnalyzer, SajuPosition
from api.birthplaces import birthplace, CATALOG

ELEMENT_NAMES={'목':'목 · 나무','화':'화 · 불','토':'토 · 흙','금':'금 · 금속','수':'수 · 물'}
TEN_GODS={
    '비견':('주도와 동료','자기 기준, 동료와의 수평적인 관계를 읽는 상징이에요.'),
    '겁재':('경쟁과 협력','같은 자원을 나누는 협력과 경쟁의 상징이에요.'),
    '식신':('표현과 창작','자기 생각과 재능을 말·글·기술·결과물로 표현하는 상징이에요.'),
    '상관':('새로운 표현','익숙한 형식을 바꾸고 자기 방식으로 표현하는 상징이에요.'),
    '편재':('기회와 확장','외부의 기회와 자원의 이동을 읽는 상징이에요.'),
    '정재':('관리와 지속','정해진 자원을 관리하고 꾸준히 유지하는 상징이에요.'),
    '편관':('도전과 책임','강한 요구와 도전적인 과제를 읽는 상징이에요.'),
    '정관':('규칙과 신뢰','사회적 기준, 역할과 책임의 상징이에요.'),
    '편인':('탐구와 관점','익숙한 방식 밖에서 배우고 해석하는 상징이에요.'),
    '정인':('배움과 지원','학습, 보호와 지원의 상징이에요.')}
POSITION_LABELS={SajuPosition.YEAR:'년주',SajuPosition.MONTH:'월주',SajuPosition.DAY:'일주',SajuPosition.HOUR:'시주'}


def build_report(saju, analysis, chart, profile):
    rows=[]
    visible_gods=Counter()
    for pos in SajuPosition:
        pillar=analysis.pillar_at(pos)
        if pillar is None:
            rows.append({'position':pos.name.lower(),'label':POSITION_LABELS[pos],'known':False})
            continue
        stem=pillar.cheon_gan; branch=pillar.ji_ji
        stem_god=analysis.cheon_gan_shipsin.get(pos)
        branch_god=analysis.ji_ji_shipsin[pos]
        if stem_god: visible_gods[stem_god.hangul]+=1
        visible_gods[branch_god.hangul]+=1
        rows.append({'position':pos.name.lower(),'label':POSITION_LABELS[pos],'known':True,
            'ganji':pillar.hanja,'reading':pillar.hangul,
            'stem':{'hanja':stem.hanja,'hangul':stem.hangul,'element':stem.o_haeng.hangul,'polarity':stem.yin_yang.hangul,'symbol':stem.description.split(' — ',1)[0],'ten_god':stem_god.hangul if stem_god else '일간'},
            'branch':{'hanja':branch.hanja,'hangul':branch.hangul,'element':branch.o_haeng.hangul,'ten_god':branch_god.hangul},
            'hidden_stems':[{'hanja':g.stem.hanja,'hangul':g.stem.hangul,'role':g.role.hangul,'element':g.stem.o_haeng.hangul} for g in branch.ji_jang_gan],
            'stage':analysis.sibiunseong[pos].hangul})
    total=sum(chart['element_counts'].values())
    elements=[{'element':e,'label':ELEMENT_NAMES[e],'count':n,'percent':round(n/total*100,1)} for e,n in chart['element_counts'].items()]
    gods=[{'name':name,'count':count,'keyword':TEN_GODS[name][0],'explanation':TEN_GODS[name][1]} for name,count in visible_gods.most_common()]
    relations=[{'kind':h.kind.hangul,'members':h.members,'type':'합'} for h in HapChungAnalyzer.detect_hap(saju)]
    relations += [{'kind':h.kind.hangul,'members':h.members,'type':'충형파해'} for h in HapChungAnalyzer.detect_chung_hyung(saju)]
    month=saju.month_pillar.ji_ji
    season=next(label for branches,label in [('寅卯辰','봄'),('巳午未','여름'),('申酉戌','가을'),('亥子丑','겨울')] if month.hanja in branches)
    balance={'available':False,'reason':'출생 시간이 없어 신강·신약, 격국과 용신은 확정하지 않았어요.'}
    if chart['hour_known']:
        strength=IlganStrengthAnalyzer.analyze(saju)
        yong=analysis.yongsin
        gyeok=analysis.jeonggyeok
        balance={'available':True,'strength':yong.eokbu.level.hangul,'strength_method':'득령·득지·인비 관계를 살피는 억부 분류',
            'month_supports':yong.eokbu.deuk_ryeong,'day_supports':yong.eokbu.deuk_ji,'ally_count':yong.eokbu.ally_count,
            'pattern':gyeok.gyeokguk.hangul,'pattern_basis':gyeok.basis,'pattern_established':gyeok.is_seonggyeok,
            'yong_element':yong.yong_o_haeng.hangul if yong.yong_o_haeng else None,'yong_method':yong.method.hangul,
            'hee_element':yong.hee_o_haeng.hangul if yong.hee_o_haeng else None,
            'season_state':yong.johu_class.state.hangul,
            'secondary_strength':strength.level.hangul,'secondary_score':strength.total,
            'secondary_weights':{'월지':3.5,'일지':1.5,'시지':1,'년지':1,'년간':1,'월간':1,'시간':1},
            'secondary_components':{'월지':strength.month_branch_score,'일지':strength.day_branch_score,'시지':strength.hour_branch_score,'년지':strength.year_branch_score,'년간':strength.year_stem_score,'월간':strength.month_stem_score,'시간':strength.hour_stem_score,'보정':strength.adjustment},
            'secondary_reason':strength.reason,
            'secondary_note':'계산 엔진의 보조 배점이에요. 명식의 좋고 나쁨이나 운세 점수가 아니며, 합화·통근 가정에 따라 억부 분류와 다를 수 있어요.',
            'method_note':'korean-saju 0.3.0의 규칙 결과예요. 유파에 따라 격국·용신 선택이 달라질 수 있어요.'}
    counts=' · '.join(f'{e} {n}' for e,n in chart['element_counts'].items())
    god_text=' · '.join(f'{g["name"]} {g["count"]}' for g in gods)
    relation_text=' · '.join(f'{r["members"]} {r["kind"]}' for r in relations) or '검출한 합·충·형·파·해 없음'
    evidence=[
        {'id':'daymaster','label':'일간','text':f'일간 {saju.day_stem.hanja}({saju.day_stem.hangul}) · {saju.day_stem.yin_yang.hangul}{saju.day_stem.o_haeng.hangul}. {chart["day_symbol"]}의 상징.','source_id':'saju-daymaster'},
        {'id':'month','label':'월지와 계절','text':f'월지 {month.hanja}({month.hangul}) · {season}. 절기 월 기준이며 실제 출생일의 기온을 뜻하지 않음.','source_id':'saju-calendar'},
        {'id':'counts','label':'오행 분포','text':f'{counts}. 겉으로 드러난 {total}글자의 개수이며 계절·지장간 가중치를 합산하지 않음.','source_id':'saju-structure'},
        {'id':'ten_gods','label':'십성 구성','text':god_text+'. 일간을 제외한 천간과 지지 본기에서 계산. 지장간 중복 집계 없음.','source_id':'saju-ten-gods'},
        {'id':'relations','label':'명식 내부 관계','text':relation_text+'. 검출은 관계표에 따른 것. 합화 성립이나 사건·관계 성패를 확정하지 않음.','source_id':'saju-internal-relations'}]
    if balance['available']:
        evidence.append({'id':'balance','label':'강약·격국·용신','text':f"억부 분류 {balance['strength']} · 격국 {balance['pattern']}({balance['pattern_basis']}) · 용신 {balance['yong_element']}({balance['yong_method']}) · 희신 {balance['hee_element']}. 계절 상태 {balance['season_state']}. 오행 개수만으로 판단하지 않음.",'source_id':'saju-yong'})
    else:
        evidence.append({'id':'balance','label':'강약·격국·용신','text':balance['reason'],'source_id':'saju-yong'})
    corrected=SolarTimeCorrection.to_apparent_solar_time(saju.kst_moment,longitude=saju.longitude)
    place=birthplace(profile.city)
    region=next(r['label'] for r in CATALOG['regions'] if r['id']==place['region'])
    place_label=place['label'] if profile.city in ['seoul','busan','jeju'] else region+' '+place['label']
    input_basis={'calendar':'양력','timezone':'한국 표준시 UTC+9','longitude':saju.longitude,
                 'birthplace_id':profile.city,'birthplace_label':place_label,'coordinate_basis':place['basis'],
                 'entered_time':profile.birth_time,'corrected_time':corrected.strftime('%H:%M:%S') if profile.birth_time else None,
                 'corrected_date':corrected.date().isoformat() if profile.birth_time else None,
                 'offset_minutes':round(SolarTimeCorrection.minutes_offset_from_kst(saju.longitude),4),
                 'equation_of_time_applied':False,'day_boundary':'야자시 분리',
                 'note':'출생지 경도로 보정한 평균 태양시 기준이며 균시차는 적용하지 않았어요. 다른 만세력과 비교할 때 양력·음력, 보정 방식과 시주가 같은지 먼저 확인해 주세요.'}
    return {'version':'8.3','profile':{'name':profile.surname+profile.name or '나','birth_date':profile.birth_date.isoformat(),'birth_time':profile.birth_time,'city':place_label,'calendar':'양력'},'input_basis':input_basis,
        'pillars':rows,'elements':elements,'element_total':total,'ten_gods':gods,'relations':relations,
        'month':{'hanja':month.hanja,'hangul':month.hangul,'season':season},'balance':balance,'evidence':evidence,
        'interpretation_frame':{'kind':'birth_chart','uses_current_date':False,'includes_luck_cycles':False,'label':'타고난 사주 · 원국 해석','description':'출생 당시의 사주 구성을 읽는 풀이예요. 오늘의 운세·대운·연운은 포함하지 않았어요.'},
        'interpretation_notice':'출생 당시의 사주 글자와 전통 해석을 연결한 원국 풀이예요. 성향과 역할의 특징을 설명하며, 현재 겪는 일이나 미래의 사건을 확정한 내용은 아닙니다.',
        'interpretation_source_ids':['saju-interpretation-rules','saju-classical-framework'],
        'coverage':['명식','십성','지장간','십이운성','오행 분포','합충형파해']+(['신강·신약','격국','용신·희신'] if balance['available'] else []),
        'scope':'원국의 구조를 읽는 사주 분석이에요. 대운·세운, 사건 시기, 재산·건강·결혼 결과는 계산하거나 예측하지 않았어요.'}


def build_chapters(report):
    from api.interpretation import build_narrative
    return build_narrative(report)
