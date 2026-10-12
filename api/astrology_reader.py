"""Everyday, role-specific zodiac readings of measured astronomical positions."""
from api.astrology_interpretation import SIGN_READINGS

SCENES={
 '양자리':('새로운 계획이 나오면 일단 작은 것부터 해보자고 말하는 장면','기다리는 동안 흥미가 떨어져 상대의 준비가 끝나기 전에 먼저 움직이는 모습'),
 '황소자리':('익숙한 방법으로 차근차근 결과를 쌓아가는 장면','이미 안정적으로 쓰던 방법이라는 이유로 새로운 제안을 오래 미루는 모습'),
 '쌍둥이자리':('한 가지 질문에서 여러 가능성을 찾아 대화로 연결하는 장면','흥미로운 이야기를 계속 더하다 처음 정할 일이 뒤로 밀리는 모습'),
 '게자리':('상대가 편안하게 느낄 환경과 익숙한 사람을 먼저 챙기는 장면','챙겨주려는 마음이 커져 상대가 스스로 할 몫까지 대신 맡는 모습'),
 '사자자리':('내가 만든 결과를 사람들에게 보여주고 반응을 나누는 장면','열심히 표현한 만큼 인정받지 못하면 대화의 중심을 다시 내 쪽으로 가져오는 모습'),
 '처녀자리':('막연한 문제를 작은 항목으로 나누어 하나씩 정리하는 장면','이미 충분한 결과인데도 작은 빈틈이 마음에 남아 수정을 계속하는 모습'),
 '천칭자리':('서로 다른 의견이 나오면 양쪽의 이유를 듣고 합의점을 찾는 장면','한쪽이 실망할까 봐 내 선택을 말하는 순간을 자꾸 늦추는 모습'),
 '전갈자리':('겉으로 나온 답 뒤에 어떤 이유와 마음이 있는지 더 깊이 묻는 장면','한 번 마음에 걸린 말을 오래 붙잡아 직접 확인할 대화가 늦어지는 모습'),
 '사수자리':('익숙한 범위를 벗어나 새 경험과 더 큰 가능성을 제안하는 장면','다음 경험이 더 흥미로워 이미 시작한 일을 끝내는 시간이 뒤로 밀리는 모습'),
 '염소자리':('무엇부터 해야 할지 순서를 정하고 약속한 결과를 끝까지 책임지는 장면','맡은 일이 많아져도 쉬거나 나눌 일을 뒤로 미루는 모습'),
 '물병자리':('다들 당연하게 여긴 방법에 다른 관점으로 질문을 던지는 장면','새 방법의 이유를 충분히 설명하지 않아 주변에는 갑자기 혼자 방향을 바꾼 것처럼 보이는 모습'),
 '물고기자리':('한 사람의 이야기에서 여러 감정과 가능성을 함께 상상하는 장면','상대의 마음을 헤아리다 내가 실제로 할 수 있는 범위를 넘어 약속하는 모습')}
ROLES={
 'Sun':('나답게 드러나는 모습','무엇을 할 때 나답다고 느끼는지','내 선택과 표현'),
 'Moon':('마음이 편해지는 순간','가까운 사람과 쉴 때 어떤 방식을 편하게 느끼는지','익숙한 분위기와 돌봄'),
 'Mercury':('말하고 생각하는 방식','새 정보를 이해하고 의견을 전하는 방식','대화와 판단'),
 'Venus':('사랑과 취향에서 마음이 가는 것','무엇에 끌리고 어떤 배려를 좋아하는지','좋아하는 것과 관계'),
 'Mars':('시작하고 끝까지 움직이는 힘','일을 시작하고 뜻이 다를 때 움직이는 방식','행동과 추진')}


def build_readings(astrology):
    rows={p['key']:p for p in astrology['positions']};chapters=[]
    for key,(title,role,subject) in ROLES.items():
        p=rows.get(key)
        if not p:
            chapters.append({'topic':key.lower(),'title':'달 · 태어난 시간을 알면 더 풀 수 있어요',
                'paragraphs':['달은 가까운 사이에서 느끼는 익숙함과 편안함을 읽는 항목이에요. 태어난 시간을 몰라 정확한 위치를 정하지 않았습니다. 다른 사람의 달이나 그날 정오의 달을 대신 넣지는 않았어요.'],
                'source_ids':['stars-time']})
            continue
        if not p['sign_confirmed']:
            chapters.append({'topic':key.lower(),'title':p['label']+' · 이날은 별자리 경계를 지나가요',
                'paragraphs':[f"정확한 시간에 따라 {' 또는 '.join(p.get('possible_signs',[]))}로 달라질 수 있어요. {role}을 한 방향으로 정해 설명하지 않고, 태어난 시간을 알 때 다시 계산할 수 있도록 남겨두었습니다."],
                'source_ids':['stars-time']})
            continue
        direction,caution=SIGN_READINGS[p['sign']];example,risk=SCENES[p['sign']]
        paragraphs=[f"{p['label']}은 {p['sign']}에 있어요. 이 항목에서는 {role}을 읽습니다. {p['sign']}의 뜻을 쉽게 풀면 {direction}이에요. 같은 별자리라도 어느 천체에 놓였느냐에 따라 나를 표현하는 모습인지, 편안한 관계의 기준인지가 달라져요.",
            f"생활에서는 {example}을 떠올릴 수 있어요. {subject}에서 이런 방식이 잘 쓰이면 익숙한 상황을 내 방식으로 이해하고 움직이는 힘이 됩니다. 이미 그런 일이 있었다는 뜻이 아니라, 내 경험과 비교할 장면이에요.",
            f"솔직하게 짚을 약점은 {risk}이에요. 장점이 사라진 것이 아니라 원래의 방식이 너무 커졌을 때의 모습입니다. 예를 들어 내가 충분히 생각했거나 충분히 표현했다고 느껴도, 상대가 이해한 내용과 속도까지 같지는 않을 수 있어요.",
            f"이 항목에서 확인할 질문은 ‘{caution}’예요. 나를 좋은 말 하나로 묶기보다, 편하게 잘하는 순간과 상대에게 부담으로 넘어가는 순간을 함께 비교하면 뜻이 더 분명해집니다."]
        if key=='Venus':paragraphs[1]=f"좋아하는 마음은 {example}처럼 전해질 수 있어요. 내가 편한 방식으로 챙겨준 것과 상대가 원하는 배려를 받은 것은 다를 수 있습니다. 선물, 연락, 함께 보내는 시간 중 어느 쪽에서 마음을 더 잘 느끼는지는 실제 대화와 함께 비교할 부분이에요."
        if key=='Mercury':paragraphs[1]=f"대화의 예로는 {example}을 떠올릴 수 있어요. 같은 고민을 듣더라도 핵심을 빨리 정하려는 사람과 여러 가능성을 같이 풀고 싶은 사람은 대답하는 속도가 달라질 수 있습니다. 내 말이 맞는지뿐 아니라 상대가 지금 무엇을 묻고 있는지도 소통의 중요한 차이예요."
        if key=='Moon':paragraphs[1]=f"가까운 사람 앞에서는 {example}처럼 편안함을 찾는 모습을 읽어요. 밖에서 잘해내는 사람도 집에서는 다른 방식의 배려를 바랄 수 있습니다. 곧바로 해결해주는 도움보다 먼저 이야기를 들어주는 태도가 필요한지처럼, 편안함의 기준을 구분해볼 수 있어요."
        chapters.append({'topic':key.lower(),'title':p['label']+' '+p['sign']+' · '+title,'paragraphs':paragraphs,
                         'basis':f"{p['label']} {p['sign']} {p['degree_in_sign']}° · {p['reference']}",
                         'source_ids':['stars-symbols','profile-interpretation-rules']})
    sun,moon=rows['Sun'],rows.get('Moon')
    if sun['sign_confirmed'] and moon:
        same=sun['sign']==moon['sign'];sa=SIGN_READINGS[sun['sign']][0];ma=SIGN_READINGS[moon['sign']][0]
        chapters.append({'topic':'inside_outside','title':'보이는 모습과 속마음이 '+('같은 방향을 향해요' if same else '서로 다를 수 있어요'),
            'paragraphs':[f"밖으로 드러내는 모습은 {sun['sign']}의 {sa}, 편안함을 찾는 방식은 {moon['sign']}의 {ma}으로 나누어 읽어요. "+('같은 별자리여서 두 기준이 이어지는 조합입니다.' if same else '두 천체의 별자리가 달라 한 가지 첫인상만으로 마음속 기준까지 설명하기 어려운 조합이에요.'),
                f"예를 들어 밖에서는 {SCENES[sun['sign']][0]}을 잘해도, 가까운 사람에게 바라는 것은 {SCENES[moon['sign']][0]}에 더 가까울 수 있어요. 남이 보기엔 충분히 능숙한데 본인은 편하지 않은 순간을 이 두 관점으로 나누어 볼 수 있습니다.",
                '같은 방향이라도 편안함과 표현은 서로 다른 항목이에요. 다른 방향이라도 모순된 사람이라는 뜻은 아닙니다. 내가 잘해내는 모습과 마음을 놓는 조건이 각각 있다는 이야기로 이해할 수 있어요.'],
            'source_ids':['stars-symbols','profile-interpretation-rules']})
    personal={p['label'] for key,p in rows.items() if key in ROLES}
    aspects=[a for a in astrology['aspects'] if a['left'] in personal and a['right'] in personal][:3]
    role_by_label={rows[key]['label']:v[2] for key,v in ROLES.items() if key in rows}
    if aspects:
        paragraphs=[]
        for a in aspects:
            left,right=role_by_label[a['left']],role_by_label[a['right']]
            if a['angle'] in [90,180]:text=f"{a['left']}과 {a['right']}의 위치에서는 {left}와 {right} 사이의 다른 요구를 함께 살피는 관계가 보여요. 한쪽에서 좋다고 느낀 방식이 다른 쪽에서는 편하지 않을 수 있는 조건으로 읽습니다. 예를 들어 마음에 드는 선택과 실제로 움직일 때 필요한 조건이 다른 순간처럼, 두 요구를 함께 생각할 장면이에요."
            elif a['angle']==0:text=f"{a['left']}과 {a['right']}은 가까운 위치에 있어, {left}와 {right}을 함께 묶어 읽어요. 한 가지 마음이 다른 행동에도 이어지기 좋은 반면, 둘을 따로 생각해야 할 순간에도 익숙한 방식만 쓰지는 않는지가 주의점입니다."
            else:text=f"{a['left']}과 {a['right']}에서는 {left}와 {right}을 연결해서 읽는 각도가 보여요. 한쪽의 강점이 다른 쪽에서도 자연스럽게 쓰일 조건으로 풉니다. 다만 생활의 모든 상황이 편하다는 뜻이 아니라, 두 방식이 함께 쓰이는 장면을 살펴보는 항목이에요."
            paragraphs.append(text)
        chapters.append({'topic':'aspects','title':'마음과 행동이 만나는 곳, 혹은 엇갈리는 곳','paragraphs':paragraphs,
                         'source_ids':['stars-aspects','profile-interpretation-rules']})
    elif not astrology['hour_known']:
        chapters.append({'topic':'aspects','title':'천체 사이의 관계는 시간을 알 때 비교해요','paragraphs':['태어난 시간이 없어 달과 천체 사이의 각도 해설은 생략했어요. 정오의 위치를 실제 출생 시각으로 바꿔 쓰지 않도록, 확인할 수 있는 별자리의 설명부터 제공합니다.'],'source_ids':['stars-time']})
    else:
        chapters.append({'topic':'aspects','title':'개인적인 다섯 천체 사이에서 뚜렷한 각도는 확인하지 못했어요','paragraphs':['현재 허용 범위 안에서 태양·달·수성·금성·화성 사이의 주요 각도는 검출하지 못했어요. 다른 천체 사이의 각도는 계산표에서 볼 수 있고, 관계가 편하거나 어렵다는 판단을 빈칸에서 만들어내지는 않았습니다.'],'source_ids':['stars-aspects']})
    return chapters
