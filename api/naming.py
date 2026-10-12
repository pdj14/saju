"""Traceable naming consultation: individual meanings, sound and birth context.

Recommendations search dictionary facts with confirmed readings in an official
Court lookup snapshot. Editorial themes affect ordering, not lookup coverage.
No stroke numerology or character-element table
is inferred from a radical, dictionary stroke count, or a language model.
"""
from itertools import product
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
DICTIONARY=json.loads((ROOT/'knowledge/hanja-unihan.json').read_text())
EDITORIAL=json.loads((ROOT/'knowledge/naming-editorial.json').read_text())
CHARACTER_NOTES=json.loads((ROOT/'knowledge/naming-character-notes.json').read_text())['characters']
REGISTRY_PATH=ROOT/'knowledge/name-registry.json'
REGISTRY=json.loads(REGISTRY_PATH.read_text()) if REGISTRY_PATH.exists() else {'readings':{},'checked_at':None}
COURT_URL='https://efamily.scourt.go.kr/cs/CsBltnWrtList.do?bltnbordId=0000010'
THEMES=EDITORIAL['themes']
CHAR_THEMES={}
for theme,data in THEMES.items():
    for char in data['characters']:
        if DICTIONARY.get(char,{}).get('meaning_ko'):
            CHAR_THEMES.setdefault(char,[]).append(theme)

def registry_check(char,reading):
    rows=REGISTRY['readings'].get(reading)
    status='unverified' if rows is None else 'listed' if char in rows else 'not_found'
    return {'status':status,'label':{'listed':'이 독음으로 공식 조회 확인','not_found':'이 독음의 조회 목록에서 확인되지 않음','unverified':'공식 독음 확인 필요'}[status],
            'checked_at':REGISTRY.get('reading_checked_at',{}).get(reading,REGISTRY['checked_at']),'source_url':COURT_URL}

def character_detail(char,syllable,index,kind='name'):
    entry=DICTIONARY.get(char,{})
    themes=CHAR_THEMES.get(char,[])
    label='성' if kind=='surname' else f'이름 {index+1}번째 글자'
    meaning=entry.get('reading_meanings',{}).get(syllable) or entry.get('meaning_ko')
    wish=''
    if kind=='surname':
        wish='성은 가족에게서 이어받은 표기예요. 이름 추천에서는 선택한 성을 유지하고, 이름 부분의 글자 조합을 비교합니다.'
    elif themes:
        wish=THEMES[themes[0]]['wish']+'을 이 글자에 담아볼 수 있어요. 이는 사전 뜻을 바탕으로 연결한 이름의 바람이에요.'
    elif meaning:
        wish='‘'+meaning+'’이라는 사전 뜻 중 가족이 이름에 담고 싶은 의미가 무엇인지 살펴볼 수 있어요. 별도의 검토 없이 작명 추천 후보로 넣지는 않았어요.'
    else:
        wish='한국어 뜻을 아직 정리하지 못해 원자료를 함께 보여드려요. 확인하지 못한 뜻으로 추천 문장을 만들지 않았어요.'
    detail=CHARACTER_NOTES.get(char) if meaning and kind=='name' else None
    if not detail and meaning and kind=='name':
        detail=[f'이 글자의 확인된 뜻은 ‘{meaning}’이에요. 이름에서는 이 뜻 중 가족이 직접 담고 싶은 의미를 골라 읽어요.',
                wish,'세밀한 글자별 의미 검토가 아직 없는 글자예요. 사전 뜻 밖의 특별한 성격·능력까지 추천 근거로 더하지 않았습니다.']
    return {'character':char,'syllable':syllable,'position':label,'kind':kind,
            'meaning':meaning,'definition':entry.get('definition'),'readings':entry.get('readings',[]),
            'dictionary_reading_matches':syllable in entry.get('readings',[]),'wish':wish,
            'themes':[THEMES[t]['label'] for t in themes],
            'interpretation':detail[0] if detail else '',
            'good_for':detail[1] if detail else '',
            'consideration':detail[2] if detail else '',
            'registry':registry_check(char,syllable) if kind=='name' else {'status':'surname','label':'가족의 성씨 한자 확인','source_url':COURT_URL,'checked_at':None}}


def dictionary_options(syllable):
    """Join dictionary and Court readings without using an editorial whitelist."""
    official=set(REGISTRY['readings'].get(syllable,[]))
    chars=[c for c,d in DICTIONARY.items()
           if syllable in d.get('readings',[]) or c in official]
    return [character_detail(c,syllable,0) for c in chars]


def has_verified_meaning(detail):
    # An untranslated source definition is still dictionary evidence. Models may
    # translate it, but must not invent a Korean meaning without that source.
    return bool(detail['meaning'] or detail['definition']) and detail['registry']['status']=='listed'

def meaning_story(hanja,preference):
    name_chars=[h for h in hanja if h['kind']=='name']
    if not name_chars:return '이름의 소리는 정해져 있어요. 글자별 한자를 선택하면 같은 소리에 어떤 뜻을 담을지 함께 비교할 수 있습니다.'
    if any(not h['meaning'] for h in name_chars):return '선택한 글자의 뜻과 독음을 하나씩 확인했어요. 아직 한국어 뜻을 정리하지 못한 글자가 있어, 이름 전체의 의미를 확정해 연결하지는 않았습니다.'
    terms='와 '.join(h['character']+'의 ‘'+h['meaning']+'’' for h in name_chars)
    themes=list(dict.fromkeys(t for h in name_chars for t in CHAR_THEMES.get(h['character'],[])))
    target=preference if preference in themes else themes[0] if themes else None
    story=terms+'을 함께 담은 조합이에요. '
    if target:story+='이 뜻을 이름의 바람으로 풀면, '+THEMES[target]['wish']+'으로 연결해볼 수 있어요. '
    story+='글자 뜻을 조합해 가족의 뜻을 담은 설명이며, 이미 정해진 사전 단어의 뜻이나 아이의 미래를 단정한 문장은 아니에요.'
    return story

def combination_details(chars,preference):
    """Explain meaning emphasis and tradeoffs; never call them fate scores."""
    selected=[h for h in chars if h['kind']=='name']
    if not selected or any(not h['meaning'] for h in selected):return []
    paras=[f"첫 글자 {selected[0]['character']}({selected[0]['syllable']})는 이름의 앞에서 ‘{selected[0]['meaning']}’을 먼저 보여줘요. "+selected[0]['interpretation']]
    if len(selected)>1:
        last=selected[-1]
        paras.append(f"뒤의 {last['character']}({last['syllable']})는 ‘{last['meaning']}’을 이어 담아요. "+last['interpretation'])
    themes=[set(CHAR_THEMES.get(h['character'],[])) for h in selected]
    common=set.intersection(*themes) if themes else set()
    if common:
        target=preference if preference in common else sorted(common)[0]
        paras.append(f"선택한 글자들의 의미는 ‘{THEMES[target]['label']}’이라는 방향에서 겹쳐요. 뜻을 한 방향으로 선명하게 모으는 조합이라 그 가치를 가장 강조하고 싶은 가족에게 비교할 만합니다. 반면 서로 다른 가치를 넓게 담는 이름보다 의미의 폭은 좁아질 수 있어요. 같은 주제라는 사실이 다른 조합보다 길하다는 뜻은 아닙니다." if len(selected)>1 else
                     f"이 글자는 ‘{THEMES[target]['label']}’의 바람과 연결해 읽을 수 있어요. 실제 성격을 예측한 것이 아니라 이름으로 전하고 싶은 가치를 담는 방식입니다.")
    else:
        labels=list(dict.fromkeys(t for h in selected for t in h['themes']))
        paras.append('이 조합은 '+('과 '.join(labels) if labels else '서로 다른 사전 뜻')+'을 함께 담는 방향이에요. 하나의 능력만 강조하기보다 다른 가치를 곁에 두는 이름으로 읽을 수 있어요. 다만 각 뜻을 어떻게 하나의 이야기로 전할지는 가족의 바람이 있어야 자연스럽습니다.')
    if len(selected)>1:
        first,last=selected[0],selected[-1]
        paras.append(f"이름의 뜻을 소개한다고 생각하면 이해가 쉬워요. ‘{first['character']}에는 {first['meaning']}이라는 뜻을, {last['character']}에는 {last['meaning']}이라는 뜻을 담았어요’라고 말할 수 있습니다. 첫 글자의 바람을 선명하게 강조할지, 뒤 글자의 다른 느낌도 함께 전할지에 따라 선택이 달라져요. 아이가 이미 그런 성격이라는 평가보다 가족이 이름으로 건네고 싶은 이야기입니다.")
    return paras

def candidate_comparison(details,profile):
    current=[character_detail(c,s,i) for i,(c,s) in enumerate(zip(profile.name_hanja,profile.name))]
    if not current:return '현재 선택한 한자가 없어 우열을 정하지 않았어요. 같은 한글 이름 안에서 이 후보가 어떤 뜻을 담는지 먼저 비교할 수 있어요.'
    changes=[]
    for old,new in zip(current,details):
        if old['character']==new['character']:continue
        changes.append(f"‘{new['syllable']}’을 {old['character']}의 ‘{old['meaning'] or '한국어 뜻 확인 필요'}’에서 {new['character']}의 ‘{new['meaning']}’으로 바꿔요. "+new['interpretation'])
    common=set.intersection(*(set(CHAR_THEMES.get(h['character'],[])) for h in details))
    current_common=set.intersection(*(set(CHAR_THEMES.get(h['character'],[])) for h in current))
    if common and not current_common:
        changes.append('현재 조합보다 뜻이 한 주제로 모이는 차이가 있어요. 의미를 집중하고 싶을 때 비교할 후보이고, 여러 가치를 함께 담고 싶다면 현재 조합의 장점도 남아 있어요.')
    elif not common and current_common:
        changes.append('현재 조합보다 뜻의 방향을 넓히는 차이가 있어요. 한 주제를 선명하게 강조하고 싶다면 현재 조합을, 서로 다른 가치를 함께 담고 싶다면 이 후보를 비교할 수 있습니다.')
    else:changes.append('같은 주제 안에서도 각 글자의 구체적인 뜻이 달라져요. 어느 쪽이 더 좋은지는 아이의 미래 점수가 아니라 가족이 전하고 싶은 바람에 따라 달라집니다.')
    return ' '.join(changes)

def sound_details(profile,name):
    vowels='ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
    finals=['없음']+list('ㄱㄲ')+['ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
    rows=[]
    for h in name['letters']:
        code=ord(h['syllable'])-0xAC00
        rows.append({**h,'vowel':vowels[(code%588)//28],'final':finals[code%28]})
    description=' · '.join(f"{h['syllable']}: 초성 {h['initial']}, 모음 {h['vowel']}, 받침 {h['final']}" for h in rows)
    end=rows[-1]['final']
    if end=='없음':ending='마지막 음절에는 받침이 없어 글자 구성상 모음으로 끝나요. 이름만 부를 때와 성을 붙여 부를 때의 끝소리가 어떻게 들리는지 비교할 수 있어요.'
    elif end in ['ㄴ','ㅁ','ㅇ','ㄹ']:ending=f'마지막 음절은 {end} 받침으로 끝나요. 받침 없이 끝나는 이름과 달리 끝에 자음이 남는 구조예요. 글자 구성은 확인할 수 있지만 부드럽다·강하다는 인상은 듣는 사람과 말투에 따라 다릅니다.'
    else:ending=f'마지막 음절은 {end} 받침으로 끝나요. 뒤에 붙는 말에 따라 실제 소리는 달라질 수 있으니 이름을 단독으로 부를 때와 이어 부를 때를 함께 들어볼 부분입니다.'
    return rows,[f"‘{profile.name}’은 {len(rows)}음절이에요. 글자별 소리 구성은 {description}입니다. "+ending,
        f"한자를 바꿔도 한글이 ‘{profile.name}’으로 같으면 부르는 소리는 같아요. 후보 사이의 차이는 발음의 좋고 나쁨이 아니라 이름에 담는 뜻입니다. 성을 붙인 ‘{profile.surname+profile.name}’, 이름만 부르는 ‘{profile.name}’, 가족이 쓰는 호칭을 연이어 읽으면 실제 사용감을 비교할 수 있어요."]

def candidates(profile):
    if len(profile.name)>4:return [],'이름이 다섯 글자 이상이면 현재 후보 조합 추천은 생략해요. 선택한 글자의 뜻은 각각 확인할 수 있습니다.'
    slots=[]
    pref=profile.naming_preference
    for syllable in profile.name:
        pool=[h['character'] for h in dictionary_options(syllable) if has_verified_meaning(h)]
        pool.sort(key=lambda c:(-(pref in CHAR_THEMES.get(c,[])),
                               not bool(DICTIONARY[c].get('reading_meanings',{}).get(syllable) or DICTIONARY[c].get('meaning_ko')),
                               c not in CHAR_THEMES,c))
        if not pool:return [],f'‘{syllable}’의 공식 독음과 사전 뜻을 함께 확인한 후보가 현재 자료에서 나오지 않았어요. 해당 한자가 존재하지 않는다는 뜻은 아니며, 확인되지 않은 글자를 대신 추천하지 않았습니다.'
        slots.append(pool[:8])
    rows=[]
    for combo in product(*slots):
        chars=''.join(combo)
        if len(set(combo))!=len(combo) and len(combo)>1:continue
        hits=sum(pref in CHAR_THEMES.get(c,[]) for c in combo)
        themes=list(dict.fromkeys(t for c in combo for t in CHAR_THEMES.get(c,[])))
        # Internal ordering is meaning preference only, never a fortune rating.
        korean=sum(bool(DICTIONARY[c].get('reading_meanings',{}).get(s) or DICTIONARY[c].get('meaning_ko')) for c,s in zip(combo,profile.name))
        priority=sum(EDITORIAL.get('reading_priority',{}).get(s,'').find(c)
                     if c in EDITORIAL.get('reading_priority',{}).get(s,'') else
                     len(EDITORIAL.get('reading_priority',{}).get(s,'')) for c,s in zip(combo,profile.name))
        rows.append((hits,len(themes),chars,combo,korean,priority))
    rows.sort(key=lambda r:(-r[0],-r[4],-r[1],r[5],r[2]))
    ranks={r[2]:i for i,r in enumerate(rows)}
    chosen=[]
    remaining=[r for r in rows if r[2]!=profile.name_hanja]
    seen=set(enumerate(profile.name_hanja))
    while remaining and len(chosen)<3:
        # Compare different positions, including alternative last characters.
        # The old first-character-only diversity rule hid alternate readings.
        row=min(remaining,key=lambda r:(-r[0],-r[4],-sum((i,c) not in seen for i,c in enumerate(r[3])),ranks[r[2]]))
        remaining.remove(row)
        _,_,chars,combo,_,_=row
        seen.update(enumerate(combo))
        details=[character_detail(c,s,i) for i,(c,s) in enumerate(zip(combo,profile.name))]
        hits=[s for c,s in zip(combo,profile.name) if pref in CHAR_THEMES.get(c,[])]
        reason=('원하신 ‘'+THEMES[pref]['label']+'’의 바람과 뜻이 이어지는 글자가 '+', '.join(hits)+'에 있어 먼저 비교할 만해요.' if hits else
                '글자마다 사전 뜻과 독음이 확인되고, 이름에 담을 바람을 설명할 수 있어 비교 후보로 골랐어요.')
        chosen.append({'name':profile.name,'name_hanja':chars,'display_name':profile.surname+profile.name,
                       'full_hanja':profile.surname_hanja+chars,'characters':details,'reason':reason,
                       'story':meaning_story(details,pref),'explanation':combination_details(details,pref),
                       'comparison':candidate_comparison(details,profile),
                       'label':'뜻을 비교할 조합','registry_confirmed':True})
        if len(chosen)==3:break
    return chosen,('같은 한글 이름을 유지하고, 뜻이 달라지는 한자 조합을 골랐어요. 추천 순서는 가족이 선택한 바람과 사전 뜻의 연결을 기준으로 합니다.' if chosen else
                   '검토한 후보가 현재 선택한 조합과 같거나 다른 조합이 없어 추가 추천은 표시하지 않았어요.')

def build_naming(profile,name,chart=None):
    chart=chart or {};pref=profile.naming_preference
    chars=[character_detail(c,s,i,'surname') for i,(c,s) in enumerate(zip(profile.surname_hanja,profile.surname))]
    chars += [character_detail(c,s,i) for i,(c,s) in enumerate(zip(profile.name_hanja,profile.name))]
    missing=[]
    if not profile.name_hanja:missing.append('이름 한자')
    if not profile.birth_date:missing.append('생년월일')
    if profile.birth_date and not profile.birth_time:missing.append('출생 시간')
    name_chars=[h for h in chars if h['kind']=='name']
    checks=[]
    if name_chars:
        checks.append({'label':'이름 글자 수','status':'확인','text':f'한글 {len(profile.name)}글자와 한자 {len(profile.name_hanja)}글자를 대응했어요.'})
        bad=[h['syllable'] for h in name_chars if h['registry']['status']!='listed']
        checks.append({'label':'인명용 글자와 독음','status':'추가 확인' if bad else '조회 확인',
            'text':(' · '.join(bad)+'의 선택 글자는 공식 독음 확인이 더 필요해요.' if bad else
                    f"모든 이름 글자가 입력한 독음의 공식 조회 목록에 있어요. 조회일 {REGISTRY['checked_at']} 기준입니다.")})
    else:checks.append({'label':'이름 글자의 뜻','status':'선택 필요','text':'한자를 선택하면 글자별 뜻과 조합의 의미를 읽을 수 있어요. 한글 이름도 그대로 사용할 수 있습니다.'})
    pref_label=THEMES[pref]['label'] if pref in THEMES else '뜻을 고르게 살펴보기'
    story=meaning_story(chars,pref)
    matches=[h['syllable'] for h in name_chars if pref in CHAR_THEMES.get(h['character'],[])]
    if pref in THEMES:
        preference_text=(f"원하신 ‘{pref_label}’의 의미와 연결해볼 글자는 {', '.join(matches)}이에요. "+THEMES[pref]['wish']+'을 이 이름에 담아볼 수 있습니다.' if matches else
            f"원하신 ‘{pref_label}’의 바람과 직접 연결해 편집한 글자는 현재 조합에서 확인되지 않았어요. 아래 다른 한자 조합을 비교해 같은 소리에 원하는 뜻을 담을 수 있는지 살펴보면 좋아요.")
    else:preference_text='한 가지 뜻만 정답으로 고르기보다, 각 글자가 담는 의미가 가족의 바람과 자연스럽게 이어지는지 살펴봤어요. 아래 후보는 같은 소리 안에서 뜻을 비교할 수 있도록 골랐습니다.'
    birth={'available':bool(chart),'hour_known':bool(profile.birth_time),'expected':bool(chart.get('birth_is_expected')),'yong_element':None,'matched_syllables':[]}
    if chart:
        from api.chart_context import context, role_for
        report=chart['report'];day=next(p for p in report['pillars'] if p['position']=='day')
        birth.update(day_pillar=day['ganji'],day_reading=day['reading'],season=report['month']['season'],elements=report['elements'])
        birth['text']=f"입력한 출생 정보로 계산한 일주는 {day['reading']}({day['ganji']})이며, {report['month']['season']}의 절기 월이에요. "+('출생 시간까지 넣어 네 기둥을 계산했어요.' if profile.birth_time else '시간이 없어 연·월·일 세 기둥만 계산했어요.')
        b=report['balance']
        if b['available'] and b.get('yong_element'):
            birth.update(yong_element=b['yong_element'],method=b['yong_method'])
            birth['matched_syllables']=[l['syllable'] for l in name['letters'] if l['element']==b['yong_element']]
            birth['connection']=f"사주의 균형 기준인 용신은 {b['yong_element']}({b['yong_method']})로 계산돼요. 이름의 초성 발음오행에서는 "+(' · '.join(birth['matched_syllables'])+' 음절이 같은 분류에 있어요.' if birth['matched_syllables'] else '그 분류에 해당하는 음절이 보이지 않아요.')+' 두 결과를 나란히 확인한 참고이며, 한자 자체의 자원오행을 판정하거나 이름이 용신을 보완했다고 결론낸 것은 아닙니다.'
        else:birth['connection']=('출생 시간이 없어 용신과 전체 강약은 확정하지 않았어요.' if not profile.birth_time else '이 계산에서 용신을 선택하지 않아 보완 오행을 확정하지 않았어요.')+' 겉 글자의 분포만으로 이름의 오행을 골라야 한다고 정하지 않았습니다.'
        if birth['expected']:birth['note']='예정일로 살펴본 참고 결과예요. 실제 생년월일시가 정해지면 사주와 이름의 참고 관계를 다시 확인해야 해요.'
        birth['detail']=context(report)['seasonal']
        if birth['yong_element']:
            birth['detail']+=f" 균형 기준인 {birth['yong_element']}는 이 일간에 {role_for(birth['yong_element'],day['stem']['element'])}의 관계예요. 숫자가 가장 적은 오행을 무조건 채운 것이 아니라, 계산에서 선택한 {birth['method']}의 조건을 함께 본 결과입니다."
    else:
        birth['text']='생년월일을 더하면 사주의 글자와 계절도 함께 살펴볼 수 있어요. 태어난 시간까지 알면 네 기둥과 균형 기준을 확인할 수 있습니다.'
        birth['connection']='지금은 이름의 소리·한자 뜻·조합을 먼저 비교했어요. 생일이나 시간을 임의로 정해 사주와 맞는 이름이라고 안내하지 않았습니다.'
    recs,rec_note=candidates(profile)
    has_meanings=bool(name_chars) and all(h['meaning'] for h in name_chars)
    summary=(f"‘{profile.surname+profile.name}({profile.name_hanja})’은 "+' · '.join(h['meaning'] for h in name_chars)+'을 담는 조합이에요. 같은 소리에서 이 뜻을 집중할지 넓힐지, 다른 한자 후보와 비교했어요.' if has_meanings else
             f"‘{profile.surname+profile.name}’의 소리를 유지하면서 어떤 뜻을 담을지 비교해봐요. 글자별 의미가 확인된 한자 조합을 추천해드려요.")
    sound_rows,sound_paras=sound_details(profile,name)
    chapters=[{'topic':'meaning','title':'이 조합이 담는 뜻과 선택할 때의 차이','paragraphs':[story]+combination_details(chars,pref)+[preference_text]},
              {'topic':'sound','title':'매일 부를 이름의 소리도 함께 봤어요','paragraphs':[
                  *sound_paras,
                  '이름 부분의 초성은 '+' · '.join(name['initials'])+'이며, 발음오행의 한 가지 기준에서는 '+' → '.join(name['sound_elements'])+'으로 분류돼요. 이는 소리에 붙인 전통 분류이고, 한자의 뜻이나 오행과는 따로 살펴야 합니다.',
                  f"‘{profile.surname+profile.name}’처럼 성을 붙여 불렀을 때와 ‘{profile.name}’만 불렀을 때를 함께 들어보면 좋아요. 가족이 평소 쓰는 말투에서도 편하게 부를 수 있는지 확인하면 글자의 뜻과 실제 사용하는 이름을 같이 생각할 수 있어요."]},
              {'topic':'birth','title':'아이의 출생 정보와 나란히 살펴보면','paragraphs':[birth['text']]+([birth['detail']] if birth.get('detail') else [])+[birth['connection'],
                  '아래 후보는 같은 한글 이름을 유지하므로 초성 발음오행도 같아요. 후보를 고르는 이유는 글자 뜻의 차이이며, 한자를 바꾸면 사주 적합도가 높아진다고 계산한 추천은 아닙니다.']+([birth['note']] if birth.get('note') else [])}]
    return {'version':'2.0','title':(profile.surname+profile.name)+' 이름 상담 리포트','summary':summary,
            'display_name':profile.surname+profile.name,'name':profile.name,'name_hanja':profile.name_hanja,
            'surname':profile.surname,'surname_hanja':profile.surname_hanja,'full_hanja':profile.surname_hanja+profile.name_hanja,
            'preference':pref,'preference_label':pref_label,'characters':chars,'chapters':chapters,'birth':birth,
            'checks':checks,'sound_structure':sound_rows,'recommendations':recs,'recommendation_note':rec_note,
            'recommendation_status':'ready' if recs else 'unavailable','missing_inputs':missing,
            'scope':'한자 뜻·공식 독음 조회·소리 구성·출생 명식의 참고 관계와 뜻 중심의 한자 조합 추천. 원획·81수리·자원오행 길흉은 아직 판정하지 않아요.',
            'registry_checked_at':REGISTRY['checked_at'],
            'source_ids':['name-hanja-dictionary','name-sound','name-elements','name-registry','name-recommendation-rules']}
