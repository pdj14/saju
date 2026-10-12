"""Fresh personal prose from allowlisted calculations, never legacy chapters.

The skill is part of the runtime prompt, not merely an editor instruction.
Only shared vocabulary and calculated observations enter first-generation calls.
"""
import asyncio
import copy
import hashlib
import json
import re
import time
from pathlib import Path

import httpx
from pydantic import BaseModel, Field
from api.model_provider import CONFIG, complete

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/moa-readings/SKILL.md'
VERSION = 'fresh-reading-1'
CONTEXT_SIZE = 12288
OUTPUT_LIMIT = 3000
BATCH_SIZE = 2
CACHE = {}
SAJU = {
    'overview':'한마디로 어떤 사람인가? 다른 특징들이 어떻게 함께 연결되는가?',
    'disposition':'일에서 드러나는 모습과 가까운 사이의 기대는 어떻게 다른가?',
    'work':'어떤 업무에서 몰입하며, 어떤 업무 조건에서는 강점을 쓰기 어려운가?',
    'career':'조직에서 책임·권한·평가를 만났을 때 장점과 부담은 무엇인가?',
    'money':'어떤 활동이 수입과 연결되고, 시간·비용 부담은 어디서 생기는가?',
    'relationships':'어떤 애정 표현과 상대 태도가 편하며, 어디에서 오해가 생기는가?',
    'family':'가족에게 기대하거나 책임지려는 방식과 경계의 문제는 무엇인가?',
    'friends':'친구·동료와 어떤 관계를 편하게 느끼고, 어떤 태도에서 마찰이 생기는가?',
    'shadow':'다른 장의 장점을 반복하지 말고, 실제로 주의할 약점과 발생 조건을 솔직히 짚어라.',
    'elements':'실제 오행 구성과 계절을 연결해 설명하되 개수가 성격 점수라는 인상을 주지 마라.',
    'balance':'선택된 균형 방향을 배움·도움·환경의 구체적인 의미로 풀고 강약을 능력으로 바꾸지 마라.'}
STARS = {
    'sun':'태양의 실제 별자리: 자신을 표현하고 중심을 잡는 방식과 과해지는 모습.',
    'moon':'달의 실제 별자리: 가까운 관계에서 편안함을 느끼는 방식. 미계산이면 짧게 유보.',
    'mercury':'수성의 실제 별자리: 정보를 이해하고 말하는 방식, 대화에서 생기는 오해.',
    'venus':'금성의 실제 별자리: 취향·애정의 표현과 상대에게 기대하는 배려.',
    'mars':'화성의 실제 별자리: 행동을 시작하고 추진하며 의견 충돌에 대응하는 방식.',
    'inside_outside':'태양과 달의 공통점·차이를 실제 두 별자리로 엮어 설명. 달이 없으면 유보.',
    'aspects':'계산된 개인 천체 사이의 각도를 역할과 연결해 풀어라. 없다면 관계를 꾸미지 마라.'}
STAR_THEMES = {
    'overview':'여러 천체의 실제 별자리와 계산된 각도를 함께 읽어 이 사람의 핵심 특징 2~3개를 연결하세요. 태양은 이렇고 달은 저렇다는 목록 대신, 겉으로 선택하는 방향과 마음이 원하는 것, 생각과 행동이 함께 움직이거나 엇갈리는 이유를 하나의 이야기로 풀어주세요. 별자리 이름은 근거가 되는 대목에서 자연스럽게 밝히세요.',
    'work':'수성·화성·태양의 실제 배치와 관련된 각도를 묶어 일·적성·협업의 종합 해석을 작성하세요. 정보를 이해하는 방식이 행동과 연결될 때 어떤 업무에서 강점이 되고, 어떤 환경에서 어려워지는지 구체적인 생활 예로 설명하세요. 하우스·중천·목성·토성을 계산하지 않은 직업 성취나 재산 규모는 예측하지 마세요.',
    'relationships':'달·금성·화성의 실제 배치와 관련된 각도를 엮어 사랑·관계의 종합 해석을 작성하세요. 편안함을 느끼는 조건과 애정 표현이 같거나 다를 때 어떤 오해가 생기는지, 편한 상대의 태도와 부딪히기 쉬운 태도를 함께 풀어주세요. 특정 태양 별자리끼리 좋거나 나쁘다고 단정하지 마세요.',
    'shadow':'전체 배치의 다른 요구와 실제 계산된 긴장을 엮어 반복하기 쉬운 약점과 조절할 지점을 설명하세요. 앞 장의 칭찬을 반복하지 말고, 어떤 상황에서 문제가 커지고 다른 선택이 도움이 되는지 일상 예로 설명하세요. 각도가 없다면 없는 관계를 발명하지 말고 확인된 별자리의 서로 다른 요구만 비교하세요.'}
PAIR = {
    'support':'양방향 보완 조건을 각각 구분해 설명. 양쪽에 같은 도움이 있다고 만들지 마라.',
    'strengths':'두 사람의 일하는 방식과 가까운 관계에서의 기대를 비교해 함께할 때의 장점을 설명.',
    'risks':'가까운 관계에 해당하는 자리에서 계산된 마찰과 서로의 기대 차이를 솔직히 설명. 보완 조건으로 충돌을 덮지 마라.',
    'affection':'누가 어떤 표현을 기대하고, 같은 말을 두 사람이 어떻게 다르게 받아들일 수 있는가?',
    'money':'각자의 일하는 방식과 자원 역할을 연결해 공동 비용·일정·역할에서의 차이를 설명.',
    'individual_risks':'각자의 약점이 상대의 어떤 부분과 만날 때 부담이 커지는지 구분해서 설명.'}
PERSON_TOPICS = ['overview','work','money','relationships','shadow','balance']
PLANETS = {'sun':'Sun','moon':'Moon','mercury':'Mercury','venus':'Venus','mars':'Mars'}
TERMS = ['일간','월지','월간','일지','십성','식상','재성','관성','비겁','인성','신약','신강','억부','격국','용신','희신','지장간',
         '비견','겁재','식신','상관','편재','정재','편관','정관','편인','정인']
SIGNS = {
    '양자리':{'strength':['시작','직접 시도','빠른 반응'],'risk':['성급한 결론','상대 속도 놓침']},
    '황소자리':{'strength':['꾸준함','감각','익숙한 기반'],'risk':['변경에 시간 필요','고집']},
    '쌍둥이자리':{'strength':['호기심','정보 교환','여러 관점'],'risk':['관심 분산','말과 지속의 차이']},
    '게자리':{'strength':['돌봄','친밀함','안전한 관계'],'risk':['걱정이 간섭으로 변함','서운함 표현 지연']},
    '사자자리':{'strength':['자기 표현','존중','앞에 나서기'],'risk':['인정에 대한 기대','의견 차이를 무시로 받아들임']},
    '처녀자리':{'strength':['관찰','정리','실용적인 개선'],'risk':['세부 확인이 결정 지연','지적이 평가로 들림']},
    '천칭자리':{'strength':['조율','공정함','상대 관점'],'risk':['결정 지연','갈등을 피하며 기대 숨김']},
    '전갈자리':{'strength':['깊이','집중','신뢰'],'risk':['확인과 통제','쉽게 놓지 못함']},
    '사수자리':{'strength':['탐색','자유','넓은 가능성'],'risk':['가능성 확대','세부 약속 놓침']},
    '염소자리':{'strength':['책임','지속','구체적 목표'],'risk':['성과로 마음 평가','자기 부담 확대']},
    '물병자리':{'strength':['독립','새 관점','기존 방식 재검토'],'risk':['거리감','다른 사람의 익숙한 방식 무시']},
    '물고기자리':{'strength':['상상','공감','맥락 이해'],'risk':['자기 경계 불명확','마음을 말로 확정하기 어려움']}}
PLAIN = {
    '비견':'자기 선택과 독립','겁재':'동료와 협력·경쟁','식신':'생각을 표현하고 만드는 활동','상관':'문제를 찾아 방법을 바꾸는 표현',
    '편재':'새 기회와 수요·자원 연결','정재':'일정·비용과 결과를 유지하는 관리','편관':'까다로운 과제에 대응하는 책임','정관':'약속과 평가 기준을 지키는 책임',
    '편인':'다른 관점을 탐구하는 배움','정인':'이해의 바탕과 도움을 얻는 배움',
    '일간':'나를 읽는 기준','월지':'태어난 달의 아래쪽 배치','월간':'태어난 달의 위쪽 배치','일지':'태어난 날의 가까운 관계 배치',
    '십성':'기준과 각 글자 사이의 역할','식상':'표현과 제작','재성':'수요와 자원','관성':'책임과 기준','비겁':'자기 선택과 동료','인성':'배움과 도움',
    '신약':'받쳐주는 관계가 상대적으로 적은 분류','신강':'받쳐주는 관계가 상대적으로 많은 분류','억부':'받쳐주는 힘과 밖에 쓰는 힘의 비교',
    '격국':'달의 배치를 읽는 구조','용신':'계산에서 선택한 균형 방향','희신':'보조로 도움이 되는 방향','지장간':'아래 글자 안의 숨은 구성'}


def plain(value):
    if isinstance(value,list):return [plain(v) for v in value]
    if isinstance(value,dict):return {plain(k):plain(v) for k,v in value.items()}
    if not isinstance(value,str):return value
    # Long terms first; preserve normal words such as '일관성' and '상관없다'.
    for word,replacement in sorted(PLAIN.items(),key=lambda x:len(x[0]),reverse=True):
        value=re.sub(r'(?<![가-힣])'+re.escape(word)+(r'(?!없|이 없|없이|하지)' if word=='상관' else ''),lambda m:replacement,value)
    return re.sub(r'[\u4e00-\u9fff]','',value)


def writing_calculations(service,data):
    """Semantic, structured facts for prose; original chart remains in UI.

    This is vocabulary normalization, not a previous personalized paragraph.
    It prevents the writer from copying the traditional notation into prose.
    """
    result=copy.deepcopy(data)
    charts=[p['chart'] for p in result['people']] if service=='compatibility' else [result] if service=='saju' else []
    for chart in charts:
        for row in chart['pillars']:
            for key in ['ganji','reading','stage']:row.pop(key,None)
            for part in ['stem','branch']:
                if part not in row:continue
                for key in ['hanja','hangul']:row[part].pop(key,None)
            for hidden in row.get('hidden_stems',[]):hidden.pop('hanja',None);hidden.pop('hangul',None)
        chart['balance'].pop('pattern',None);chart['balance'].pop('pattern_basis',None)
        chart['month']=pick(chart['month'],['season'])
        chart['evidence']=[pick(e,['id','label','source_id']) for e in chart['evidence']]
    result['evidence']=[pick(e,['id','label','source_id']) for e in result['evidence']]
    if service=='compatibility':
        for r in result['primary_relations']+result['cross_relations']:
            for key in ['left','right']:r.pop(key,None)
        for d in result['directions']:
            for m in d['matches']:m.pop('character',None)
    return plain(result)


class Chapter(BaseModel):
    topic: str
    title: str = Field(min_length=5, max_length=90)
    paragraphs: list[str] = Field(min_length=1, max_length=8)
    reflection: str = Field(min_length=8, max_length=220)
    evidence_ids: list[str] = Field(min_length=1, max_length=6)


class Batch(BaseModel):
    title: str = Field(min_length=5, max_length=40)
    summary: str = Field(min_length=20, max_length=180)
    chapters: list[Chapter]


class Followup(BaseModel):
    answer: str = Field(min_length=50, max_length=3000)
    evidence_ids: list[str] = Field(min_length=1, max_length=8)


class LifeInterval(BaseModel):
    period_index: int
    paragraph: str = Field(min_length=100,max_length=1000)


class LifeDraft(BaseModel):
    title: str = Field(min_length=5,max_length=80)
    intro: str = Field(min_length=60,max_length=450)
    before_first_cycle: str | None = None
    intervals: list[LifeInterval]


def pick(obj, keys):
    return {k:copy.deepcopy(obj[k]) for k in keys if k in obj}


def raw_saju(report, *, include_cycles=False):
    # Deliberate allowlist: new legacy prose fields cannot silently enter prompts.
    data = pick(report, ['profile','input_basis','pillars','elements','element_total','month','balance','relations'])
    data['input_basis'] = pick(report['input_basis'], ['calendar','timezone','longitude','entered_time','corrected_time','corrected_date','offset_minutes','equation_of_time_applied','day_boundary'])
    data['ten_gods'] = [pick(g,['name','count']) for g in report['ten_gods']]
    data['balance'] = pick(report['balance'], ['available','strength','pattern','pattern_basis','pattern_established','yong_element','yong_method','hee_element','season_state','month_supports','day_supports'])
    data['evidence'] = [copy.deepcopy(e) for e in report['evidence'] if e['id'] in {'daymaster','month','counts','ten_gods','relations','balance','time_basis'}]
    if include_cycles:
        cycles = report.get('luck_cycles', {})
        data['luck_cycles'] = pick(cycles, ['available','missing','reason','direction','criterion','start_months','start_label','method','scope'])
        data['luck_cycles']['periods'] = [pick(p, ['index','start_months','end_months','age_label','stem_god','branch_god','elements','support_elements']) for p in cycles.get('periods', [])]
        if cycles.get('available'):
            data['evidence'] += [{'id':'cycle:'+str(p['index']), 'label':p['age_label'], 'text':json.dumps(p,ensure_ascii=False), 'source_id':'saju-luck-cycles'} for p in data['luck_cycles']['periods']]
    return data


def life_stage_data(report, stage):
    """One age band, clipped to real month boundaries; no authored age prose."""
    from api.luck_cycles import STAGES, age_label
    data = raw_saju(report, include_cycles=True)
    start, end = next((lo*12, hi*12) for key, _, lo, hi in STAGES if key==stage['key'])
    periods=[]
    for p in data['luck_cycles']['periods']:
        lo, hi = max(start,p['start_months']), min(end,p['end_months'])
        if lo < hi:
            periods.append({**p, 'stage_start_months':lo,'stage_end_months':hi,
                            'stage_age_label':age_label(lo)+' ~ '+age_label(hi)+' 전'})
    data['luck_cycles']['periods']=periods
    data['life_stage']={**pick(stage,['key','label','age_label']), 'start_months':start,'end_months':end,
                        'before_first_cycle_until':min(end,data['luck_cycles']['start_months']) if start<data['luck_cycles']['start_months'] else None}
    ids={'cycle:'+str(p['index']) for p in periods}
    data['evidence']=[e for e in data['evidence'] if not e['id'].startswith('cycle:') or e['id'] in ids]
    data['evidence'].append({'id':'life:'+stage['key'],'label':stage['label']+'의 계산 범위',
                             'text':json.dumps(data['life_stage'],ensure_ascii=False),'source_id':'saju-luck-cycles'})
    return data


def raw_stars(astrology, profile):
    data = pick(astrology,['positions','aspects','aspect_orb','hour_known','sun_boundary_day','method','scope'])
    data['profile'] = pick(profile,['name','birth_date','birth_time','city'])
    personal = {'태양','달','수성','금성','화성'}
    data['aspects'] = [a for a in data['aspects'] if a['left'] in personal and a['right'] in personal]
    data['evidence'] = [{'id':'planet:'+p['key'],'label':p['label'],'text':json.dumps(p,ensure_ascii=False),'source_id':'stars-natal'} for p in data['positions']]
    data['evidence'] += [{'id':'aspect:'+str(i),'label':'천체 관계','text':json.dumps(a,ensure_ascii=False),'source_id':'stars-aspects'} for i,a in enumerate(data['aspects'])]
    data['evidence'].append({'id':'astrology_scope','label':'계산 범위','text':data['scope']+' 시간 입력: '+str(data['hour_known']),'source_id':'stars-time'})
    return data


def raw_pair(comparison):
    data = {'people':[{'name':p['name'],'chart':raw_saju(p['report'])} for p in comparison['people']],
            'directions':[pick(d,['receiver','other','available','other_hour_known','matches','status','element','method','visible_count','receiver_strength','other_strength','other_season']) for d in comparison['directions']],
            'primary_relations':copy.deepcopy(comparison['primary_relations']),
            'cross_relations':copy.deepcopy(comparison['cross_relations']), 'scope':comparison['scope']}
    data['evidence'] = [{**e,'id':side+':'+e['id'],'label':p['name']+' · '+e['label']} for side,p in zip(['left','right'],data['people']) for e in p['chart']['evidence']]
    data['evidence'] += [{'id':'support:'+str(i),'label':'보완 방향','text':json.dumps(d,ensure_ascii=False),'source_id':'saju-compatibility-rules'} for i,d in enumerate(data['directions'])]
    data['evidence'] += [{'id':'relation:'+str(i),'label':'두 사람 일지 관계','text':json.dumps(r,ensure_ascii=False),'source_id':'saju-relations'} for i,r in enumerate(data['primary_relations'])]
    return data


def calculate_pair(left,right):
    """Calculate comparisons without running any legacy narrative builder."""
    from api.compatibility import branch_relations,SOURCE_IDS
    names=[left['profile']['name'],right['profile']['name']]
    if names[0]=='나' or names[0]==names[1]:names[0]='첫 번째 사람'
    if names[1]=='나' or names[0]==names[1]:names[1]='두 번째 사람'
    directions=[]
    for receiver,other,receiver_name,other_name in [(left,right,*names),(right,left,names[1],names[0])]:
        b=receiver['balance'];known=other['element_total']==8
        d={'receiver':receiver_name,'other':other_name,'available':bool(b['available'] and b.get('yong_element')),'other_hour_known':known,'matches':[]}
        if not d['available']:d['status']='unknown'
        else:
            element=b['yong_element']
            d['matches']=[{'position':row['label'],'part':'천간' if part=='stem' else '지지 본기','character':row[part]['hanja'],'element':element}
                          for row in other['pillars'] if row['known'] for part in ['stem','branch'] if row[part]['element']==element]
            d.update(element=element,method=b['yong_method'],visible_count=len(d['matches']),receiver_strength=b['strength'],
                     other_strength=other['balance'].get('strength'),other_season=other['month']['season'],
                     status='candidate_present' if d['matches'] else 'no_visible_candidate' if known else 'partial_no_visible_candidate')
        directions.append(d)
    cross=[]
    for a in left['pillars']:
        if not a['known']:continue
        for b in right['pillars']:
            if not b['known']:continue
            for kind in branch_relations(a['branch']['hanja'],b['branch']['hanja']):
                cross.append({'left_position':a['position'],'right_position':b['position'],'left_label':a['label'],'right_label':b['label'],
                              'left':a['branch']['hanja'],'right':b['branch']['hanja'],'kind':kind,'primary':a['position']==b['position']=='day'})
    primary=[r for r in cross if r['primary']]
    adverse=any(r['kind']!='육합' for r in primary)
    return {'version':VERSION,'title':'두 사람의 궁합 계산','summary':'두 사람의 사주를 각각 계산했어요.',
        'status':'일지 비교에서 마찰 관계가 확인됐어요.' if adverse else '각자의 배치와 양방향 보완 조건을 비교했어요.',
        'people':[{'name':name,'report':without_authored_prose(r)} for name,r in zip(names,[left,right])],
        'directions':directions,'cross_relations':cross,'primary_relations':primary,'strengths':[],'risks':[],'chapters':[],
        'warnings':[] if left['element_total']==right['element_total']==8 else ['출생 시간이 없는 쪽은 전체 균형 비교를 확정하지 않았어요.'],
        'source_ids':SOURCE_IDS,'scope':'각자의 명식·계절·강약·용신, 양방향 겉 오행 대응과 일지 관계를 비교합니다. 합화·공통 대운·궁합 점수·결혼·이별 결과는 판정하지 않았어요.'}


def knowledge(service, notes, calculations=None):
    from api.chart_context import GODS
    ids = {'stars-symbols','stars-aspects','stars-time','stars-natal','profile-interpretation-rules'} if service=='stars' else {
        'saju-daymaster','saju-ten-gods','saju-classical-framework','saju-yong','saju-food-wealth','saju-interpretation-rules'}
    if service=='compatibility':ids|={'saju-compatibility-rules','saju-relations'}
    if calculations and 'luck_cycles' in calculations:ids.add('saju-luck-cycles')
    selected = [pick(n,['id','title','text']) for n in notes if n['id'] in ids]
    result = {'references':selected}
    if service=='stars':
        result['sign_vocabulary'] = SIGNS
        result['planet_roles'] = {'Sun':'자신을 표현하는 중심','Moon':'편안함과 익숙함','Mercury':'생각과 소통','Venus':'취향과 애정','Mars':'행동과 추진'}
    else:
        charts=[p['chart'] for p in calculations['people']] if calculations and service=='compatibility' else [calculations] if calculations else []
        observed={g['name'] for c in charts for g in c['ten_gods']}
        observed |= {p[k] for c in charts for p in c.get('luck_cycles',{}).get('periods',[]) for k in ['stem_god','branch_god']}
        result['role_vocabulary'] = {name:pick(g,['need','gift','risk']) for name,g in GODS.items() if not charts or name in observed}
        result['placement_rules'] = {'work':['month.stem.ten_god','month.branch.ten_god'], 'private':['day.branch.ten_god'],
                                     'balance':'계절과 선택된 계산 결과를 함께 읽는다. 겉 글자 개수로 재판정하지 않는다.'}
    return result


def payload(service, calculations, notes, sections):
    result={'REQUEST':'아래 계산과 공통 지식으로 요청한 항목만 새로 작성하세요. 이전 개인 풀이가 없습니다. 일반인이 바로 이해할 한국어 해요체로, 각 항목의 특징과 실제 생활의 가정 예시, 약점을 서로 다르게 풀어주세요. 전문 명칭과 한자는 계산 근거 id에만 남기고 본문에는 쓰지 마세요.',
            'SERVICE':service,'CALCULATIONS':writing_calculations(service,calculations),'KNOWLEDGE':plain(knowledge(service,notes,calculations)),
            'SECTION_REQUESTS':[{'topic':topic,'question':plain(question)} for topic,question in sections]}
    # State required references before generation, not only during repair.
    # These are raw evidence IDs, not a previous personalized explanation.
    for section in result['SECTION_REQUESTS']:
        required=[]
        if service=='compatibility' and section['topic']=='support':required=['support:0','support:1']
        elif service=='compatibility' and section['topic']=='risks':
            required=['relation:'+str(i) for i,r in enumerate(calculations['primary_relations']) if r['kind']!='육합']
        elif service=='stars' and section['topic']=='aspects':
            required=[e['id'] for e in calculations['evidence'] if e['id'].startswith('aspect:')]
            section['question']+=' 이번 계산의 관계를 모두 다루세요: '+'; '.join(a['left']+' · '+a['right']+' '+str(a['angle'])+'도 ('+a['meaning']+')' for a in calculations['aspects'])
        elif service=='stars' and section['topic'] in STAR_THEMES:
            keys={'overview':['Sun','Moon'],'work':['Sun','Mercury','Mars'],'relationships':['Moon','Venus'],'shadow':[]}[section['topic']]
            required=['planet:'+p['key'] for p in calculations['positions'] if p['key'] in keys and p['sign_confirmed']]
            if section['topic']=='shadow':required=[e['id'] for e in calculations['evidence'] if e['id'].startswith('aspect:')][:6] or ['planet:Sun']
        elif section['topic'].startswith('life:'):
            required=[section['topic']]+['cycle:'+str(p['index']) for p in calculations['luck_cycles']['periods']]
        if required:
            section['required_evidence_ids']=required[:6]
            section['instruction']='본문에서 이 계산들을 각각 설명하고, evidence_ids에 필수 근거를 모두 포함하세요.'
        if service=='compatibility' and section['topic']=='support':
            section['direction_checks']=[pick(d,['receiver','other','available','other_hour_known','element','visible_count','status']) for d in calculations['directions']]
            section['instruction']='방향마다 필요한 기운과 상대의 실제 겉 구성에 보이는 수를 설명하세요. 0이면 상대에게 그 보완 재료가 겉으로 보이지 않는다는 뜻을 숨기지 마세요. 일하는 역할의 협력을 기운의 양방향 보완과 혼동하지 마세요. 필수 근거를 모두 포함하세요.'
    if service!='stars':
        charts=[p['chart'] for p in calculations['people']] if service=='compatibility' else [calculations]
        placements=[]
        for chart in charts:
            rows={p['position']:p for p in chart['pillars'] if p['known']}
            placements.append({'name':chart['profile']['name'],
                'work_root':rows['month']['branch']['ten_god'],
                'work_outward':rows['month']['stem']['ten_god'],
                'private_expectation':rows['day']['branch']['ten_god'],
                'hour_role':rows.get('hour',{}).get('stem',{}).get('ten_god'),
                'visible_roles':{g['name']:g['count'] for g in chart['ten_gods']},
                'not_visibly_counted':[name for name in TERMS[-10:] if name not in {g['name'] for g in chart['ten_gods']}],
                'engine_strength':chart['balance'].get('strength'),
                'engine_support_element':chart['balance'].get('yong_element')})
        result['PLACEMENT_FACTS']=plain(placements)
    topics=[s['topic'] for s in result['SECTION_REQUESTS']]
    if service=='compatibility' and topics==['support']:
        # This question is about the calculated directional match, not all
        # personality roles. Avoid burying the two counts in both full charts.
        result['CALCULATIONS']=pick(result['CALCULATIONS'],['directions','evidence','scope'])
        result['CALCULATIONS']['evidence']=[e for e in result['CALCULATIONS']['evidence'] if e['id'].startswith('support:')]
        result['KNOWLEDGE']={'references':[n for n in result['KNOWLEDGE']['references'] if n['id'] in ['saju-compatibility-rules','saju-yong']]}
        result.pop('PLACEMENT_FACTS',None)
    elif service=='stars' and topics==['aspects']:
        result['CALCULATIONS']['evidence']=[e for e in result['CALCULATIONS']['evidence'] if e['id'].startswith('aspect:') or e['id']=='astrology_scope']
        result['KNOWLEDGE']['references']=[n for n in result['KNOWLEDGE']['references'] if n['id']=='stars-aspects']
    elif service=='saju' and len(topics)==1 and topics[0].startswith('life:'):
        # Natal counts are not timed influences. Put the current intervals
        # first and remove the natal role histogram that a model confused with
        # cycle-specific roles in a real generation audit.
        result['CALCULATIONS']=pick(result['CALCULATIONS'],['profile','month','balance','life_stage','luck_cycles','evidence'])
        result['CALCULATIONS']['evidence']=[e for e in result['CALCULATIONS']['evidence'] if e['id'].startswith(('cycle:','life:'))]
        baseline=result.pop('PLACEMENT_FACTS')[0]
        result['CALCULATIONS']['natal_roles']=pick(baseline,['work_root','work_outward','private_expectation'])
        roles={p[k] for p in calculations['luck_cycles']['periods'] for k in ['stem_god','branch_god']}
        roles |= {row[part]['ten_god'] for row in calculations['pillars'] if row['position'] in ['month','day'] for part in ['stem','branch'] if row[part]['ten_god'] in TERMS[-10:]}
        result['KNOWLEDGE']['role_vocabulary']={plain(k):plain(v) for k,v in knowledge('saju',notes,calculations)['role_vocabulary'].items() if k in roles}
        result['SECTION_REQUESTS'][0]['instruction']+=' 각 기간의 역할은 해당 period의 stem_god와 branch_god 두 필드만 사용하세요. 다른 시기의 역할을 현재 시기의 역할로 바꾸지 마세요. 기간 순서와 시작 나이를 지켜주세요.'
    if service=='stars' and any(t in STAR_THEMES for t in topics):
        result['REQUEST']+=' 전체 인물 소개는 overview에서만 하세요. work는 실제 업무 장면, relationships는 둘 사이의 대화와 기대, shadow는 문제가 커지는 순간을 중심으로 서로 다른 문장을 쓰세요. 계산 범위의 공통 안내는 별도 화면에 있으므로 각 장에서 반복하지 마세요.'
    return result


def issues(batch, data, topics, service, earlier=()):
    errors = []
    intro=batch.title+' '+batch.summary
    if re.search(r'[\u4e00-\u9fff]',intro) or any(re.search(r'(?<![가-힣])'+t,intro) for t in TERMS if t!='상관'):
        errors.append('제목과 요약에서도 한자와 전문 명칭을 빼고 쉽게 쓰세요.')
    if service=='stars' and re.search(r'사주|오행|일주',intro):errors.append('제목과 요약은 별자리 해설로 작성하세요.')
    if [c.topic for c in batch.chapters]!=list(topics):
        errors.append('요청한 topic을 같은 순서로 빠짐없이 출력하세요.')
    allowed = {e['id'] for e in data['evidence']}
    for c in batch.chapters:
        if not set(c.evidence_ids)<=allowed:
            errors.append(c.topic+': 계산에 없는 근거 id입니다.')
        text = ' '.join([c.title,*c.paragraphs,c.reflection])
        if any(len(p.strip())<45 for p in c.paragraphs) or len(''.join(c.paragraphs))<240:
            # Missing or ambiguous calculations should remain brief.
            unknown = service=='stars' and (c.topic in ['moon','inside_outside','aspects'] and not data['hour_known'] or c.topic in PLANETS and not next((p.get('sign_confirmed') for p in data['positions'] if p['key']==PLANETS[c.topic]),False))
            if not unknown:errors.append(c.topic+': 짧은 요약 대신 특징·생활 예·약점을 충분히 풀어주세요.')
        jargon = [t for t in TERMS if re.search(r'(?<![가-힣])'+re.escape(t),text)]
        # '상관없다' is an ordinary Korean word, not the ten-god label.
        jargon = [t for t in jargon if t!='상관' or re.search(r'상관(?!없|이 없|하지|없이)',text)]
        if jargon or re.search(r'[\u4e00-\u9fff]',text):
            errors.append(c.topic+': 전문 이름과 한자를 쉬운 생활의 말로 바꾸세요. 검출: '+', '.join(jargon))
        if re.search(r'(반드시|무조건|보장).{0,15}(성공|부자|결혼|이별)|우울증|질병|수명|괴강|백호|재고귀인|이번 주|오늘의 운세',text):
            errors.append(c.topic+': 계산하지 않은 사건·질병·운명 단정입니다.')
        if re.search(r'물.{0,8}마시|음식|음료|차를\s*마',text):
            errors.append(c.topic+': 오행을 실제 음식·음료에 연결하지 마세요. 환경과 활동의 상징으로 설명하세요.')
        if service=='stars':
            if re.search(r'사주|오행|용신|일주|편재',text):errors.append(c.topic+': 별자리 해설에 사주를 섞지 마세요.')
            if c.topic in STAR_THEMES:
                if len(c.paragraphs)<3:errors.append(c.topic+': 읽기 쉽게 특징·생활 예·주의할 점을 3~4단락으로 나누세요.')
                request=payload('stars',data,[],[(c.topic,STAR_THEMES[c.topic])])['SECTION_REQUESTS'][0]
                if not set(request.get('required_evidence_ids',[]))<=set(c.evidence_ids):errors.append(c.topic+': 종합 해석에 필요한 실제 천체의 근거를 모두 연결하세요.')
            if c.topic=='aspects' and 0<len(data['aspects'])<=6:
                required={e['id'] for e in data['evidence'] if e['id'].startswith('aspect:')}
                if not required<=set(c.evidence_ids):errors.append('계산된 천체 관계를 빠뜨리지 말고 각 관계를 설명하고 근거를 포함하세요.')
                if any(a['left'] not in text or a['right'] not in text for a in data['aspects']):
                    errors.append('근거 id만 나열하지 말고 모든 계산된 관계의 두 천체를 본문에서 설명하세요.')
            if c.topic in PLANETS:
                position = next((p for p in data['positions'] if p['key']==PLANETS[c.topic]),None)
                if position and position['sign_confirmed']:
                    if position['sign'] not in text or 'planet:'+position['key'] not in c.evidence_ids:
                        errors.append(c.topic+': 실제 천체의 별자리 이름과 해당 근거를 포함하세요.')
                    if any(s in text for s in SIGNS if s!=position['sign']):
                        errors.append(c.topic+': 다른 천체의 별자리를 이 천체의 위치로 바꾸지 마세요.')
                elif c.topic=='moon' and re.search('|'.join(SIGNS),text):errors.append('달의 위치를 계산하지 않았습니다. 채우지 마세요.')
        elif service=='saju':
            if c.topic.startswith('life:'):
                if len(c.paragraphs)<len(data['luck_cycles']['periods']):errors.append(c.topic+': 실제 기간마다 한 단락씩 빠짐없이 작성하세요.')
                required={c.topic}|{'cycle:'+str(p['index']) for p in data['luck_cycles']['periods']}
                if not required<=set(c.evidence_ids):errors.append(c.topic+': 이 나이대에 걸치는 실제 기간의 근거를 모두 포함하세요.')
                missing=[]
                for p in data['luck_cycles']['periods']:
                    for months in [p['stage_start_months'],p['stage_end_months']]:
                        year,month=divmod(months,12)
                        pattern=r'(?<!\d)'+str(year)+r'\s*세'+(r'\s*'+str(month)+r'\s*개월' if month else r'(?!\s*\d+\s*개월)')
                        if not re.search(pattern,text):missing.append(p['stage_age_label']);break
                if missing:errors.append(c.topic+': 본문에서 누락된 실제 나이 구간을 설명하세요: '+'; '.join(missing))
                allowed_months={data['life_stage']['start_months'],data['life_stage']['end_months'],data['life_stage']['end_months']-12,data['luck_cycles']['start_months']}
                for p in data['luck_cycles']['periods']:
                    allowed_months.update(p[k] for k in ['start_months','end_months','stage_start_months','stage_end_months'])
                for m in re.finditer(r'(?<!\d)(\d+)\s*세(?:\s*(\d+)\s*개월)?',' '.join(c.paragraphs)):
                    if int(m[1])*12+int(m[2] or 0) not in allowed_months:
                        errors.append(c.topic+': 계산에 없는 나이 경계를 쓰지 마세요: '+m[0])
                for m in re.finditer(r'첫\s*대운.{0,14}?(\d+)\s*세(?:\s*(\d+)\s*개월)?',text):
                    if int(m[1])*12+int(m[2] or 0)!=data['luck_cycles']['start_months']:
                        errors.append(c.topic+': 첫 대운의 시작은 '+data['luck_cycles']['start_label']+'입니다. 다른 기간의 시작과 혼동하지 마세요.')
            counts={e['element']:e['count'] for e in data['elements']}
            labels={'목':['나무','목'],'화':['불','화'],'토':['흙','토'],'금':['금속','금'],'수':['물','수']}
            for element,names in labels.items():
                for name in names:
                    for m in re.finditer(r'(?<![가-힣])'+name+r'(?:의?\s*기운)?(?:은|는|이|가)?\s*(\d+)\s*개',text):
                        if int(m[1])!=counts[element]:errors.append(c.topic+': '+name+'의 개수가 계산값과 달라요.')
            if not data['balance']['available'] and re.search(r'(금속|나무|흙|불|물).{0,12}(부족|보완|필요|도움)',text):
                errors.append(c.topic+': 시간이 없어 특정 기운의 보완을 확정하지 마세요.')
        if service=='compatibility' and c.topic=='support':
            if not {'support:0','support:1'}<=set(c.evidence_ids):errors.append('보완은 양쪽 방향의 계산을 모두 근거로 설명하세요.')
            labels={'목':'나무','화':'불','토':'흙','금':'금속','수':'물'}
            complete_directions=[d for d in data['directions'] if d['available'] and d['other_hour_known']]
            if any(labels[d['element']] not in text for d in complete_directions):
                errors.append('보완 항목에는 각 방향에서 필요한 기운을 쉬운 이름으로 설명하세요.')
            if any(d['visible_count']==0 for d in complete_directions) and not re.search(r'0개|없|보이지 않|드러나지 않|확인되지 않',text):
                errors.append('상대의 겉 구성에 보완 재료가 0개인 방향은 그 재료가 보이지 않는다고 명확히 설명하세요.')
        if service=='compatibility' and c.topic=='risks' and data['primary_relations']:
            adverse={i for i,r in enumerate(data['primary_relations']) if r['kind']!='육합'}
            if adverse and not any('relation:'+str(i) in c.evidence_ids for i in adverse):errors.append('실제 일지 마찰 관계를 빼지 마세요.')
    paragraphs = [p for c in [*earlier,*batch.chapters] for p in c.paragraphs]
    if any(re.search(r'\b(stage_age_label|stem_god|branch_god|CALCULATIONS|evidence_ids)\b',p) for p in paragraphs):errors.append('내부 필드명을 본문에 쓰지 마세요. 계산된 나이 구간과 쉬운 설명만 보여주세요.')
    if len(paragraphs)!=len(set(p.strip() for p in paragraphs)):errors.append('같은 단락을 여러 항목에 반복하지 마세요.')
    sentences = [s.strip() for p in paragraphs for s in re.split(r'(?<=[.!?。])\s+',p) if len(s.strip())>=38]
    if len(sentences)!=len(set(sentences)):errors.append('같은 긴 문장을 여러 항목에 반복하지 마세요.')
    return list(dict.fromkeys(errors))


async def call_model(schema, system, user, model, url, lock, output_limit=OUTPUT_LIMIT):
    output_schema=schema.model_json_schema()
    if schema is Batch:
        topics=[s['topic'] for s in user['SECTION_REQUESTS']]
        output_schema['properties']['chapters'].update(minItems=len(topics),maxItems=len(topics))
        output_schema['$defs']['Chapter']['properties']['topic']['enum']=topics
        output_schema['$defs']['Chapter']['properties']['evidence_ids']['items']['enum']=[e['id'] for e in user['CALCULATIONS']['evidence']]
        paragraphs=output_schema['$defs']['Chapter']['properties']['paragraphs']
        if len(topics)==1 and topics[0].startswith('life:'):
            count=len(user['CALCULATIONS']['luck_cycles']['periods'])
            paragraphs.update(minItems=max(1,count),maxItems=min(8,count+2))
        else:paragraphs['maxItems']=4
        if len(topics)==1 and user['SECTION_REQUESTS'][0].get('required_evidence_ids'):
            output_schema['$defs']['Chapter']['properties']['evidence_ids']['enum']=[user['SECTION_REQUESTS'][0]['required_evidence_ids']]
    elif schema is LifeDraft:
        indices=[p['index'] for p in user['CALCULATIONS']['luck_cycles']['periods']]
        output_schema['properties']['intervals'].update(minItems=len(indices),maxItems=len(indices))
        output_schema['$defs']['LifeInterval']['properties']['period_index']['enum']=indices
        output_schema['properties']['before_first_cycle']=({'type':'string','minLength':60,'maxLength':650} if user['CALCULATIONS']['life_stage']['before_first_cycle_until'] else {'type':'null'})
    content,metrics=await complete(output_schema,
        [{'role':'system','content':system},{'role':'user','content':json.dumps(user,ensure_ascii=False)}],
        model,url,lock,output_limit=output_limit,context_size=CONTEXT_SIZE)
    return schema.model_validate_json(content),metrics


async def write(service, data, notes, sections, model, url, lock):
    skill = SKILL.read_text()
    material = payload(service,data,notes,sections)
    digest = hashlib.sha256(json.dumps([VERSION,CONFIG.provider,CONFIG.json_mode,url,model,skill,material],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    now=time.monotonic()
    for key in list(CACHE):
        if now-CACHE[key]['created']>1800:CACHE.pop(key,None)
    if digest in CACHE:
        result=copy.deepcopy(CACHE[digest]['result']);result['metadata']['cache_hit']=True
        return result
    output=[];metrics=[];title=summary=''
    started=time.monotonic()
    # Mandatory comparison references can then be enforced per chapter in the
    # JSON schema, without forcing unrelated chapters to cite those same IDs.
    chunks=[];pending=[]
    mandatory={'support','risks'} if service=='compatibility' else {'aspects'} if service=='stars' else set()
    for section in sections:
        if section[0] in mandatory:
            if pending:chunks.append(pending);pending=[]
            chunks.append([section])
        else:
            pending.append(section)
            if len(pending)==BATCH_SIZE:chunks.append(pending);pending=[]
    if pending:chunks.append(pending)
    for chunk in chunks:
        user=payload(service,data,notes,chunk)
        # Headlines may prevent repeated framing without supplying old prose.
        if output:user['ALREADY_COVERED_TOPICS']=[c.topic for c in output]
        for attempt in range(2):
            try:
                batch,metric=await call_model(Batch,skill,user,model,url,lock)
            except ValueError:
                if attempt:raise
                user['VALIDATION_ERRORS']=['출력 형식 또는 길이가 잘못됐어요. 요청한 JSON 구조와 주제를 지키고, 장별 3단락을 간결하지만 충분하게 완성하세요.']
                continue
            metrics.append({**metric,'topics':[s[0] for s in chunk],'repair':bool(attempt)})
            errors=issues(batch,data,[s[0] for s in chunk],service,output)
            if not errors:break
            if attempt:raise ValueError('개인별 해설 검증 실패: '+' / '.join(errors))
            user['VALIDATION_ERRORS']=errors
        if not output:title,summary=batch.title,batch.summary
        output.extend(batch.chapters)
    evidence={e['id']:e for e in data['evidence']}
    chapters=[]
    for c in output:
        value=c.model_dump();value['body']='\n\n'.join(c.paragraphs);value['lead']=c.paragraphs[0]
        value['source_ids']=list(dict.fromkeys(evidence[i]['source_id'] for i in c.evidence_ids))
        value['basis']=' · '.join(evidence[i]['label']+': '+evidence[i]['text'] for i in c.evidence_ids)
        chapters.append(value)
    result={'title':title,'summary':summary,'chapters':chapters,'evidence':data['evidence'],
            'metadata':{'mode':'fresh_model','version':VERSION,'provider':CONFIG.provider,'model':model,'previous_reading_used':False,
                'actual_models':list(dict.fromkeys(m.get('actual_model',model) for m in metrics)),
                'skill_sha256':hashlib.sha256(skill.encode()).hexdigest(),'input_sha256':digest,
                'context_size':CONTEXT_SIZE if CONFIG.provider=='ollama' else None,'output_limit':OUTPUT_LIMIT,'thinking':False,'cache_hit':False,
                'temperature':0.2,'seed':42,
                'calls':metrics,'seconds':round(time.monotonic()-started,2)}}
    if len(CACHE)>=32:CACHE.pop(next(iter(CACHE)))
    CACHE[digest]={'created':time.monotonic(),'result':copy.deepcopy(result)}
    return result


def without_authored_prose(report):
    r=copy.deepcopy(report)
    r['chapters']=[];r['review_points']=[]
    if r.get('astrology'):r['astrology']['interpretation']=[]
    if r.get('comparison'):
        r['comparison']={'title':'사주와 별자리는 각각의 계산으로 읽어요.','saju':'사주 해설에서 확인해 주세요.',
                         'astrology':'별자리 해설에서 확인해 주세요.','reflection':'같은 출생 정보라도 서로 다른 해석 체계예요.','note':'두 체계의 오행이나 점수를 합치지 않습니다.'}
    if r.get('luck_cycles'):
        for p in r['luck_cycles'].get('periods',[]):p.update(paragraphs=[],transition='',title=p.get('age_label','10년 흐름'))
        for s in r['luck_cycles'].get('stages',[]):s['paragraphs']=[]
    return r


async def generate_report(facts, notes, model, url, lock):
    service=facts['service']
    if service=='compatibility':
        c=copy.deepcopy(facts['compatibility'])
        generated=await write('compatibility',raw_pair(c),notes,list(PAIR.items()),model,url,lock)
        # Keep two independently generated personal readings available in tabs.
        personal=[]
        for p in c['people']:
            result=await write('saju',raw_saju(p['report']),notes,[(t,SAJU[t]) for t in PERSON_TOPICS],model,url,lock)
            personal.append(result['metadata'])
            p['report']=without_authored_prose(p['report'])
            p['report']['chapters']=result['chapters'];p['report']['generation']=result['metadata']
            await add_life_readings(p['report'],notes,model,url,lock)
        c.update(title=generated['title'],summary=generated['summary'],chapters=generated['chapters'],strengths=[],risks=[],generation=generated['metadata'])
        c['generation']['personal_reports']=personal
        for d in c['directions']:d.pop('text',None)
        c['source_ids']=list(dict.fromkeys(s for ch in c['chapters'] for s in ch['source_ids']))
        return {'editorial':generated,'report':None,'compatibility':c,'metadata':c['generation']}
    report=without_authored_prose(facts['chart']['report'])
    if service=='stars':
        data=raw_stars(facts['astrology'],report['profile']);sections=list(STAR_THEMES.items())
        if not data['aspects']:sections.append(('aspects',STARS['aspects']))
    else:
        data=raw_saju(report);sections=list(SAJU.items())
    generated=await write(service,data,notes,sections,model,url,lock)
    if service=='stars' and data['aspects']:
        aspect=await write_aspect_chapter(data,notes,model,url,lock)
        generated['chapters'].append(aspect['chapter'])
        generated['metadata']['aspect_readings']=aspect['metadata']
        generated['metadata']['calls'] += [call for m in aspect['metadata'] for call in m['calls']]
        generated['metadata']['actual_models']=list(dict.fromkeys(generated['metadata']['actual_models']+[name for m in aspect['metadata'] for name in m['actual_models']]))
        generated['metadata']['seconds'] += sum(m['seconds'] for m in aspect['metadata'])
    report['generation']=generated['metadata'];report['primary_service']=service
    if service=='stars':
        report['astrology']['interpretation']=generated['chapters']
    else:
        report['chapters']=generated['chapters']
        await add_life_readings(report,notes,model,url,lock)
    return {'editorial':generated,'report':report,'compatibility':None,'metadata':generated['metadata']}


async def write_aspect_chapter(data,notes,model,url,lock):
    """Give every calculated relationship its own fresh model call.

    A model kept discussing only the first relationship while citing both IDs.
    Focused calls contain one observed relationship, never an earlier reading.
    The reader sees one chapter containing every independently written section.
    """
    parts=[];metadata=[]
    for i,relation in enumerate(data['aspects']):
        focused=copy.deepcopy(data)
        labels={relation['left'],relation['right']}
        focused['positions']=[p for p in focused['positions'] if p['label'] in labels]
        focused['aspects']=[relation]
        keys={p['key'] for p in focused['positions']}
        focused['evidence']=[e for e in focused['evidence'] if e['id']=='aspect:'+str(i) or e['id']=='astrology_scope' or e['id'].removeprefix('planet:') in keys]
        result=await write('stars',focused,notes,[('aspects',STARS['aspects'])],model,url,lock)
        parts.append(result['chapters'][0]);metadata.append(result['metadata'])
    chapter={'topic':'aspects','title':'천체 사이에서 읽는 조화와 긴장',
        'paragraphs':[p for part in parts for p in part['paragraphs']],
        'reflection':'서로 잘 연결되는 모습과 다른 요구가 부딪히는 모습을 함께 살펴요.',
        'evidence_ids':list(dict.fromkeys(e for part in parts for e in part['evidence_ids'])),
        'source_ids':list(dict.fromkeys(s for part in parts for s in part['source_ids'])),
        'basis':' · '.join(part['basis'] for part in parts)}
    chapter['body']='\n\n'.join(chapter['paragraphs']);chapter['lead']=chapter['paragraphs'][0]
    paragraphs=chapter['paragraphs']
    sentences=[s.strip() for p in paragraphs for s in re.split(r'(?<=[.!?。])\s+',p) if len(s.strip())>=38]
    if len(paragraphs)!=len(set(p.strip() for p in paragraphs)) or len(sentences)!=len(set(sentences)):
        raise ValueError('천체 관계별 해설에 같은 단락이나 긴 문장이 반복됐습니다.')
    return {'chapter':chapter,'metadata':metadata}


async def add_life_readings(report,notes,model,url,lock):
    cycles=report.get('luck_cycles',{})
    if not cycles.get('available'):return
    stages=[];metadata=[]
    for stage in cycles['stages']:
        data=life_stage_data(report,stage)
        generated=await write_life(data,notes,model,url,lock)
        chapter=generated['chapters'][0]
        stages.append({**pick(stage,['key','label','age_label','period_indices']),**chapter,
                       'period_labels':[p['stage_age_label'] for p in data['luck_cycles']['periods']]})
        metadata.append(generated['metadata'])
    # Never publish a partially generated or repeated set of stages.
    paragraphs=[p for s in stages for p in s['paragraphs']]
    if len(paragraphs)!=len(set(paragraphs)):raise ValueError('나이대별 해설에서 같은 단락을 반복했습니다.')
    cycles['stages']=stages;cycles['generation']=metadata
    generation=report['generation']
    generation['life_readings']=metadata
    generation['calls'] += [c for m in metadata for c in m['calls']]
    generation['seconds'] += sum(m['seconds'] for m in metadata)
    generation['actual_models']=list(dict.fromkeys(generation['actual_models']+[n for m in metadata for n in m['actual_models']]))


async def write_life(data,notes,model,url,lock):
    """The model explains each indexed period; dates come from calculations."""
    stage=data['life_stage'];topic='life:'+stage['key']
    material=payload('saju',data,notes,[(topic,'실제 기간마다 그 기간의 역할과 원래 성향을 연결해 장점·생활의 가정 예·부담을 설명하세요.')])
    material['REQUEST']+=' 제목과 소개, 기간별 설명을 요청한 출력 구조대로 작성하세요. title은 이 나이대의 특징을 담은 한국어 제목이에요. 각 intervals 항목의 period_index 순서를 계산과 동일하게 유지하세요. 나이·기간 숫자는 화면에서 계산값으로 표시하므로 문장 안에서 쓰지 마세요. 각 기간은 해당 행의 두 역할만 사용해 연결하세요. 첫 대운 이전 설명은 before_first_cycle에 쓰고, 그 구간이 없으면 null로 반환하세요. intro는 전체 흐름을 짧게 연결하세요. 실제 과거를 알아낸 것처럼 말하지 마세요. 역할의 긴 정의를 복사하지 말고 행동과 생활 장면으로 설명하세요.'
    material['BEFORE_FIRST_CYCLE_REQUIRED']=bool(stage['before_first_cycle_until'])
    skill=SKILL.read_text()
    digest=hashlib.sha256(json.dumps(['life-intervals-1',CONFIG.provider,CONFIG.json_mode,url,model,skill,material],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    if digest in CACHE and time.monotonic()-CACHE[digest]['created']<1800:
        result=copy.deepcopy(CACHE[digest]['result']);result['metadata']['cache_hit']=True;return result
    metrics=[];started=time.monotonic()
    for attempt in range(2):
        try:draft,metric=await call_model(LifeDraft,skill,material,model,url,lock)
        except ValueError:
            if attempt:raise
            material['VALIDATION_ERRORS']=['출력 구조와 글 길이를 지켜 모든 실제 기간의 설명을 완성하세요.']
            continue
        metrics.append(metric)
        body=[draft.intro]+([draft.before_first_cycle] if draft.before_first_cycle else [])+[v.paragraph for v in draft.intervals]
        evidence_ids=[topic]+['cycle:'+str(p['index']) for p in data['luck_cycles']['periods']]
        proxy=Batch(title=draft.title[:40],summary=draft.intro[:180],chapters=[Chapter(topic='life_explanation',title=draft.title,paragraphs=body,reflection='계산된 기간별로 활동과 부담의 변화를 함께 읽어요.',evidence_ids=evidence_ids)])
        errors=issues(proxy,data,['life_explanation'],'saju')
        if [v.period_index for v in draft.intervals]!=[p['index'] for p in data['luck_cycles']['periods']]:errors.append('각 실제 기간의 index를 동일한 순서로 빠짐없이 설명하세요.')
        if any(re.search(r'\d+\s*세|\d+\s*개월',p) for p in body):errors.append('본문의 나이 숫자를 빼세요. 화면에서 정확한 계산 나이로 각 문단을 구분합니다.')
        if bool(stage['before_first_cycle_until'])!=bool(draft.before_first_cycle):errors.append('첫 대운 전 구간이 있으면 원래 사주만 읽는 설명을 before_first_cycle에 쓰세요. 없으면 null로 두세요.')
        if not errors:break
        if attempt:raise ValueError('나이대별 해설 검증 실패: '+' / '.join(errors))
        material['VALIDATION_ERRORS']=errors
    paragraphs=[draft.intro]
    if draft.before_first_cycle:
        paragraphs.append('첫 대운인 '+data['luck_cycles']['start_label']+' 전까지는 타고난 사주를 기준으로 읽어요. '+draft.before_first_cycle)
    paragraphs += [p['stage_age_label']+'. '+v.paragraph for p,v in zip(data['luck_cycles']['periods'],draft.intervals)]
    evidence={e['id']:e for e in data['evidence']}
    title=stage['label']+'에 따라 달라지는 흐름' if draft.title.strip().lower()=='lifedraft' else draft.title
    chapter={'topic':topic,'title':title,'paragraphs':paragraphs,'body':'\n\n'.join(paragraphs),
             'reflection':'시기마다 달라지는 활동과 부담을 함께 살펴요.','evidence_ids':evidence_ids,'source_ids':['saju-luck-cycles'],
             'basis':' · '.join(evidence[i]['label']+': '+evidence[i]['text'] for i in evidence_ids)}
    result={'chapters':[chapter],'metadata':{'mode':'fresh_model','provider':CONFIG.provider,'model':model,
        'previous_reading_used':False,'input_sha256':digest,'skill_sha256':hashlib.sha256(skill.encode()).hexdigest(),
        'timeline_labels':'calculated','title_source':'stage_label' if title!=draft.title else 'model','actual_models':list(dict.fromkeys(m.get('actual_model',model) for m in metrics)),
        'calls':metrics,'seconds':round(time.monotonic()-started,2),'cache_hit':False}}
    if len(CACHE)>=32:CACHE.pop(next(iter(CACHE)))
    CACHE[digest]={'created':time.monotonic(),'result':copy.deepcopy(result)}
    return result


async def followup(session, question, notes, model, url, lock):
    service=session['service'];facts=session['facts']
    if service=='compatibility':data=raw_pair(facts['compatibility'])
    elif service=='stars':data=raw_stars(facts['astrology'],facts['chart']['report']['profile'])
    else:data=raw_saju(facts['chart']['report'],include_cycles=True)
    material=payload(service,data,notes,[]);material['QUESTION']=question
    system=SKILL.read_text()+'\n이번에는 QUESTION에 직접 답하는 2~3단락의 한국어 해설과 실제 evidence_ids를 반환하세요. 다른 체계를 요청받으면 이 입력에는 없다는 범위를 짧게 밝히세요.'
    result,metric=await call_model(Followup,system,material,model,url,lock,1600)
    paragraphs=[p.strip() for p in result.answer.split('\n\n') if p.strip()]
    proxy=Batch(title='후속 질문 해설',summary='계산 결과와 공통 자료로 후속 질문을 설명해요.',chapters=[Chapter(topic='followup',title='후속 질문 해설',paragraphs=paragraphs,reflection='질문에 맞는 계산 자료로 읽었어요.',evidence_ids=result.evidence_ids)])
    # Validate references and plain prose, not paragraph count for a followup.
    errors=[e for e in issues(proxy,data,['followup'],service) if '짧은 요약' not in e]
    if errors:raise ValueError('후속 해설 검증 실패: '+' / '.join(errors))
    evidence={e['id']:e for e in data['evidence']}
    return {'answer':result.answer,'source_ids':list(dict.fromkeys(evidence[i]['source_id'] for i in result.evidence_ids)),
            'answer_mode':'fresh_model','generation':{'model':model,**metric}}
