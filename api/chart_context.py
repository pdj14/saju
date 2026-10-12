"""Position-aware, traceable editorial interpretation of calculated observations.

The engine supplies the facts. These modern applications are our own reading
rules, not empirical personality diagnoses or a claim of classical quotations.
No count ranking is used as a substitute for the engine's strength judgement.
"""
import re
from api.reading_voice import ROLE_VOICE

CYCLE=['목','화','토','금','수']
GROUPS={'비겁':['비견','겁재'],'식상':['식신','상관'],'재성':['편재','정재'],'관성':['편관','정관'],'인성':['편인','정인']}
GROUP_OF={n:g for g,ns in GROUPS.items() for n in ns}
WORK_HEAD={'비견':'내 판단으로 방향을 정하고','겁재':'함께 움직이며 몫을 나누고','식신':'생각과 재능을 결과로 만들고','상관':'더 나은 방법을 찾고','편재':'밖의 기회를 연결하고','정재':'약속한 결과를 유지하고','편관':'어려운 과제를 책임지고','정관':'기준을 지키며 신뢰를 쌓고','편인':'다른 관점을 깊이 탐구하고','정인':'이해의 바탕을 쌓고'}
PRIVATE_HEAD={'비견':'각자의 선택을 존중받고 싶은 사람','겁재':'동등한 편이 되어주길 바라는 사람','식신':'일상 속 다정함을 바라는 사람','상관':'솔직한 생각을 나누고 싶은 사람','편재':'함께 경험을 넓히고 싶은 사람','정재':'생활 속 일관된 약속을 바라는 사람','편관':'힘든 순간에도 책임져주길 바라는 사람','정관':'분명한 약속을 바라는 사람','편인':'개인 시간과 깊은 대화를 바라는 사람','정인':'차분한 설명과 도움을 바라는 사람'}
GODS={
 '비견':{'need':'스스로 선택할 권한','gift':'자기 판단으로 방향을 지키는 힘','risk':'도움을 간섭으로 받아들이며 혼자 결정하는 태도','work':'결정권과 담당 범위가 분명한 업무','private':'가까운 사이에서도 선택을 존중받고 싶은 마음','test':'같이 정하는 일에서 상대의 의견을 듣기 전에 내 결론부터 정하는지','money':'내가 기여한 만큼의 몫과 독립적인 자원 관리','example':'둘이 여행을 준비할 때도 각자 꼭 하고 싶은 일정이 남아 있어야 편할 수 있어요.'},
 '겁재':{'need':'함께 움직이되 공정하게 나누는 관계','gift':'사람을 모아 힘을 합치는 추진력','risk':'공동의 목표가 몫과 비교를 둘러싼 경쟁으로 바뀌는 태도','work':'협업의 역할과 기여를 명확히 나누는 업무','private':'나를 동등한 사람으로 대하고 편을 들어주길 바라는 마음','test':'함께 잘된 일을 기뻐하면서도 누가 더 인정받았는지 계속 비교하는지','money':'공동 비용·보상·권한을 누구와 어떻게 나누는가','example':'함께 일을 끝냈어도 한 사람만 칭찬받으면 결과보다 공정한 인정이 마음에 남을 수 있어요.'},
 '식신':{'need':'자기 생각과 재능을 직접 펼칠 시간','gift':'생각과 재능을 표현하고 결과로 만드는 힘','risk':'만드는 재미와 완성도에 몰입해 마감과 상대의 필요를 놓치는 태도','work':'기획·창작·제작·교육처럼 생각을 실제 결과로 옮기는 업무','private':'말만 큰 약속보다 일상의 다정한 행동을 바라는 마음','test':'내가 만들고 싶은 것과 상대에게 필요한 결과가 같은지','money':'직접 만든 결과물·기술·서비스와 그에 필요한 비용','example':'함께 먹을 식사를 챙기거나 약속한 일을 해주는 행동에서 애정을 더 잘 느낄 수 있어요.'},
 '상관':{'need':'이유를 묻고 방법을 바꿀 여지','gift':'불편한 규칙을 발견하고 새로운 방식으로 표현하는 힘','risk':'문제 지적이 상대에 대한 평가로 들리는 날카로운 말','work':'기획·개선·표현처럼 기존 방식의 문제를 고치는 업무','private':'틀에 맞추기보다 내 생각을 솔직히 나누고 싶은 마음','test':'방법의 문제를 말하다 상대의 능력이나 성격까지 평가하는지','money':'새로운 표현을 실제로 필요한 상품·서비스로 정리하는 과정','example':'데이트 방식이 마음에 들지 않을 때 개선안을 말했는데 상대는 자기 노력이 평가받았다고 느낄 수 있어요.'},
 '편재':{'need':'새로운 사람과 기회를 만날 여지','gift':'밖의 수요와 자원을 연결하는 감각','risk':'여러 기회를 잡느라 약속과 관리 범위를 넓히는 태도','work':'제휴·영업·유통처럼 외부 기회를 연결하는 업무','private':'함께 경험을 넓히고 관계에 활기를 주고 싶은 마음','test':'새로운 제안을 받아들이면서 기존 약속을 감당할 시간을 먼저 확인하는지','money':'기회의 범위와 거래마다 들어가는 시간·비용의 관리','example':'즉흥적인 나들이는 즐겁지만 일정이 자주 바뀌면 상대는 자기 시간이 뒷전이라고 느낄 수 있어요.'},
 '정재':{'need':'예측 가능한 조건과 꾸준한 결과','gift':'자원·일정·약속을 안정적으로 유지하는 감각','risk':'계획에서 벗어난 변화까지 손해로 받아들이는 경직된 관리','work':'운영·정산·일정처럼 결과를 지속시키는 업무','private':'말과 행동이 일치하고 생활 약속이 지켜지길 바라는 마음','test':'작은 계획 변경에서도 실제 손실보다 통제하지 못했다는 불편이 더 큰지','money':'반복 수입의 조건·고정 비용·유지 가능한 약속','example':'비싼 선물보다 정해둔 시간에 만나고 작은 약속을 계속 지키는 모습이 더 든든할 수 있어요.'},
 '편관':{'need':'어려운 요구를 해결할 기준과 권한','gift':'까다로운 과제를 맡아 결론을 내는 대응력','risk':'요구를 전부 떠안거나 가까운 사람에게도 엄격한 해결책을 요구하는 태도','work':'문제 대응·위험 관리처럼 판단과 책임이 필요한 업무','private':'어려운 순간에도 서로 책임져주길 바라는 마음','test':'도와주려는 말이 상대에게 반드시 따라야 할 지시로 들리는지','money':'수익보다 먼저 감당할 의무와 손실 범위를 정하는 과정','example':'상대가 고민을 털어놓으면 감정을 듣기 전에 해결책과 행동 기준부터 제시할 수 있어요.'},
 '정관':{'need':'합의한 기준과 일관된 신뢰','gift':'약속과 역할을 지키며 신뢰를 쌓는 힘','risk':'실수나 예외까지 원칙 위반으로 판단하는 엄격함','work':'검토·품질·공적 절차처럼 기준을 유지하는 업무','private':'관계의 약속과 서로 맡은 책임을 분명히 하고 싶은 마음','test':'둘이 합의한 약속과 내가 혼자 정한 기대를 구분하고 있는지','money':'규정·계약·책임을 지키며 결과를 유지하는 과정','example':'연락이나 만남의 약속이 어긋났을 때 이유를 듣기보다 약속을 지켰는지가 먼저 보일 수 있어요.'},
 '편인':{'need':'다른 관점으로 탐구할 시간','gift':'익숙한 답 밖에서 전문적인 관점을 찾는 힘','risk':'상대의 말에서 숨은 의도를 너무 오래 추측하는 태도','work':'특수 분야 조사·분석처럼 관점을 깊이 만드는 업무','private':'생각을 정리할 개인 시간과 깊이 있는 대화를 바라는 마음','test':'직접 물어볼 일을 머릿속 해석으로 대신하며 대답을 늦추는지','money':'전문 지식을 실제 고객의 필요와 연결하는 과정','example':'상대의 짧은 답장을 여러 뜻으로 해석하느라 정작 무엇을 뜻했는지 확인하는 대화가 늦어질 수 있어요.'},
 '정인':{'need':'이해할 설명과 안정적인 지원','gift':'배운 것을 정리하고 사람을 받쳐주는 힘','risk':'충분한 확신이나 도움이 생길 때까지 결정을 미루는 태도','work':'학습·자료 정리·교육처럼 이해의 바탕을 만드는 업무','private':'마음을 설명해주고 편안하게 도움을 주고받길 바라는 마음','test':'자료나 조언을 더 모으는 동안 내 선택을 계속 미루고 있는지','money':'배움에 들이는 비용과 이를 실제 결과로 옮기는 과정','example':'상대가 해결을 대신해주기보다 왜 그런지 차분히 설명해줄 때 더 안심할 수 있어요.'}
}

SEASON={
 '목':{'봄':'나무가 자라는 계절에 놓여 자기 방향을 키우는 상징이 계절과 이어져요. 성장의 의욕과 가지를 넓히는 힘을 함께 살피되, 전체 강약은 다른 글자까지 보아야 해요.', '여름':'나무가 불을 돕는 계절에 놓여, 자라는 힘을 밖으로 표현하고 결과를 만드는 데 쓰는 그림이에요. 많이 만들어내는 것과 그것을 받쳐줄 바탕이 충분한지는 별개라, 물의 역할도 함께 살펴요.', '가을':'나무를 다듬는 금의 계절에 놓여 자기 방향과 외부의 기준이 만나는 그림이에요. 하고 싶은 것을 정하는 힘만큼 요구에 맞춰 조정하는 과정이 중요한 조건입니다.', '겨울':'물의 계절에 놓인 나무는 도움을 받는 관계와 차가운 계절 조건을 함께 보아요. 바탕을 갖추는 것과 실제로 밖에 표현하는 것을 구분하고, 전체에서 따뜻함이 어떻게 이어지는지도 살펴요.'},
 '화':{'봄':'나무가 불을 돕는 계절이라 배움과 지원을 받아 표현하는 그림이에요. 관심을 얻는 힘과 준비의 바탕이 어떻게 연결되는지가 중요한 조건입니다.', '여름':'불의 계절에 불이 놓여 표현의 상징이 계절과 겹쳐요. 추진과 표현을 읽되, 열기를 더하는 글자만 있는지 정리하거나 조절하는 글자도 있는지를 함께 봐야 해요.', '가을':'불이 금을 다루는 계절이라 밖의 자원과 결과를 어떻게 감당하는지를 함께 읽어요. 눈에 띄는 표현력만으로 설명하기보다 실제 관리 조건이 중요해지는 그림입니다.', '겨울':'물을 만나는 불이라 자기 표현과 외부의 요구 사이를 함께 살펴요. 따뜻함을 유지할 바탕이 있는지에 따라 같은 불도 다른 조건으로 읽힙니다.'},
 '토':{'봄':'흙에 나무가 자라는 계절이라 맡은 책임과 자기 바탕을 함께 살피는 그림이에요. 안정감을 지키는 마음과 밖에서 요구하는 변화가 만나는 조건입니다.', '여름':'불이 흙을 돕는 계절이라 지원의 관계와 더운 계절 조건을 함께 읽어요. 버티는 힘을 살피되 건조함을 조절할 글자도 있는지 확인합니다.', '가을':'흙에서 금으로 이어지는 계절이라 가진 것을 밖의 작업과 표현으로 옮기는 그림이에요. 안정적인 토대가 실제 결과로 어떻게 쓰이는지가 중요합니다.', '겨울':'흙이 물을 다루는 계절이라 자원 관리와 차가운 조건을 함께 살펴요. 자원이 보인다는 사실과 그것을 감당할 토대가 있는지는 구분해야 해요.'},
 '금':{'봄':'금이 나무를 다루는 계절이라 기준을 세우는 힘이 바깥 자원과 만나는 그림이에요. 분명한 판단에 관리할 범위가 얼마나 이어지는지도 함께 살펴요.', '여름':'불이 금을 다듬는 계절이라 외부의 요구와 자기 기준이 만나는 조건이에요. 정확함의 장점과 요구를 감당하는 부담을 같이 읽어야 합니다.', '가을':'금의 계절에 금이 놓여 자기 기준의 상징이 계절과 이어져요. 결론을 내는 힘을 살피면서도 그 판단이 밖으로 전달되거나 유연해질 통로가 있는지 확인합니다.', '겨울':'금에서 물로 이어지는 계절이라 판단을 생각과 표현으로 옮기는 그림이에요. 차가운 계절 조건 속에서 그 표현을 받쳐주는 다른 글자도 함께 봅니다.'},
 '수':{'봄':'물에서 나무로 이어지는 계절이라 생각을 밖의 표현과 작업으로 옮기는 그림이에요. 넓게 이해하는 것과 실제로 만드는 것의 연결이 중요한 조건입니다.', '여름':'물이 불을 다루는 계절이라 생각의 폭과 바깥 성과를 감당하는 힘을 함께 보아요. 기회를 넓히는 이야기보다 그것을 받쳐줄 물의 바탕이 있는지 확인해야 해요.', '가을':'금이 물을 돕는 계절이라 판단의 자료와 지원을 받아 흐름을 넓히는 그림이에요. 정보를 받아들이는 바탕과 밖에 쓰는 통로를 함께 살펴요.', '겨울':'물의 계절에 물이 놓여 흐름과 생각의 상징이 계절과 겹쳐요. 생각의 폭을 넓히는 힘만큼 밖으로 표현하거나 따뜻하게 이어줄 글자가 있는지도 중요합니다.'}
}

PAIR={
 frozenset(['식상','재성']):('생각을 결과와 현실의 기회로 연결하는 구성','생각을 표현하고 만드는 역할과 현실의 수요·시간·비용을 다루는 역할이 함께 보여요. 떠올리는 일, 실제로 만드는 일, 누군가에게 필요한 결과로 전달하는 일이 연결되는 조합입니다. 예를 들어 새 서비스를 구상했다면 무엇을 만들지뿐 아니라 누가 왜 사용할지까지 함께 생각하는 모습으로 풀 수 있어요.'),
 frozenset(['관성','인성']):('요구를 이해하고 근거로 책임지는 구성','기준을 지키는 역할과 그 이유를 배우는 역할이 함께 보여요. 요구를 무조건 따르기보다 충분히 이해한 뒤 책임지는 모습으로 연결해 읽습니다. 예를 들어 검토를 맡을 때 기준이 왜 필요한지까지 정리하는 힘이 장점이고, 확인할 근거가 끝없이 늘면 판단이 늦어지는 것이 약점이 될 수 있어요.'),
 frozenset(['식상','관성']):('바꾸고 싶은 방법과 지켜야 할 기준이 만나는 구성','자기 방식으로 표현하는 역할과 약속·책임을 지키는 역할이 함께 보여요. 문제를 잘 찾아도 전달 방식이 상대를 평가하는 말로 들리면 장점이 갈등으로 바뀔 수 있어요. 예를 들어 회의에서 새 방법을 제안할 때 무엇을 바꾸고 무엇은 지킬지 함께 설명하는 과정이 중요해지는 조합입니다.'),
 frozenset(['비겁','재성']):('내 선택과 공동의 자원을 함께 조율하는 구성','자기 판단을 지키는 역할과 결과·자원을 다루는 역할이 함께 있어요. 혼자 선택할 수 있는 범위와 돈·일정을 함께 관리할 범위가 섞이면 불편이 생길 수 있습니다. 예를 들어 공동 작업에서 방향은 내가 잡더라도 비용과 보상까지 혼자 결정하면 상대에게는 공정함의 문제가 될 수 있어요.'),
 frozenset(['식상','인성']):('이해하는 시간과 밖에 보여주는 시간이 모두 필요한 구성','내용을 배우는 역할과 익힌 것을 표현하는 역할이 함께 보여요. 조사만 하거나 결과만 서두르는 한 가지 방식으로는 설명이 부족해요. 예를 들어 충분히 알아보고 싶은 마음과 작업을 완성해 반응을 확인하고 싶은 마음 사이에서 마감의 기준이 중요해지는 조합입니다.'),
 frozenset(['재성','관성']):('실제 성과와 맡은 책임을 함께 따지는 구성','자원·결과를 다루는 역할과 책임·기준을 지키는 역할이 함께 있어요. 결과만 남기면 되는 것이 아니라 어떤 절차와 약속으로 얻었는지도 중요하게 읽습니다. 예를 들어 좋은 기회라도 책임 범위가 불명확하면 선뜻 받아들이기 어려운 모습으로 연결할 수 있어요.'),
 frozenset(['비겁','식상']):('자기 생각을 직접 만들어 보여주는 구성','선택의 주도권과 표현의 역할이 함께 있어요. 남이 정한 방식에 맞추는 것보다 직접 정하고 결과로 보여주는 과정을 중요하게 읽습니다. 예를 들어 협업에서 내 방법을 끝까지 지키려는 마음이 커지면 다른 사람의 작업이 들어올 자리가 좁아질 수 있어요.'),
 frozenset(['비겁','관성']):('자율성과 외부의 기준을 함께 조율하는 구성','내 선택을 지키는 역할과 맡은 책임을 지키는 역할이 함께 있어요. 자율성이 없으면 답답하고, 기준이 없으면 무엇을 책임져야 할지 모호해지는 두 조건이 공존합니다. 예를 들어 역할은 명확하되 방법을 직접 정할 수 있는 자리에서 두 힘을 함께 쓰는 모습으로 읽어요.'),
 frozenset(['비겁','인성']):('자기 판단에 이해의 바탕을 더하는 구성','스스로 결정하는 역할과 배우고 지원받는 역할이 함께 보여요. 이해를 바탕으로 기준을 세우는 것이 장점이지만, 내가 충분히 알았다는 확신 때문에 다른 관점이 들어오기 어려울 수도 있어요. 예를 들어 설명은 깊어도 결론을 미리 정한 채 자료를 고르고 있지는 않은지 비교해볼 수 있습니다.'),
 frozenset(['재성','인성']):('충분히 이해하고 싶은 마음과 현실 조건을 함께 따지는 구성','배움의 바탕과 결과·비용을 다루는 역할이 함께 있어요. 시간을 들여 이해할 가치와 당장 유지해야 할 조건 사이의 조율이 중요합니다. 예를 들어 더 배우고 싶은 과정에 비용을 쓰면서 그것이 실제 작업에 언제 연결되는지도 동시에 따지는 모습으로 읽어요.')
}

def role_for(element,day_element):
    return list(GROUPS)[(CYCLE.index(element)-CYCLE.index(day_element))%5]

def polish_particles(text):
    phrases=sorted(set(GODS)|{v for god in GODS.values() for k,v in god.items() if k!='example'},key=len,reverse=True)
    for phrase in phrases:
        code=ord(phrase[-1])-0xAC00
        if not 0<=code<11172:continue
        final=code%28
        for consonant,vowel in [('이','가'),('을','를'),('과','와'),('은','는')]:
            wrong=vowel if final else consonant
            right=consonant if final else vowel
            text=text.replace(phrase+wrong+' ',phrase+right+' ')
        if final==0 or final==8:text=text.replace(phrase+'으로',phrase+'로')
        if final:text=text.replace(phrase+'예요',phrase+'이에요')
    # Hanja in parentheses does not change the Korean noun's final consonant.
    for god in GODS:
        has_final=(ord(god[-1])-0xAC00)%28!=0
        for consonant,vowel in [('이','가'),('을','를'),('과','와'),('은','는')]:
            wrong=vowel if has_final else consonant
            right=consonant if has_final else vowel
            text=re.sub(r'('+re.escape(god)+r'\([^)]*\))'+wrong+r'(?=\s)',lambda m:m[1]+right,text)
    return text

def location(row,part):
    return {'year':'년주','month':'월주','day':'일주','hour':'시주'}[row['position']]+(' 위 글자' if part=='stem' else ' 아래 글자')

def describe(row,part):
    v=row[part];god=v['ten_god']
    return f"{location(row,part)} {v['hanja']}({v['hangul']})의 {god}"

def context(report):
    rows={p['position']:p for p in report['pillars'] if p['known']}
    day=rows['day'];month=rows['month'];b=report['balance']
    outside=month['stem']['ten_god'];root=month['branch']['ten_god'];private=day['branch']['ten_god']
    a=GODS[root];o=GODS[outside];p=GODS[private]
    root_group=GROUP_OF[root];private_group=GROUP_OF[private]
    pair=PAIR.get(frozenset([root_group,private_group]))
    if pair is None:
        pair=(a['gift']+'과 '+p['need']+'이 함께 있는 구성',
              f"월지의 {root}와 일지의 {private}가 같은 역할 계열에 있어요. 밖에서 중요하게 여기는 기준이 가까운 관계에서도 이어지는 것으로 읽습니다. {a['gift']}이 장점이지만, 친밀함을 이유로 같은 기준을 상대에게도 요구하면 {p['risk']}로 보일 여지가 있어요.")
    # Work uses the two monthly roles. The private day-branch combination
    # belongs to relationship discussion and must not replace this evidence.
    work_pair=PAIR.get(frozenset([root_group,GROUP_OF[outside]]))
    work_text=(work_pair[1] if work_pair else
        f"일에서는 {root}의 {a['gift']}과 {outside}의 {o['gift']}이 같은 계열로 이어져요. {a['need']}과 {o['need']}이 함께 충족되는 업무인지 살펴볼 수 있어요.")
    if root_group=='식상' and GROUP_OF[outside]=='재성':
        work_title=('생각을 만들고, 새로운 기회로 연결하는 사람' if outside=='편재' else
                    '생각을 만들고, 오래 이어갈 결과로 다듬는 사람')
        work_feature=('아이디어와 표현을 실제 수요나 새로운 기회에 연결하는 쪽에 특징을 읽어요. 무엇을 만들지와 누가 필요로 할지를 함께 생각하는 흐름입니다.' if outside=='편재' else
                      '생각과 표현을 결과물로 옮기고, 일정과 비용 안에서 이어가는 쪽에 특징을 읽어요. 만드는 즐거움과 유지할 약속을 함께 살피는 흐름입니다.')
        work_risk=('아이디어를 더 내고 활동을 넓히는 동안, 이미 맡은 일의 마감과 시간·비용이 뒤로 밀리는 모습' if outside=='편재' else
                   '완성도를 더 높이고 싶은 마음과 약속한 일정·비용을 지키려는 마음이 부딪히는 모습')
    else:
        work_title=WORK_HEAD[root]+', '+o['gift']
        work_feature=f"{a['gift']}과 {o['gift']}을 함께 쓸 때의 모습을 읽어요."
        work_risk=a['risk']+'과 '+o['risk']
    placement=f"태어난 달의 아래 글자, 월지 {month['branch']['hanja']}({month['branch']['hangul']})는 {root}예요. 여기서는 {a['need']}을 중요한 일의 조건으로 읽어요. 같은 역할이 몇 개 있느냐보다, 계절을 읽는 자리에 무엇이 놓였는지를 먼저 본 설명입니다."
    outward=f"밖으로 드러난 월간은 {month['stem']['hanja']}({month['stem']['hangul']})의 {outside}예요. {o['gift']}으로 표현하는 쪽을 함께 읽어요. "+(
        '달의 위아래 글자가 같은 역할이어서 일하는 기준과 겉으로 표현하는 방향이 겹쳐요.' if root==outside else
        f"달의 아래쪽에서 중요하게 읽은 {a['need']}과, 밖으로 보여주는 {o['gift']}은 서로 다른 조건이에요. 그래서 겉으로 드러난 한 모습만으로 전체를 설명하기 어려워요.")
    inner=f"태어난 날의 아래 글자, 일지 {day['branch']['hanja']}({day['branch']['hangul']})는 {private}예요. 가까운 관계를 읽는 자리에서는 {p['private']}에 의미를 두어요. 이것은 배우자나 가족의 실제 성격을 계산한 결과가 아니라, 내 쪽의 관계 기준을 풀어쓴 부분입니다."
    season=SEASON[day['stem']['element']][report['month']['season']]
    seasonal=f"{day['reading']}({day['ganji']})의 기준은 {day['stem']['hanja']}({day['stem']['hangul']}) {day['stem']['element']}이고, {report['month']['hanja']}({report['month']['hangul']})는 {report['month']['season']}의 절기 월이에요. "+season
    if not b['available']:
        capacity='출생 시간이 없어 전체 강약과 용신은 확정하지 않았어요. 지금 읽은 배치에 시주의 역할이 더해지면 균형과 보완 방향은 달라질 수 있어요. 따라서 과다·부족을 확정해 사람이나 이름의 오행을 추천하지 않았습니다.'
    elif '약' in b['strength']:
        capacity=f"전체 계산은 {b['strength']}으로 분류돼요. 월지의 지지는 {'있고' if b['month_supports'] else '없고'}, 일지의 지지는 {'있어요' if b['day_supports'] else '없어요'}. 이는 의지나 능력이 약하다는 뜻이 아니라 일간을 받쳐주는 관계의 판정입니다. 이 해석에서는 {a['gift']}을 많이 쓰는 만큼 배움·도움·감당할 범위를 받쳐줄 조건도 중요한 것으로 연결해 읽어요."
    elif '강' in b['strength']:
        capacity=f"전체 계산은 {b['strength']}으로 분류돼요. 월지의 지지는 {'있고' if b['month_supports'] else '없고'}, 일지의 지지는 {'있어요' if b['day_supports'] else '없어요'}. 개인의 능력 점수가 아니라 일간을 받쳐주는 관계를 살핀 결과예요. 이 해석에서는 {a['gift']}에 자기 기준까지 강하게 더할 때, 상대의 방식이 들어올 여지도 함께 보는 쪽으로 읽습니다."
    else:
        capacity=f"전체 계산은 {b['strength']}으로 분류됐어요. 따라서 받쳐주는 힘이나 밖에 쓰는 힘 어느 한쪽만 과하다고 설명하지 않고, {a['need']}과 실제로 드러난 다른 역할의 연결을 함께 읽습니다."
    # A comparison is a changed condition, not an invented second person's chart.
    counter=f"같은 {day['stem']['hanja']}({day['stem']['hangul']}) 일간이라고 모두 이렇게 풀리지는 않아요. 이 명식은 {report['month']['season']}의 {root} 월지에 {private} 일지가 더해져, {a['need']}과 {p['private']}을 함께 읽었어요. 다른 계절이나 다른 일지라면 일의 조건과 친밀함의 기준도 달라집니다. 일간의 비유 하나가 같아도 이 조합까지 같다는 뜻은 아니에요."
    return dict(rows=rows,day=day,month=month,b=b,root=root,outside=outside,private=private,
                a=a,o=o,p=p,root_group=root_group,private_group=private_group,
                placement=placement,outward=outward,inner=inner,seasonal=seasonal,
                capacity=capacity,counter=counter,pair_title=WORK_HEAD[root]+', '+PRIVATE_HEAD[private],pair_text=pair[1],
                work_pair_text=work_text,work_title=work_title,work_feature=work_feature,work_risk=work_risk)

def elemental_details(report,c):
    counts={e['element']:e['count'] for e in report['elements']}
    dominant=[e for e,n in counts.items() if n==max(counts.values())]
    paras=[]
    for e in dominant:
        group=role_for(e,c['day']['stem']['element'])
        actual=[n for n in GROUPS[group] if any(g['name']==n for g in report['ten_gods'])]
        # The day stem itself is included in element counts, excluded from gods.
        paras.append(f"겉 글자에서 {e}는 {counts[e]}개로 가장 많이 보여요. 기준인 {c['day']['stem']['element']}에서 보면 {e}는 {group}의 관계예요. "+
            (f"실제 역할 표에서 확인한 관계는 {' · '.join(actual)}입니다. "+ROLE_VOICE[group]['core'] if actual else '이 분포에는 기준인 일간 자체도 포함되므로 같은 역할이 여러 자리 있다고 바꾸어 말하지는 않아요.')+
            ' 이 관계는 기준 오행이 달라지면 달라져요. 그래서 불이 많이 보인다는 사실만으로 모든 사람을 열정적인 성격이라고 정하지 않습니다.')
    return paras

def person_fit(report,c):
    b=c['b']
    if not b['available'] or not b.get('yong_element'):
        return f"지금 관계에서 우선 살펴볼 조건은 {c['p']['private']}이에요. {c['p']['example']} 전체 균형은 시간이 없어 확정하지 않았으므로, 어떤 오행이 많은 상대가 맞는지는 아직 고르지 않았어요."
    e=b['yong_element'];group=role_for(e,c['day']['stem']['element'])
    manner={
      '목':('서로의 가능성을 열어두고 과정을 함께 키우는','아이디어를 바로 닫지 않되 단계와 범위를 함께 정하는'),
      '화':('생각과 마음을 따뜻하고 분명하게 표현하는','혼자 추측하게 두기보다 좋아하는 점과 바라는 점을 직접 말하는'),
      '토':('생활의 약속과 역할을 안정적으로 지키는','즉흥적인 제안 뒤에도 일정과 맡은 일을 확인하는'),
      '금':('할 일과 하지 않을 일의 기준을 명확히 나누는','막연히 재촉하기보다 완료 기준과 책임 범위를 함께 정하는'),
      '수':('서두르기 전에 듣고 생각할 여백을 만드는','의견이 부딪힐 때 잠깐 멈춰 이유를 듣고 속도를 맞추는')}
    style,example=manner[e]
    partner_scope=('이곳은 개인 풀이이고, 입력한 상대와의 보완·마찰 비교는 ‘두 사람 궁합’에서 함께 볼 수 있어요.' if report.get('partner_comparison_available') else '여기서는 상대 명식을 아직 입력받지 않았습니다.')
    return f"이 명식의 보완 기준은 {e}({b['yong_method']})로 계산됐어요. 나의 {c['day']['stem']['element']}에 대해서는 {group}의 역할이며, 전통 상징을 관계의 말로 옮기면 {style} 태도를 참고할 수 있어요. 예를 들어 {example} 사람인지가 실제로 확인할 부분입니다. {e} 기운이 많은 상대를 보완 후보로 비교할 수는 있지만, 개수만 많은 사람과 반드시 잘 맞는다는 결론은 아니에요. 상대의 계절·강약·일지와 두 사람의 전체 배치를 함께 보아야 해요. "+partner_scope

def relation_detail(report,c):
    day_chars={c['day']['stem']['hanja'],c['day']['branch']['hanja']}
    selected=[r for r in report['relations'] if day_chars.intersection(set(r['members']))]
    if not selected:
        return f"기준인 일주와 직접 연결된 합·충·형·파·해는 이 관계표에서 검출되지 않았어요. 그래서 관계 갈등을 글자끼리의 충돌로 꾸며 설명하지 않고, {c['private']}에서 읽은 친밀함의 기준을 중심에 두었습니다."
    labels=' · '.join(dict.fromkeys(r['members']+' '+r['kind'] for r in selected))
    return f"일주 글자와 연결된 관계표에서 확인한 배치는 {labels}입니다. 합과 충돌 관계는 글자끼리의 연결을 기록한 것이며, 합이 사랑을 뜻하거나 충이 이별을 뜻하는 것은 아니에요. 여기서는 앞서 읽은 역할이 서로 연결되는 배치가 있다는 근거로만 사용하고, 합화가 성립해 오행이 바뀌었다거나 실제 관계의 결과가 정해졌다고 해석하지 않았습니다."
