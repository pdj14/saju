"""One birth input, separate and traceable calculation systems."""
from datetime import timedelta, timezone
from itertools import combinations
import json
from pathlib import Path
import astronomy
from api.astrology_interpretation import build_astrology_narrative

HANJA_DATA=json.loads((Path(__file__).resolve().parents[1]/'knowledge/hanja-unihan.json').read_text())

SIGNS = ['양자리','황소자리','쌍둥이자리','게자리','사자자리','처녀자리','천칭자리','전갈자리','사수자리','염소자리','물병자리','물고기자리']
SIGN_WORDS = ['시작과 용기','꾸준함과 감각','호기심과 소통','돌봄과 친밀함','표현과 창의성','관찰과 정리','균형과 관계','깊이와 집중','탐색과 자유','책임과 지속','독립과 새로움','상상과 공감']
BODIES = [('Sun','태양','표현과 중심'),('Moon','달','익숙함과 돌봄'),
          ('Mercury','수성','생각과 소통'),('Venus','금성','가치와 관계'),('Mars','화성','행동과 추진'),
          ('Jupiter','목성','확장과 배움'),('Saturn','토성','구조와 책임'),('Uranus','천왕성','변화와 새로움'),
          ('Neptune','해왕성','상상과 이상'),('Pluto','명왕성','변환과 깊이')]
ASPECTS = [(0,'합','두 상징이 같은 방향에서 만나는 관계'),(60,'육분','두 상징의 연결을 살펴보는 관계'),
           (90,'사각','서로 다른 요구를 살펴보는 관계'),(120,'삼분','상징의 조화를 살펴보는 관계'),
           (180,'대립','마주 보는 두 관점을 살펴보는 관계')]

def astro_time(moment):
    utc=moment.astimezone(timezone.utc)
    return astronomy.Time.Make(utc.year,utc.month,utc.day,utc.hour,utc.minute,0)

def longitude(key, moment):
    t=astro_time(moment)
    if key=='Sun':
        return astronomy.SunPosition(t).elon % 360
    if key=='Moon':
        return astronomy.EclipticGeoMoon(t).lon % 360
    return astronomy.Ecliptic(astronomy.GeoVector(getattr(astronomy.Body,key),t,True)).elon % 360

def astrology_for(profile, local, *, include_interpretation=True):
    known=bool(profile.birth_time)
    positions=[]
    for key,label,role in BODIES:
        if key=='Moon' and not known:
            continue
        lon=longitude(key,local)
        index=int(lon//30)
        row={'key':key,'label':label,'role':role,'longitude':round(lon,3),
             'degree_in_sign':round(lon%30,2),'sign':SIGNS[index],'symbol':SIGN_WORDS[index],
             'sign_confirmed':True,'reference':'출생 시각' if known else '한국 시간 정오 참고'}
        if not known:
            # Check the entire civil birth date at hourly intervals; no fabricated time.
            start=local.replace(hour=0,minute=0)
            indices={int(longitude(key,start+timedelta(hours=h))//30) for h in range(25)}
            row['sign_confirmed']=len(indices)==1
            row['possible_signs']=[SIGNS[i] for i in sorted(indices)]
        positions.append(row)
    aspects=[]
    if known:
        for a,b in combinations(positions,2):
            gap=abs(a['longitude']-b['longitude'])
            separation=min(gap,360-gap)
            for angle,label,meaning in ASPECTS:
                orb=abs(separation-angle)
                if orb<=4:
                    aspects.append({'left':a['label'],'right':b['label'],'name':label,
                        'angle':angle,'separation':round(separation,3),'orb':round(orb,3),'meaning':meaning})
        aspects.sort(key=lambda a:a['orb'])
    sun=positions[0]
    result={'sun':sun,'positions':positions,'aspects':aspects,'aspect_orb':4,
        'hour_known':known,'sun_boundary_day':not sun['sign_confirmed'],
        'method':'열대황도 12궁 · 지심 황경 · 한국 시간 → UTC · Astronomy Engine 2.1.19',
        'scope':'태양·달·8개 행성의 위치와 주요 5종 각도. 상승궁·하우스·역행·트랜짓·베다 점성술은 미계산.',
        'source_ids':['stars-natal','stars-time','stars-aspects','stars-symbols']}
    if known:
        result['moon']=next(p for p in positions if p['key']=='Moon')
    result['interpretation']=build_astrology_narrative(result) if include_interpretation else []
    result['source_ids'].append('profile-interpretation-rules')
    return result

def name_for(profile, initials, sound_elements):
    if not profile.name:
        return {'available':False,'reason':'이름을 입력하면 같은 리포트에서 한글 소리와 발음오행을 함께 볼 수 있어요.',
                'source_ids':['name-sound','name-elements']}
    letters=[{'syllable':c,'initial':initials[(ord(c)-0xAC00)//588],
              'element':sound_elements[initials[(ord(c)-0xAC00)//588]]} for c in profile.name]
    hanja=[]
    for character,syllable in zip(profile.name_hanja,profile.name):
        entry=HANJA_DATA.get(character,{})
        hanja.append({'character':character,'syllable':syllable,'readings':entry.get('readings',[]),
            'meaning':entry.get('meaning_ko'),'definition':entry.get('definition'),
            'verified':bool(entry.get('definition')),
            'reading_matches':syllable in entry['readings'] if entry.get('readings') else None})
    labels=[h['meaning'] for h in hanja if h['meaning']]
    explanation=''
    if hanja and len(labels)==len(hanja):
        explanation='입력한 '+profile.name_hanja+'는 '+', '.join(h['character']+'의 ‘'+h['meaning']+'’' for h in hanja)+'이라는 뜻을 함께 담아요. '
        explanation+='이름의 뜻을 연결해 가족이 어떤 의미를 담고 싶은지 이야기할 수 있어요. 글자 뜻의 연결과 사주에 맞는 작명 판정은 별도로 살펴야 합니다.'
    elif hanja:
        explanation='입력한 한자를 사전에서 찾아 뜻과 독음을 함께 표시했어요. 한국어로 정리하지 않은 뜻은 원자료를 펼쳐 확인할 수 있고, 확인되지 않은 뜻은 임의로 만들지 않았어요.'
    return {'available':True,'name':profile.name,'surname':profile.surname,'name_hanja':profile.name_hanja,
        'display_name':profile.surname+profile.name,'surname_hanja':profile.surname_hanja,'syllables':len(profile.name),'letters':letters,
        'initials':[l['initial'] for l in letters],'sound_elements':[l['element'] for l in letters],
        'hanja_provided':bool(profile.name_hanja),'hanja':hanja,'hanja_explanation':explanation,'surname_provided':bool(profile.surname),
        'method':'이름 부분의 한글 초성 발음오행 · 된소리는 기본 자음에 대응',
        'scope':'입력한 한자의 사전 뜻과 독음을 살펴봐요. 작명용 원획·자원오행·81수리 길흉은 아직 판정하지 않아요. 인명용 글자와 독음은 이름 상담의 공식 조회 자료에서 확인해요.',
        'source_ids':['name-sound','name-elements','name-standard']+(['name-hanja-dictionary'] if hanja else [])}

def enrich_report(report, astrology, name, *, include_interpretation=True):
    from api.interpretation import build_narrative
    """Keep eastern five elements separate from western zodiac symbolism."""
    year=next(p for p in report['pillars'] if p['position']=='year')
    animals=dict(zip('子丑寅卯辰巳午未申酉戌亥',['쥐','소','호랑이','토끼','용','뱀','말','양','원숭이','닭','개','돼지']))
    animal=animals[year['branch']['hanja']]
    day=next(p for p in report['pillars'] if p['position']=='day')
    sun=astrology['sun']
    return {**report,'astrology':astrology,'name_analysis':name,
        'year_symbol':{'animal':animal,'branch':year['branch']['hanja'],'method':'사주 년지 기준 · 입춘 경계 적용'},
        'overview':[{'label':'사주','value':day['ganji']+' 일주','detail':report['month']['season']+'의 절기 월 · '+str(report['element_total'])+'글자'},
                    {'label':'점성술','value':sun['sign'] if sun['sign_confirmed'] else '태양 경계일',
                     'detail':str(len(astrology['positions']))+'개 천체 · '+('출생 시각 기준' if astrology['hour_known'] else '정오 참고')},
                    {'label':'이름','value':name['display_name'] if name['available'] else '이름 미입력',
                     'detail':str(name['syllables'])+'음절 · 초성 발음오행' if name['available'] else '이름 입력 시 함께 분석'}],
        'comparison':{'title':'같은 생일, 서로 다른 읽는 기준',
            'saju':build_narrative(report)[0]['lead'] if include_interpretation else '사주 해설은 별도 항목에서 읽어요.',
            'astrology':f"점성술은 태양의 {sun['sign']}를 {sun['symbol']}의 상징으로 읽어요." if sun['sign_confirmed'] else '이날은 태양이 별자리 경계를 지나 출생 시각을 확인해야 해요.',
            'reflection':'사주의 일과 관계에 관한 질문과 별자리의 상징 중, 내 경험을 돌아보는 데 도움이 되는 관점을 골라보세요.',
            'note':'두 가지는 서로 다른 해석 방법이에요. 비슷한 설명이 나와도 더 정확하다는 증거는 아니고, 합쳐서 하나의 점수로 만들지 않았어요.',
            'source_ids':['saju-daymaster','stars-symbols','profile-comparison']},
        'input_coverage':[{'label':'생년월일','status':'확인','text':'사주 년·월·일주, 태양·행성 별자리'},
            {'label':'출생 시간','status':'확인' if astrology['hour_known'] else '미입력',
             'text':'시주·강약·용신, 달의 별자리·천체 각도' if astrology['hour_known'] else '시주·강약·용신·달·천체 각도는 생략'},
            {'label':'이름','status':'확인' if name['available'] else '미입력','text':'한글 소리와 발음오행' if name['available'] else '이름 풀이 생략'},
            {'label':'추가 분석','status':'미지원','text':'대운·세운, 상승궁·하우스, 원획·81수리 길흉은 아직 제공하지 않아요.'}]}
