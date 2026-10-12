"""Fresh naming prose and multiple-name comparison from verified raw data."""
import copy
import hashlib
import json
import re
import time
from typing import Literal

from pydantic import BaseModel, Field
from api.model_provider import CONFIG, complete
from api.model_readings import SKILL, raw_saju, writing_calculations, knowledge, pick, TERMS, PLAIN
from api.naming import (candidates, character_detail, sound_details, THEMES,
                        CHAR_THEMES, REGISTRY, COURT_URL, dictionary_options, has_verified_meaning)

CACHE={}
SOURCE_IDS=['name-hanja-dictionary','name-sound','name-elements','name-registry','name-recommendation-rules']


class NameChapter(BaseModel):
    topic: Literal['sound','birth']
    title: str = Field(min_length=5,max_length=70)
    paragraphs: list[str] = Field(min_length=1,max_length=4)


class CombinationDraft(BaseModel):
    id: str
    reason: str = Field(min_length=30,max_length=300)
    paragraphs: list[str] = Field(min_length=2,max_length=3)
    consideration: str = Field(min_length=20,max_length=300)


class NameBase(BaseModel):
    title: str = Field(min_length=5,max_length=60)
    summary: str = Field(min_length=30,max_length=180)
    status: Literal['recommend','consider','not_recommended','needs_verification']
    verdict: str = Field(min_length=30,max_length=300)
    concerns: list[str] = Field(min_length=1,max_length=3)


class NameDraft(NameBase):
    combinations: list[CombinationDraft]


class NameContext(NameBase):
    chapters: list[NameChapter] = Field(min_length=1,max_length=1)


class Choice(BaseModel):
    id: str
    reason: str = Field(min_length=30,max_length=350)
    concern: str = Field(min_length=20,max_length=300)


class ComparisonDraft(BaseModel):
    title: str = Field(min_length=5,max_length=40)
    summary: str = Field(min_length=30,max_length=180)
    recommended_ids: list[str] = Field(max_length=5)
    choices: list[Choice] = Field(min_length=1,max_length=5)
    paragraphs: list[str] = Field(min_length=2,max_length=4)


class NameAnswer(BaseModel):
    answer: str = Field(min_length=60,max_length=3000)


def raw_character(char,syllable,index,kind='name'):
    detail=character_detail(char,syllable,index,kind)
    return pick(detail,['character','syllable','position','kind','meaning','definition','readings','themes','registry'])


def naming_calculations(request,facts,notes):
    from api.server import name_for, INITIALS, SOUND_ELEMENTS
    primary=request.profile
    people=[primary]+[primary.model_copy(update={'name':c.name,'name_hanja':c.name_hanja}) for c in request.name_candidates]
    if len({p.name for p in people})!=len(people):raise ValueError('같은 이름은 한 번만 입력해 주세요. 한자 조합은 이름별로 함께 비교해요.')
    birth=raw_saju(facts['chart']['report']) if facts.get('chart') else None
    raw=[]
    for index,p in enumerate(people):
        sound=name_for(p,INITIALS,SOUND_ELEMENTS)
        rows,_=sound_details(p,sound)
        recs,_=candidates(p)
        combos=[]
        if p.name_hanja:
            combos.append({'id':'selected','name_hanja':p.name_hanja,'selected':True})
        combos += [{'id':'option:'+str(i),'name_hanja':r['name_hanja'],'selected':False} for i,r in enumerate(recs)]
        for combo in combos:
            combo['characters']=[raw_character(c,s,i) for i,(c,s) in enumerate(zip(combo['name_hanja'],p.name))]
            combo['verified']=all(has_verified_meaning(h) for h in combo['characters'])
            combo['preference_matches']=[h['syllable'] for h in combo['characters'] if p.naming_preference in CHAR_THEMES.get(h['character'],[])]
        raw.append({'id':'name:'+str(index),'name':p.name,'display_name':p.surname+p.name,
                    'selected_hanja':p.name_hanja,'surname':p.surname,'surname_hanja':p.surname_hanja,
                    'sound_structure':rows,'sound_elements':sound['sound_elements'],
                    'sound_matches_birth_element':([h['syllable'] for h in rows if h['element']==birth['balance'].get('yong_element')] if birth else []),
                    'combinations':combos,'recommendable':any(c['verified'] for c in combos)})
    return {'birth':birth,'candidates':raw,'preference':primary.naming_preference,
            'surname_characters':[raw_character(c,s,i,'surname') for i,(c,s) in enumerate(zip(primary.surname_hanja,primary.surname))],
            'preference_label':THEMES.get(primary.naming_preference,{}).get('label','뜻을 고르게 살펴보기'),
            'registry_checked_at':REGISTRY['checked_at'],
            'registry_source':{'name':'대법원 전자가족관계등록시스템','url':COURT_URL},
            'knowledge':knowledge('saju',notes,birth) if birth else {},
            'scope':'검토된 한자의 사전 뜻·공식 독음 조회 자료·이름 소리·동일한 출생 명식의 참고 관계. 한자 자원오행·원획·81수리 길흉 판정 자료는 제공되지 않았습니다.'}


def material(data,candidate=None):
    raw=copy.deepcopy(data)
    if candidate is not None:raw['candidates']=[copy.deepcopy(candidate)]
    # A sound-category match is a calculated reference, not a validated naming
    # suitability rule. A live model wrongly used it to reject another name.
    for p in raw['candidates']:
        p.pop('sound_elements',None);p.pop('sound_matches_birth_element',None)
        for row in p['sound_structure']:row.pop('element',None)
    if raw['birth']:
        raw['birth']=writing_calculations('saju',raw['birth'])
        raw['birth']['profile']['name']='아이'
        # Normalize shared role vocabulary, preserving Han characters only in
        # dictionary naming facts where their actual meanings are required.
        from api.model_readings import plain
        raw['knowledge']=plain(raw['knowledge'])
    return raw


def prose_issues(text,data):
    errors=[]
    # Names and dictionary characters are allowed; invented combinations are not.
    allowed=set(''.join(c['name_hanja'] for p in data['candidates'] for c in p.get('combinations',[])))
    allowed |= set(''.join(p.get('surname_hanja','') for p in data['candidates']))
    lookup=data.get('dictionary_lookup',{})
    allowed |= {h['character'] for rows in lookup.values() for h in rows}
    unexpected=set(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]',text))-allowed
    if unexpected:errors.append('제공되지 않은 한자나 명식을 만들지 마세요. 입력에 없는 글자: '+''.join(sorted(unexpected)))
    names={p['name'] for p in data['candidates']}
    detected=[t for t in TERMS if t!='상관' and t not in names and re.search(r'(?<![가-힣])'+t,text)]
    if detected:errors.append('사주 전문 명칭을 생활의 쉬운 말로 풀어 쓰세요. 검출: '+', '.join(detected))
    if re.search(r'(반드시|무조건|보장).{0,15}(성공|부자|결혼)|운명이 정해|사주 적합도\s*\d|\d+\s*점|우울증|질병|획수.{0,12}(길|흉)|자원오행.{0,12}(계산했|판정했)',text):errors.append('계산하지 않은 점수·길흉·능력과 미래의 보장을 만들지 마세요.')
    if re.search(r'(발음오행|소리\s*오행|초성.{0,8}오행).{0,16}([목화토금수][·\s,→]+[목화토금수]|[목화토금수]으로 분류)|오행.{0,12}(불일치|맞지 않|감수)|[가-힣]{1,4}[\(\[][목화토금수][\)\]]',text):errors.append('이름 추천에는 뜻·독음·실제 음절 구성을 사용하세요. 제공되지 않은 발음오행 분류나 오행 적합도 판정을 쓰지 마세요.')
    if re.search(r'표준\s*독음.{0,25}(?:만|뿐|므로).{0,50}(차이|다르|괴리|어긋)|독음.{0,10}뿐',text):errors.append('다른 독음이 있다는 이유로 제공된 이름의 독음이 어긋난다고 단정하지 마세요. 글자별 registry에서 확인한 독음과 사전의 다른 독음을 구분하세요.')
    if re.search(r'국립[가-힣]*(센터|기관|사전)',text):errors.append('조회하지 않은 기관을 출처로 만들지 마세요. 제공된 출처는 대법원 전자가족관계등록시스템입니다.')
    if re.search(r'공식\s*문서.{0,20}(사용.{0,6}제한|사용.{0,6}불가)',text):errors.append('한자가 낯설다는 이유로 공식 문서 사용 제한을 만들지 마세요. 제공된 공식 독음 확인 사실과 구분하세요.')
    if data.get('birth'):
        known=bool(data['birth']['input_basis'].get('entered_time'))
        if known and re.search(r'(출생|태어난)\s*시간(?:이|을)?\s*(없|미입력|모르)',text):errors.append('출생 시간이 입력됐어요. 시간이 없다고 설명하지 마세요.')
        if not known and re.search(r'(네|4)\s*기둥.{0,8}(확인했|계산했)',text):errors.append('시간이 없어 세 기둥만 계산했어요. 네 기둥이라고 만들지 마세요.')
    elif re.search(r'(사주|출생 명식).{0,12}(계산했|확인했)',text):errors.append('생일이 없어 출생 명식을 계산하지 않았어요.')
    for syllable,rows in lookup.items():
        if any(has_verified_meaning(h) for h in rows) and re.search(re.escape(syllable)+r'[^.!?\n]{0,90}(한자가?\s*없|한자는?\s*없|한자(?:가|는)?\s*존재하지|표준\s*한자.{0,8}없)',text):
            errors.append(f'‘{syllable}’에 해당하는 확인된 한자가 조회됐습니다. 기존 추천 목록에 없다는 것을 한자가 존재하지 않는다는 뜻으로 설명하지 마세요.')
    if lookup:
        known_names=names | {p['surname']+p['name'] for p in data['candidates']}
        for name,glyphs in re.findall(r'([가-힣]{2,4})\(([\u3400-\u4dbf\u4e00-\u9fff]{2,4})\)',text):
            if len(name)==len(glyphs) and name not in known_names:
                errors.append('후속 질문은 입력한 한글 이름의 한자 조합을 확인하는 상담입니다. 새로운 한글 이름을 예시로 발명하지 마세요: '+name)
    return errors


def normalize_vocabulary(value,data,*,context=False):
    """Translate fixed role terms only; never modify facts or name characters."""
    names={p['name'] for p in data['candidates']}
    protected_hanja=set(''.join(c['name_hanja'] for p in data['candidates'] for c in p.get('combinations',[])))
    def transform(obj):
        if isinstance(obj,list):return [transform(v) for v in obj]
        if isinstance(obj,dict):return {k:transform(v) for k,v in obj.items()}
        if not isinstance(obj,str):return obj
        obj=obj.replace('nasal','콧소리')
        for word,replacement in sorted(PLAIN.items(),key=lambda x:-len(x[0])):
            if word in names:continue
            obj=re.sub(r'(?<![가-힣])'+re.escape(word)+(r'(?!없|이 없|없이|하지)' if word=='상관' else ''),replacement,obj)
        # A model wrote the ordinary descriptor 無理 inside Korean sentences.
        # Translate that fixed word without changing any supplied name glyph.
        if not set('無理')<=protected_hanja:obj=obj.replace('無理','무리')
        if '像' not in protected_hanja:obj=obj.replace('像','모습')
        if context:
            obj=re.sub(r'[\u4e00-\u9fff]','',obj)
            obj=re.sub(r'\(\s*\)','',obj)
        return obj
    return type(value).model_validate(transform(value.model_dump()))


def name_issues(value,data,candidate):
    errors=prose_issues(value.model_dump_json(),material(data,candidate))
    if [c.id for c in value.combinations]!=[c['id'] for c in candidate['combinations']]:errors.append('계산에 제공된 한자 조합 id를 같은 순서로 모두 설명하세요.')
    if not candidate['recommendable'] and value.status=='recommend':errors.append('확인된 뜻과 공식 독음을 갖춘 조합이 없어 추천을 확정할 수 없어요.')
    if any(not c['verified'] for c in candidate['combinations']) and not re.search(r'확인|미확인|보류|조회',value.model_dump_json()):errors.append('뜻·독음이 확인되지 않은 입력 조합을 숨기지 마세요.')
    for value_combo,raw_combo in zip(value.combinations,candidate['combinations']):
        text=' '.join(value_combo.paragraphs)
        if any(h['character'] not in text for h in raw_combo['characters']):errors.append(raw_combo['id']+': 글자별 한자와 확인된 뜻을 각각 설명하세요.')
    paragraphs=[p for c in value.combinations for p in c.paragraphs]
    if len(paragraphs)!=len(set(paragraphs)):errors.append('같은 단락을 복사해 반복하지 마세요.')
    return errors


def context_issues(value,data,candidate):
    errors=prose_issues(value.model_dump_json(),material(data,candidate))
    if [c.topic for c in value.chapters]!=['sound']:errors.append('sound 한 항목만 작성하세요. 출생 해설은 공통으로 별도 작성합니다.')
    if re.search(r'(한자|독음).{0,25}(없|존재하지|불가능|표준.{0,8}아니)',value.model_dump_json()):errors.append('이 장은 소리 구조만 설명합니다. 한자 존재 여부나 공식 독음은 별도 조회 사항이므로 단정하지 마세요.')
    for chapter in value.chapters:
        if chapter.topic!='birth' or data['birth']:
            if len(''.join(chapter.paragraphs))<180:errors.append(chapter.topic+'을 구체적인 이유와 생활 예를 포함해 충분히 설명하세요.')
    return errors


def comparison_issues(value,data):
    errors=prose_issues(value.model_dump_json(),data)
    ids={p['id'] for p in data['candidates']}
    eligible={p['id'] for p in data['candidates'] if p['recommendable']}
    if len(value.choices)!=len(ids) or {c.id for c in value.choices}!=ids:errors.append('입력한 모든 이름을 정확히 한 번씩 비교하세요.')
    if len(set(value.recommended_ids))!=len(value.recommended_ids) or not set(value.recommended_ids)<=eligible:errors.append('확인된 조합이 있는 실제 후보만 중복 없이 추천하세요.')
    if len(ids)==1 and re.search(r'(?<![가-힣0-9])(두|세|네|다섯|[2-5])\s*(?:개(?:의)?\s*)?(이름|후보)',value.model_dump_json()):errors.append('한글 이름 후보는 한 개입니다. 여러 한자 조합을 여러 이름 후보라고 설명하지 마세요.')
    if any(p.strip() in ['reflection','paragraphs'] for p in value.paragraphs):errors.append('paragraphs의 모든 항목은 한국어 본문이어야 합니다. reflection 같은 필드 이름을 넣지 마세요.')
    return errors


def output_schema(schema,data):
    """Constrain identifiers to the actual names, separate from combinations."""
    result=copy.deepcopy(schema.model_json_schema())
    if schema is ComparisonDraft:
        ids=[p['id'] for p in data['candidates']]
        eligible=[p['id'] for p in data['candidates'] if p['recommendable']]
        result['properties']['choices'].update(minItems=len(ids),maxItems=len(ids))
        result['$defs']['Choice']['properties']['id']['enum']=ids
        result['properties']['recommended_ids']['items']['enum']=eligible or ids
        result['properties']['recommended_ids']['maxItems']=len(eligible)
        result['properties']['paragraphs']['items']['minLength']=70
    elif schema is NameDraft:
        ids=[c['id'] for c in data['candidates'][0]['combinations']]
        result['properties']['combinations'].update(minItems=len(ids),maxItems=len(ids))
        result['$defs']['CombinationDraft']['properties']['id']['enum']=ids
    return result


async def fresh_call(schema,data,instruction,validator,model,url,lock):
    constrained_schema=output_schema(schema,data)
    key=hashlib.sha256(json.dumps([CONFIG.provider,CONFIG.json_mode,model,SKILL.read_text(),constrained_schema,data,instruction],ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    now=time.monotonic()
    for k in list(CACHE):
        if now-CACHE[k][0]>1800:CACHE.pop(k,None)
    if key in CACHE:
        v,m=copy.deepcopy(CACHE[key][1]);m['cache_hit']=True
        return schema.model_validate(v),m
    user={'CALCULATIONS':data,'REQUEST':instruction}
    metrics=[];started=time.monotonic()
    for attempt in range(2):
        content,metric=await complete(constrained_schema,[
            {'role':'system','content':SKILL.read_text()+'\n이름 상담입니다. 확인된 한자와 뜻은 정확히 사용하고, 의미·발음·출생 참고 관계를 구분해 한국어 해요체로 충분히 설명하세요. 이전 개인 해설은 입력되지 않았습니다. '
             'registry.status=listed이면 제공된 syllable이 공식적으로 확인된 독음입니다. 다른 독음도 있다는 사실을 독음 불일치나 표준 한자가 아니라는 설명으로 바꾸지 마세요. '
             '예를 들어 率의 솔과 理·俐의 이는 공식 조회에서 확인된 독음이며, 률·리라는 다른 독음이 있어도 제공된 이름의 독음은 유효합니다. '
             '사전 뜻을 가족의 바람으로 설명하되 아이의 성격·감정·행동을 이미 정해진 사실처럼 예측하지 마세요. '
             '현재 JSON 스키마에 정의된 필드로만 작성하세요. paragraphs의 각 항목은 완성된 한국어 문단입니다. reflection 같은 필드 이름이나 영문 자리표시자를 본문에 넣지 마세요. '
             '길이 제한이 있는 summary와 reason은 짧은 완결 문장으로 끝내고 문장을 중간에 자르지 마세요.'},
            {'role':'user','content':json.dumps(user,ensure_ascii=False)}],model,url,lock,output_limit=3800)
        metrics.append(metric)
        try:
            value=schema.model_validate_json(content)
            value=normalize_vocabulary(value,data,context=schema is NameContext)
            errors=validator(value)
        except ValueError:errors=['요청한 JSON 구조와 글 길이를 지켜 완성하세요.']
        if not errors:break
        if attempt:raise ValueError('이름 해설 검증 실패: '+' / '.join(errors))
        user['VALIDATION_ERRORS']=errors
    metadata={'mode':'fresh_model','provider':CONFIG.provider,'model':model,'previous_reading_used':False,
              'input_sha256':key,'calls':metrics,'cache_hit':False,'seconds':round(time.monotonic()-started,2),
              'actual_models':list(dict.fromkeys(m.get('actual_model',model) for m in metrics)), 'vocabulary_normalized':True}
    if len(CACHE)>=32:CACHE.pop(next(iter(CACHE)))
    CACHE[key]=(time.monotonic(),(value.model_dump(),copy.deepcopy(metadata)))
    return value,metadata


async def generate_names(data,model,url,lock):
    reports=[];metrics=[]
    birth_reading=None
    if data['birth']:
        from api.model_readings import write
        birth_data=copy.deepcopy(data['birth']);birth_data['profile']['name']='아이'
        birth_reading=await write('saju',birth_data,data['knowledge'].get('references',[]),
            [('overview','같은 아이의 출생 명식을 이름 후보와 별도로 읽으세요. 계산한 계절과 전체 균형, 어떤 환경에서 배우고 표현할지 생활의 가정 예로 충분히 풀어주세요. 이름이나 한자가 사주를 바꾼다고 설명하지 마세요. 아이의 실제 성격·미래를 이미 알고 있다고 단정하지 마세요.')],model,url,lock)
        metrics.append(birth_reading['metadata'])
    for candidate in data['candidates']:
        context_data=material(data,candidate)
        context_data['candidates'][0].pop('combinations')
        context_data['candidates'][0].pop('selected_hanja')
        context_data['candidates'][0].pop('surname_hanja')
        context_data['birth']=None;context_data['knowledge']={}
        context,context_metadata=await fresh_call(NameContext,context_data,
            '이 후보의 한글 소리만 새로 설명하세요. chapters에는 sound 한 항목만 넣고 2~3단락으로 충분히 풀어주세요. '
            'sound에서는 성을 붙인 음절·모음·받침 구조를 가족의 실제 호칭 예로 설명하고, 듣는 인상을 객관적인 사실로 단정하지 마세요. '
            '초성의 오행이나 사주 적합도는 작성 입력에 없습니다. 그런 분류를 발명하지 마세요. '
            '한자의 뜻과 조합은 다른 해설에서 다루므로 여기에는 없습니다. 한자를 발명하거나 조합 의미를 이 장에 대신 쓰지 마세요. '
            '출생 해설은 같은 아이에 대해 공통으로 따로 보여줍니다. 여기에서 생일이나 시간이 없다고 안내하거나 사주를 해설하지 마세요. '
            '정해진 운명처럼 추천하거나 모두 좋은 이름이라고 포장하지 말고, 실제 확인 범위 안의 아쉬운 조건을 쓰세요.',
            lambda v:context_issues(v,context_data,candidate),model,url,lock)
        instruction=('이 이름의 한자 조합만 충분히 해설하세요. 소리나 출생 사주를 다시 해설하지 마세요. '
                     '각 한자 조합은 id 순서대로 모든 글자의 한자와 사전 뜻을 직접 풀고, 조합으로 담는 바람·다른 조합과의 차이·아쉬운 점을 2단락 이상 작성하세요. '
                     '한 글자가 여러 조합에 공통이어도 정의 단락 전체를 복사하지 말고 각 조합의 다른 글자와 어떻게 연결되는지 설명하세요. '
                     '후보에 해당하는 단점·선택 조건을 concerns에 쓰세요. 서로 다른 이름은 여기 입력되지 않았으니 비교 대상을 발명하지 마세요. '
                     '확인되지 않은 뜻·독음은 확인 필요라고 하고, 이름의 소리만으로 성격이나 미래를 단정하지 마세요. '
                     '한국어 meaning이 미정리라도 definition 원자료가 있으면 그 원문을 한국어로 풀어 설명할 수 있습니다. 원문에 없는 뜻을 발명하지 마세요. '
                     '한자 자원오행·획수 표가 없어 사주에 맞는 한자로 확정할 수 없습니다. 초성 오행이나 사주 적합도는 제공되지 않았으므로 새로 판정하지 마세요. '
                     '같은 한자가 있어도 의미 조합의 차이를 자세히 쓰세요. 공통 확인 범위 안내를 조합마다 그대로 반복하지 마세요. '
                     '성의 표기는 유지하세요. 추천을 방해하는 실제 조건이 있으면 솔직히 쓰되, 단순히 자료가 없다는 이유를 이름 자체의 결점으로 만들지 마세요. '
                     '추천할지·조건부로 비교할지·추천을 보류할지 이유가 분명해야 해요. 좋은 말로만 포장하지 마세요.')
        if candidate['combinations']:
            combo_data=material(data,candidate);combo_data['birth']=None;combo_data['knowledge']={}
            draft,metadata=await fresh_call(NameDraft,combo_data,instruction,
                lambda v:name_issues(v,data,candidate),model,url,lock)
        else:
            draft=NameDraft(**context.model_dump(exclude={'chapters'}),combinations=[])
            draft.status='needs_verification'
            metadata={'calls':[],'seconds':0,'actual_models':[],'previous_reading_used':False}
        combined={'mode':'fresh_model','previous_reading_used':False,'parts':[context_metadata,metadata],
                  'calls':context_metadata['calls']+metadata['calls'],'seconds':context_metadata['seconds']+metadata['seconds'],
                  'actual_models':list(dict.fromkeys(context_metadata['actual_models']+metadata['actual_models']))}
        recs=[]
        for combo,explained in zip(candidate['combinations'],draft.combinations):
            recs.append({**combo,'name':candidate['name'],'full_hanja':candidate['surname_hanja']+combo['name_hanja'],
                         'reason':explained.reason,'story':explained.paragraphs[0],'explanation':explained.paragraphs[1:],
                         'comparison':explained.consideration,'registry_confirmed':combo['verified'],
                         'selectable':combo['verified']})
        reports.append({**candidate,'title':draft.title,'summary':draft.summary,'verdict':draft.verdict,
                        'status':draft.status,'concerns':list(dict.fromkeys(draft.concerns+context.concerns)),
                        'chapters':[c.model_dump() for c in context.chapters],
                        'recommendations':recs,'hanja_status':'ready' if candidate['recommendable'] else 'needs_verification','generation':combined})
        metrics.append(combined)
    instruction=('같은 출생 정보로 입력한 이름 후보들을 비교하세요. 각 이름을 정확히 한 번씩 choices에 넣고 확인된 한자 조합과 '
                 '가족의 바람, 음절·받침 구조에 근거해 추천 이유와 아쉬운 점을 각각 구체적으로 설명하세요. '
                 'recommended_ids는 우선 비교할 이름을 순서대로 고르는 목록이에요. 전부를 억지로 추천하지 마세요. '
                 '우열을 정할 자료가 없으면 그렇게 설명하고 빈 추천 목록도 허용됩니다. 검증된 조합이 없는 이름은 추천 보류하세요. '
                 '한자가 검토되지 않았다는 사실은 이름 소리가 나쁘다는 뜻이 아닙니다. '
                 '사주 길흉 점수와 한자 자원오행·원획·81수리는 입력에 없으므로 발명하지 마세요. '
                 '최종 paragraphs에는 왜 이 이름들을 먼저 비교하는지, 어떤 취향·조건에서는 다른 후보가 나은지, 확인을 보류한 후보는 왜인지 풀어 쓰세요. '
                 '뜻의 사전 정의와 가족이 이름으로 담을 바람을 구분하세요. 이전 개인 풀이를 참고하지 마세요.')
    instruction+=f" 실제 한글 이름 후보는 {len(data['candidates'])}개이며 choices.id와 recommended_ids에는 이름 id {[p['id'] for p in data['candidates']]}만 사용하세요. option:*은 한자 조합 id로 이 두 필드에 넣지 마세요. 같은 이름의 여러 한자 조합을 여러 이름 후보로 세지 마세요."
    if len(data['candidates'])==1:instruction+=' 이름 하나의 선택 조건을 정리하는 상담입니다. 이름 간의 우열을 만들지 않고 같은 이름 안에서 한자 의미의 차이를 설명하세요.'
    comparison_data=material(data);comparison_data['birth']=None;comparison_data['knowledge']={}
    instruction+=' 같은 아이의 사주는 공통으로 따로 보여줍니다. 사주나 초성 오행을 추천 순위의 근거로 삼지 마세요. 음절·모음·받침과 확인된 한자 의미만 비교하세요.'
    comparison,metadata=await fresh_call(ComparisonDraft,comparison_data,instruction,lambda v:comparison_issues(v,data),model,url,lock)
    metrics.append(metadata)
    order={c.id:i for i,c in enumerate(comparison.choices)}
    for r in reports:
        choice=comparison.choices[order[r['id']]]
        r['comparison_reason']=choice.reason;r['comparison_concern']=choice.concern
        r['recommended_rank']=(comparison.recommended_ids.index(r['id'])+1) if r['id'] in comparison.recommended_ids else None
    return {'version':'fresh-naming-1','title':comparison.title,'summary':comparison.summary,
            'candidate_reports':reports,'comparison':comparison.model_dump(),
            'birth':data['birth'],'birth_reading':birth_reading,'surname_characters':data['surname_characters'],
            'scope':data['scope'],'registry_checked_at':data['registry_checked_at'],
            'preference_label':data['preference_label'],'source_ids':SOURCE_IDS,
            'generation':{'mode':'fresh_model','provider':CONFIG.provider,'model':model,'previous_reading_used':False,
                          'candidate_count':len(reports),'parts':metrics,'calls':[c for m in metrics for c in m['calls']],
                          'seconds':round(sum(m['seconds'] for m in metrics),2),
                          'actual_models':list(dict.fromkeys(n for m in metrics for n in m['actual_models']))}}


def preview_names(data):
    return {'version':'fresh-naming-1','title':'이름 후보를 하나씩 살펴보고 있어요.',
            'summary':'한자 뜻과 독음을 먼저 확인했어요. 이름별 해설과 비교 추천은 작성 중이에요.',
            'candidate_reports':[{**p,'chapters':[],'recommendations':[], 'concerns':[], 'analysis_pending':True} for p in data['candidates']],
            'comparison':None,'birth':data['birth'],'scope':data['scope'],'registry_checked_at':data['registry_checked_at'],
            'surname_characters':data['surname_characters'],
            'preference_label':data['preference_label'],'source_ids':SOURCE_IDS}


async def followup_name(session,question,model,url,lock):
    data=copy.deepcopy(session['name_calculations'])
    # A recommendation is a small comparison sample, never the dictionary.
    # Refresh original facts even if a question refers to a glyph not selected
    # for those three sample combinations (or an older session missed a glyph).
    syllables=set(''.join(p['name'] for p in data['candidates']))
    syllables.update(re.findall(r'(?<![가-힣])([가-힣])(?=\s*(?:[\(（]?한자|[\)）]|[\s,.!?]|$))',question))
    explicit=set(re.findall(r'[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff\U00020000-\U000323af]',question))
    lookup={}
    for syllable in sorted(syllables):
        rows=dictionary_options(syllable)
        rows.sort(key=lambda h:(h['character'] not in explicit,h['registry']['status']!='listed',not bool(h['meaning']),h['character']))
        lookup[syllable]=[pick(h,['character','syllable','meaning','definition','readings','registry']) for h in rows[:96]]
    data['dictionary_lookup']=lookup
    answer,metadata=await fresh_call(NameAnswer,material(data),
        '이름 상담의 후속 질문에 입력한 후보·공통 출생 계산과 dictionary_lookup의 다시 조회한 한자 자료로 2~3단락으로 답하세요. '
        '추천 조합은 전체 한자 목록이 아닙니다. 기존 추천에 없어도 dictionary_lookup에서 뜻·공식 독음을 확인한 글자는 설명하고 새로운 조합으로 비교할 수 있습니다. '
        '한국어 뜻이 없고 definition이 있으면 그 사전 원문만 번역해 설명하세요. 그 밖의 뜻을 발명하지 마세요. '
        '공식 독음 확인, 한국어 뜻 정리 여부, 이전 추천에 포함된 여부를 구분하세요. 자료 미조회·미정리를 한자 자체가 없거나 표준 한자가 아니라는 결론으로 바꾸지 마세요. '
        '공식 독음의 출처는 registry_source의 대법원 전자가족관계등록시스템입니다. 다른 기관명을 붙이지 마세요. '
        '입력한 한글 이름을 유지한 조합만 예시로 제시하세요. 率을 솔로 조회했으면 예시는 이솔(怡率)처럼 솔을 유지하세요. '
        '질문에 바로 답하고, 확인된 한자와 뜻 및 조합 예시를 2~3개의 짧은 문단으로 설명하세요. 질문: '+question,
        lambda v:prose_issues(v.answer,data),model,url,lock)
    return {'answer':answer.answer,'source_ids':SOURCE_IDS,'answer_mode':'fresh_model','generation':metadata}
