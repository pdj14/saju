"""Authored everyday explanations of actual roles; calculation labels stay in evidence."""
from api.chart_context import context, GODS, GROUP_OF, role_for, polish_particles
from api.reading_voice import STEM_VOICE, ROLE_VOICE
from api.reading_scenes import scene

ELEMENT = {'목':'나무', '화':'불', '토':'흙', '금':'금속', '수':'물'}
HEAD = {
 '비견':'남이 정한 길보다, 내가 납득한 길에 힘이 붙어요',
 '겁재':'함께 달릴 때 힘이 나지만, 내 몫도 중요해요',
 '식신':'머릿속 생각을 내 손으로 만들어야 즐거워요',
 '상관':'그냥 따르기보다, 더 나은 방법을 찾는 사람이에요',
 '편재':'새로운 사람과 기회를 연결하는 데 눈이 가요',
 '정재':'좋은 시작만큼, 오래 이어가는 실력이 중요해요',
 '편관':'어려운 일을 만나면, 해결할 방법부터 찾는 사람이에요',
 '정관':'작은 약속을 지키며 큰 신뢰를 쌓는 사람이에요',
 '편인':'남들이 지나친 질문을 오래 들여다보는 사람이에요',
 '정인':'충분히 이해하고 나면, 든든하게 움직이는 사람이에요'}
PRIVATE = {
 '비견':'가까워도 내 선택은 존중받고 싶어요', '겁재':'같은 편이라는 말에 공정한 행동이 따라야 해요',
 '식신':'큰 약속보다 작은 다정함에 마음이 가요', '상관':'좋은 말만 하는 사이보다 솔직한 사이가 좋아요',
 '편재':'함께 새로운 경험을 할 때 가까워져요', '정재':'설렘 뒤에도 달라지지 않는 태도가 좋아요',
 '편관':'힘들 때 함께 해결해주는 사람이 든든해요', '정관':'관계의 약속이 분명해야 안심할 수 있어요',
 '편인':'혼자 생각할 시간도 사랑의 일부예요', '정인':'내 마음을 이해해주는 설명에 안심해요'}
MONEY = {
 '비견':'돈을 함께 써도, 내가 결정할 몫은 남아 있어야 해요',
 '겁재':'함께 벌 때보다, 함께 나눌 때 기준이 중요해요',
 '식신':'잘 만든 결과와 잘 남긴 수입은 다른 이야기예요',
 '상관':'반짝이는 아이디어에 가격과 마감이 붙을 때',
 '편재':'기회가 늘어날수록, 남는 돈도 함께 봐야 해요',
 '정재':'꾸준히 들어오는 돈보다, 꾸준히 남기는 힘',
 '편관':'큰 수입을 기대하기 전에, 큰 책임을 확인해요',
 '정관':'약속과 신뢰가 오래 가는 수입의 바탕이에요',
 '편인':'깊은 지식을 누군가에게 필요한 가치로 바꾸려면',
 '정인':'배운 만큼, 실제로 쓰이는 결과가 중요해요'}
# These are modern relationship examples, not evidence of energy transfer.
MANNER = {
 '목':('가능성을 함께 키우는 태도','새 아이디어를 듣고 바로 안 된다고 하기보다, 작게 시작할 방법을 같이 찾는 사람'),
 '화':('마음을 분명하게 표현하는 태도','고마운 점이나 서운한 점을 상대가 알아맞히길 기다리지 않고 말해주는 사람'),
 '토':('약속과 생활을 안정적으로 받치는 태도','즐거운 계획 뒤에도 시간과 각자의 할 일을 함께 확인하는 사람'),
 '금':('선을 분명하게 정하는 태도','무조건 더 하라고 재촉하기보다 어디까지 하면 충분한지 함께 정하는 사람'),
 '수':('듣고 생각할 여유를 주는 태도','의견이 다를 때 바로 결론을 밀어붙이지 않고 이유를 끝까지 들어주는 사람')}


def work_story(c):
    root, outside = c['root'], c['outside']
    if c['root_group'] == '식상' and GROUP_OF[outside] == '재성':
        return c['work_pair_text']
    if root == outside:
        return f"일할 때 중요하게 여기는 것과 남에게 보여주는 방식이 같은 방향이에요. {scene(root,'work')} 스스로 집중하기 좋은 조건은 분명하지만, 익숙한 방법만 정답으로 두면 다른 사람이 끼어들 공간이 좁아질 수 있습니다."
    return f"먼저 {c['a']['need']}이 있어야 몰입하기 좋아요. 여기에 {c['o']['gift']}이 더해집니다. {scene(outside,'work')} 한 가지 일만 잘한다는 설명보다, 이 두 모습을 함께 쓸 수 있는 환경이 이 사주의 특징을 더 잘 보여줘요."


def capacity(c):
    b = c['b']
    if not b['available']:
        return '태어난 시간을 아직 몰라, 일을 얼마나 넓혀도 괜찮을지 판단하는 전체 균형은 남겨두었어요. 지금은 확인한 일하는 방식부터 읽으며, 시간까지 들어오면 부담을 받쳐줄 조건의 설명이 달라질 수 있습니다.'
    if '약' in b['strength']:
        return f"이 사주는 밖으로 힘을 쓰는 만큼 준비와 도움을 챙기는 쪽에 무게를 두어요. {c['a']['gift']}을 발휘하는 일이 많아질수록 시간과 책임까지 같이 늘어나는지를 봐야 합니다. 일을 못한다는 뜻이 아니라, 잘할 수 있다는 이유만으로 모두 맡으면 무리가 생기기 쉬운 조건이라는 뜻이에요."
    if '강' in b['strength']:
        return f"내 기준을 지키는 바탕이 강하게 계산된 사주예요. {c['a']['gift']}을 밀고 나가는 데 도움이 되는 한편, 내 방법이 익숙하다는 이유로 다른 선택까지 막지는 않는지가 중요합니다. 혼자 잘해내는 것과 함께 잘해내는 것은 서로 다른 힘이에요."
    return f"나를 받쳐주는 힘과 밖에 쓰는 힘 중 한쪽만 과하다고 읽지는 않아요. {c['a']['need']}을 유지하면서 {c['o']['gift']}도 쓸 수 있는지가 관건입니다. 일이 잘된다는 이유로 모든 역할을 넓히기보다, 지금 잘하는 방식이 계속 이어질 조건까지 보는 풀이예요."


def partner_story(report,c):
    b=c['b'];p=c['p']
    if not b['available'] or not b.get('yong_element'):
        return f"편안한 상대를 찾는 기준은 우선 {p['private']}이에요. 태어난 시간을 몰라 어떤 기운이 많은 상대와 균형을 이룰지는 아직 고르지 않았어요. 먼저 {p['example']} 같은 행동을 실제로 주고받을 수 있는지를 비교할 수 있습니다."
    e=b['yong_element'];style,example=MANNER[e]
    scope=('상대와 함께 입력한 비교는 ‘두 사람 궁합’에서 볼 수 있어요.' if report.get('partner_comparison_available') else '상대의 출생 정보는 아직 입력받지 않아, 실제 두 사람이 맞는지는 여기서 정하지 않았어요.')
    return f"전체 균형을 살핀 계산에서는 {ELEMENT[e]}의 기운을 도움이 되는 방향으로 골랐어요. 관계의 말로 풀어보면 {style}를 떠올릴 수 있습니다. 예를 들어 {example}인지가 생활에서 비교할 장면이에요. 이는 전통 상징을 이해하기 쉽게 옮긴 예시이고, 그 기운이 많은 사람의 실제 성격을 알아낸 결과는 아닙니다. "+scope


def build_readable_chapters(report):
    c=context(report);a,o,p=c['a'],c['o'],c['p'];root,outside,private=c['root'],c['outside'],c['private'];b=c['b']
    symbol,_,core,social,shadow,base_example=STEM_VOICE[c['day']['stem']['hangul']]
    name=report['profile']['name'];address=name+'님' if name!='나' else '당신'
    chapters=[]
    def add(topic,title,paras,focus,ids,rule):
        paras=[polish_particles(x) for x in paras]
        chapters.append({'topic':topic,'title':polish_particles(title),'paragraphs':paras,'body':'\n\n'.join(paras),
                         'focus':polish_particles(focus),'reflection':polish_particles(focus),'evidence_ids':ids,
                         'rule_ids':[rule],'source_ids':['saju-interpretation-rules','saju-classical-framework']})
    overview_title=c['work_title'] if c['root_group']=='식상' and GROUP_OF[outside]=='재성' else HEAD[root]
    add('overview',overview_title,[
        f"{address}의 특징을 한마디로 잡으면, {a['gift']}이 눈에 들어와요. 여기에 {o['gift']}도 함께 있습니다. 사람을 만날 때의 분위기만 보는 것보다 무엇을 맡았을 때 몰입하는지 보면 이 두 모습이 더 분명해져요.",
        f"사주에서는 {address}의 중심을 {symbol}에 비유해요. {core} 이 비유에 태어난 {report['month']['season']}의 계절과 일하는 자리의 구성을 더해서 읽었습니다. 같은 비유를 가진 사람이라도 모든 성격이 같지는 않아요.",
        scene(root),
        f"가까운 사이에서는 다른 마음이 드러나요. {p['example']} 밖에서 일을 잘 해내는 모습과, 사랑받았다고 느끼는 순간을 따로 보면 이해하기 쉬워요. 내게 중요한 것은 {p['private']}입니다.",
        f"좋은 쪽으로 쓰이면 {a['gift']}이 장점이 되지만, 과하면 {c['work_risk']}이 약점이 될 수 있어요. 특히 일을 할 때는 {a['need']}, 관계에서는 {p['need']}이 있다는 차이가 이 풀이의 중심이에요."],
        a['gift']+'과 '+p['private']+'을 함께 읽어요.',['daymaster','month','ten_gods','balance'],'position-aware-overview')
    if not b['available']:chapters[-1]['paragraphs'].append('출생 시간이 없어, 사주 전체의 균형은 확정하지 않았어요. 시간에 따라 달라질 수 있는 설명은 남겨두었습니다.')
    chapters[-1]['lead']=c['work_feature']
    chapters[-1]['differences']=[{'label':'일에서 힘이 나는 조건','text':a['need'],'basis':''},
        {'label':'가까운 사이에서 바라는 것','text':p['private'],'basis':''},
        {'label':'과하면 약점이 되는 순간','text':c['work_risk'],'basis':''}]
    add('disposition',PRIVATE[private],[
        f"밖에서 보이는 모습과 마음이 편해지는 조건 사이에 차이가 있어요. 일에서는 {a['gift']}이 먼저 보이지만, 가까운 사이에서는 {p['private']}이 중요합니다. 남에게 능숙해 보인다고 해서 모든 상황에서 같은 방식으로 움직이는 사람은 아니라는 이야기예요.",
        scene(private),
        f"그 차이는 작은 순간에 나타날 수 있어요. {p['example']} 상대는 나름대로 잘 챙겼다고 생각하는데 내 마음은 덜 채워질 수 있습니다. 무엇을 해줬는지보다, 내가 기대한 방식으로 전해졌는지가 다른 셈이에요.",
        f"반대로 일을 할 때는 {a['need']}이 있느냐가 더 중요해요. {scene(root,'work')} 평소에는 편한 사람이어도 일하는 방식을 세세하게 대신 정해주면 불편해질 수 있는 이유를 여기서 살펴볼 수 있어요.",
        f"기질의 약점은 {p['risk']}으로 읽어요. 혼자 느끼는 마음과 상대에게 전한 말을 구분하면, 왜 좋은 의도가 다르게 받아들여지는지 이해하기 쉬워집니다."],p['private'],['daymaster','month','ten_gods'],'month-day-context')
    hour=c['rows'].get('hour')
    add('charm',f"{a['gift']}, 그래서 함께하면 든든해요",[
        f"{address}의 매력은 큰 말로 자신을 보여주는 것보다 {a['gift']}이 필요한 순간에 드러나요. {scene(root,'friends')} 같이 일을 하거나 약속을 정해보면, 첫인상만으로 보이지 않던 강점이 더 또렷해질 수 있어요.",
        f"여기에 {o['gift']}도 더해져요. {scene(outside,'work')} 내 장점 하나만 앞세우기보다 두 힘이 연결될 때, 내가 잘하는 것을 다른 사람이 받아들이기 좋은 형태로 전달할 수 있습니다.",
        (f"태어난 시간까지 살피면 {GODS[hour['stem']['ten_god']]['gift']}도 함께 읽어요. "+scene(hour['stem']['ten_god']) if hour else '태어난 시간은 아직 모르는 상태예요. 더 보탤 수 있는 특징은 남겨두고, 지금 확인한 일하는 방식과 관계의 모습을 중심으로 매력을 풀었습니다.'),
        f"다만 매력이 오래 가려면 {a['need']}이 존중되는 환경이어야 해요. 그 조건이 계속 빠진 채 결과만 요구받으면, 원래의 장점이 {a['risk']}으로 보일 수 있습니다. 잘하는 모습을 더 크게 만드는 것보다, 자연스럽게 잘할 수 있는 자리가 맞는지도 중요해요."],a['gift'],['month','ten_gods','daymaster'],'position-specific-gifts')
    add('shadow','솔직히 말하면, 잘하려는 마음이 발목을 잡을 때',[
        f"일에서 먼저 짚을 약점은 {c['work_risk']}이에요. 처음에는 잘해보려는 마음에서 시작하지만, 그 마음이 너무 커지면 같이 일하는 사람의 시간과 기대가 뒤로 밀릴 수 있어요. {scene(root,'work')}",
        f"가까운 사람 앞에서는 {p['risk']}을 조심할 부분으로 읽어요. {p['example']} 본인은 도움이나 배려라고 생각해도 상대가 실제로 받은 느낌은 다를 수 있습니다. 이때 의도가 좋았다는 설명만 되풀이하면 서운했던 지점은 남아요.",
        capacity(c),
        f"이 약점이 맞는지 확인할 장면은 구체적이에요. 일을 할 때는 ‘{a['test']}’, 가까운 사이에서는 ‘{p['test']}’를 떠올릴 수 있어요. 잘 맞는 대목이 있다면 장점을 없애야 한다는 뜻보다, 장점이 상대에게 부담으로 넘어가는 선을 찾는 이야기입니다."],c['work_risk'],['month','daymaster','ten_gods','balance'],'conditional-specific-shadow')
    add('work',HEAD[root],[
        scene(root,'work'),
        f"구체적으로는 {a['work']}에서 이런 강점을 살펴볼 수 있어요. 직업 이름 하나보다 실제로 맡을 일이 중요합니다. 같은 회사의 같은 직함이라도 내 판단을 쓸 수 있는지, 내가 만든 결과를 보여줄 수 있는지에 따라 몰입의 조건은 달라질 수 있어요.",
        work_story(c),
        f"잘 맞지 않는 업무 조건도 있어요. {a['need']}이 계속 빠지고, {o['need']}마저 기대하기 어려운 자리라면 장점을 쓰기보다 버티는 데 힘이 들어갈 수 있습니다. 그때 {c['work_risk']}이 나타나는지가 구체적인 주의점이에요.",
        f"새 일을 고른다고 생각하면 이해하기 쉬워요. ‘이 직업이 멋있나’보다 ‘내가 어떤 결과를 만들고, 무엇을 결정하고, 누구에게 도움을 받을 수 있나’가 더 직접적인 질문이에요. {capacity(c)}"],a['need']+'이 실제 업무에 있는지가 중요해요.',['month','ten_gods','balance'],'position-aware-work')
    officers=list(dict.fromkeys(row[part]['ten_god'] for row in c['rows'].values() for part in ['stem','branch'] if GROUP_OF.get(row[part]['ten_god'])=='관성'))
    add('career','일을 잘하는 것과, 책임을 잘 맡는 것은 달라요',[
        f"{address}이 가진 재능이 조직 안에서 인정받으려면, 잘 만든 결과를 어떤 기준으로 평가하는지도 중요해요. 맡은 일을 잘하는 능력과 사람·일정·결정에 책임지는 자리는 다른 문제입니다. 스스로 만족한 결과가 상사나 동료에게도 충분한지 설명하는 과정이 필요할 수 있어요.",
        ('이 사주에서 책임을 읽는 특징은 '+' '.join(GODS[g]['gift']+'입니다. '+scene(g,'work') for g in officers) if officers else f"확인한 글자에서는 책임과 규칙을 직접 읽는 항목이 겉에 나타나지 않았어요. 조직생활을 못한다는 뜻은 아니에요. 우선 {a['gift']}을 다른 사람이 확인할 수 있는 결과로 전달하는 쪽부터 읽습니다."),
        f"더 큰 역할을 맡을 때의 주의점은 {c['work_risk']}이에요. 새 프로젝트를 잘해보고 싶어 맡았는데 승인권은 없고 모든 일정만 책임지게 되면, 재능을 펼치는 자리와 부담을 떠안는 자리가 달라질 수 있습니다. 책임의 크기만큼 권한도 함께 있는지가 중요한 차이예요.",
        f"평가를 받는 자리에서는 {o['gift']}이 어떻게 드러나는지도 살펴요. ‘열심히 했다’는 설명과 ‘무엇이 달라졌는지 보여준다’는 설명은 다를 수 있어요. 맡은 범위, 마친 결과, 아직 필요한 도움을 구분할 수 있어야 능력이 결과로 전달됩니다.",
        '승진 여부나 시험 합격을 정해놓은 풀이가 아니라, 조직의 기준을 만났을 때 힘을 쓰는 방식이에요. 시기에 따른 변화는 아래의 나이대별 흐름에서 따로 읽을 수 있습니다.'],o['gift']+'이 평가받는 방식까지 함께 보아요.',['month','ten_gods','balance'],'observed-officer-roles')
    visible={g['name'] for g in report['ten_gods']}
    finance=('새로운 수요와 거래를 발견하는 모습' if '편재' in visible else '')
    if '정재' in visible:finance+=('과 ' if finance else '')+'수입·비용·약속을 꾸준히 유지하는 모습'
    add('money',MONEY[root],[
        f"{address}의 돈 이야기는 {a['money']}에서 출발해요. "+(f"사주에서 돈을 직접 읽는 특징으로는 {finance}이 보입니다. " if finance else '겉에 보이는 글자에는 돈을 직접 읽는 항목이 나타나지 않았어요. 수입이 없다는 뜻보다, 내가 가진 능력이 어떤 과정을 거쳐 돈으로 이어지는지 먼저 봅니다. ')+ '많이 벌 수 있다는 말만으로는 부족하고, 들이는 시간과 비용 뒤에 무엇이 남는지도 함께 보는 항목이에요.',
        f"수입으로 연결되는 힘은 {a['gift']}이에요. {scene(root,'work')} 잘하는 일을 누군가에게 필요한 결과로 건넬 때 가치를 만들 수 있습니다. 다만 내가 좋아하는 결과와 상대가 돈을 내고 원하는 결과가 같은지는 별도로 확인할 지점이에요.",
        work_story(c)+f" 돈에서는 여기에 {o['money']}이라는 조건이 붙어요. 같은 일을 맡아도 준비와 수정에 쓰는 시간이 길어지면, 약속한 금액은 같아도 남는 결과는 달라집니다.",
        f"손실을 조심할 지점은 {c['work_risk']}이에요. 예를 들어 새 일을 하나 더 맡으며 들어올 돈만 세면, 기존 일을 늦춰 생기는 비용이나 더 필요한 도움을 놓칠 수 있습니다. 좋은 기회를 알아보는 것과 그 기회를 끝까지 유지하는 것은 다른 판단이에요.",
        f"{capacity(c)} 이 풀이에서 재물복은 큰돈을 반드시 얻는다는 약속보다, 내 강점이 수입으로 연결되는 조건과 돈이 새기 쉬운 습관을 살피는 이야기입니다."],a['money'],['ten_gods','month','balance'],'position-aware-resource-context')
    add('relationships',PRIVATE[private],[
        f"{address}의 애정운을 쉽게 풀면, {p['private']}이 먼저 나와요. 누구에게나 통하는 화려한 표현보다, 내가 마음을 놓는 방식으로 전해지는 애정이 중요합니다. 사람을 좋아하는 마음과 그 사람이 나를 좋아한다고 느끼는 순간은 서로 다를 수 있어요.",
        p['example']+' '+scene(private),
        f"갈등이 생기기 쉬운 지점은 {p['risk']}이에요. ‘{p['test']}’를 떠올리면 차이가 보일 수 있습니다. 상대를 아끼는 마음이 있어도 그 마음을 내가 익숙한 방식으로만 전하면, 상대는 이해받지 못했다고 느낄 여지가 있어요.",
        partner_story(report,c),
        f"일에서 보이는 {a['gift']}을 연애의 답으로 그대로 가져오지는 않아요. 일을 해결해준 것과 마음을 알아준 것은 다른 경험일 수 있기 때문이에요. 서로 원하는 표현이 {p['need']}과 만나는지 살피는 것이 실제 관계를 이해하는 더 가까운 기준입니다."],p['private'],['daymaster','month','ten_gods','balance','relations'],'day-branch-relational-context')
    add('family','가족이라서, 말하지 않아도 알아줬으면 하는 마음',[
        scene(private,'family'),
        f"{address}이 가까운 사이에서 바라는 것은 {p['private']}이에요. 밖에서는 {a['gift']}으로 문제를 해결하더라도, 집에서는 내가 잘해냈다는 평가보다 다른 말을 기다릴 수 있어요. 일에서 능숙한 사람이 가족 앞에서도 늘 해결사 역할을 원한다고 보기는 어렵습니다.",
        f"예를 들어 가족이 내 일을 걱정하며 조언할 때, 내가 원하는 것이 방법인지, 내 선택을 믿어주는 말인지에 따라 같은 조언도 다르게 들려요. {p['example']} 가족에게도 이런 표현의 차이가 있을 수 있습니다.",
        f"주의할 모습은 {p['risk']}이에요. 가까운 사이라는 이유로 기대를 말하지 않거나 내 기준을 대신 정해주면 서로 서운해질 수 있어요. 누가 더 사랑하는지를 따지기보다, {p['need']}이 실제 대화에 남아 있는지가 더 구체적인 확인 지점입니다.",
        '이 항목은 내가 가족 사이에서 바랄 수 있는 태도를 읽었어요. 부모님의 실제 성격, 어린 시절의 경제 상황, 자녀가 어떤 삶을 살지는 이 출생 정보만으로 알아낸 내용이 아닙니다.'],p['need']+'이 가족 사이에서도 중요해요.',['daymaster','month','ten_gods'],'family-own-role-context')
    add('friends','같이 일하기 좋은 친구와, 속마음을 나눌 친구',[
        scene(root,'friends'),
        f"함께 뭔가를 할 때는 {a['need']}을 존중하는 사람이 편해요. {scene(root,'work')} 내 판단과 기여가 받아들여지는 관계라면 일을 같이하면서 신뢰가 쌓일 수 있습니다.",
        f"마음이 가까워질수록 {p['need']}도 중요해져요. {scene(private,'friends')} 같은 취미를 가졌다는 사실만큼, 서로 어떤 말을 듣고 싶어 하는지도 우정의 깊이에 영향을 줄 수 있어요.",
        f"반대로 {a['need']}을 계속 무시하거나 {p['risk']}을 자극하는 관계에서는 오래 편하기 어려울 수 있어요. 예를 들어 좋은 뜻이라며 내 선택을 계속 대신 정하거나, 내가 중요하게 여기는 약속을 가볍게 넘기는 순간을 각자의 기준에서 비교할 수 있습니다.",
        ROLE_VOICE[c['private_group']]['fit']+' 친구 수가 많아야 좋은 인연이라는 뜻보다, 함께할 때 내 장점이 자연스럽게 나오고 서로의 부담이 커지지 않는지를 읽었습니다.'],a['need']+'과 '+p['need']+'을 함께 존중하는 사이',['daymaster','month','ten_gods'],'specific-friendship-context')
    elems=report['elements'];dominant=[x for x in elems if x['count']==max(e['count'] for e in elems)]
    add('elements','같은 불도, 누구에게나 같은 뜻은 아니에요',[
        '오행은 나무·불·흙·금속·물이라는 다섯 가지 상징이에요. 이 사주에서 겉에 확인한 구성은 '+', '.join(ELEMENT[e['element']]+' '+str(e['count'])+'개' for e in elems)+'입니다. 이 숫자는 구성표이지 성격 점수나 성공 확률은 아니에요.',
        '가장 많이 보이는 것은 '+' · '.join(ELEMENT[e['element']] for e in dominant)+'이에요. '+ ' '.join(ROLE_VOICE[role_for(e['element'],c['day']['stem']['element'])]['core'] for e in dominant)+' 이 뜻은 나를 나타내는 기운과 어떤 관계인지 함께 살핀 설명이라, 같은 개수라도 다른 사람에게는 다른 역할로 읽힙니다.',
        f"계절도 차이를 만들어요. {address}은 {report['month']['season']}에 태어났어요. "+c['seasonal'].split('이에요. ',1)[-1]+' 계절과 실제 배치를 함께 보아야 가장 많은 기운만으로 사람을 설명하는 일을 줄일 수 있습니다.',
        ('겉에 보이지 않는 것은 '+' · '.join(ELEMENT[e['element']] for e in elems if not e['count'])+'이에요. 숨은 글자까지 모두 없다는 뜻은 아니고, 그와 연결되는 능력이 없다는 뜻도 아닙니다. 보이지 않는 칸을 무조건 채우기보다 전체 균형에서 무엇이 필요한지는 다음 항목에서 따로 읽었어요.' if any(not e['count'] for e in elems) else '다섯 기운이 모두 보여도 똑같은 힘으로 쓰이지는 않아요. 계절과 위치에 따라 잘 드러나는 역할이 달라지기 때문에, 골고루 있다는 말보다 일과 관계에서 각각 무엇을 중요하게 읽는지가 더 구체적입니다.')],
        '개수에 계절과 기운 사이의 관계를 더해서 읽어요.',['counts','month','balance'],'elements-season-context')
    e=b.get('yong_element')
    if b['available'] and e:
        group=role_for(e,c['day']['stem']['element']);style,example=MANNER[e]
        balance_paras=[f"전체 균형을 살핀 계산에서는 {ELEMENT[e]}의 기운을 도움이 되는 방향으로 선택했어요. 가장 적은 기운을 자동으로 고른 것은 아니에요. "+('태어난 계절의 차고 더움과 건조함을 먼저 살핀 기준입니다.' if b['yong_method']=='조후' else '나를 받쳐주는 힘과 밖에 쓰는 힘의 관계를 살핀 기준입니다.'),
            c['seasonal'].split('이에요. ',1)[-1]+' 이것은 계절과 상징의 관계에 대한 설명이며, 내 몸이나 감정의 상태를 진단한 뜻은 아니에요.',
            ROLE_VOICE[group]['support']+f" {a['gift']}을 더 많이 쓰라는 말만 하기보다 그 힘이 계속 이어질 환경까지 살피는 이유입니다.",
            f"관계의 예로는 {example}을 떠올릴 수 있어요. {style}가 필요한지 실제 경험과 비교하는 방식입니다. 특정 색이나 물건을 사면 운이 바뀐다는 계산은 하지 않았어요.",
            capacity(c)]
    else:balance_paras=['출생 시간이 없어, 전체 균형을 돕는 기운은 확정하지 않았어요. 어떤 기운이 반드시 필요하다고 말하기보다 지금 확인한 배치에서 편하게 힘을 쓸 조건부터 읽습니다.',
        c['seasonal'].split('이에요. ',1)[-1],ROLE_VOICE[c['root_group']]['support'],f"{a['gift']}을 살리려면 {a['need']}이 있는지도 함께 봐야 해요. 같은 일을 맡더라도 혼자 모든 책임을 지는 자리와 질문하고 도움받을 수 있는 자리는 다르게 느껴질 수 있습니다."]
    add('balance','내 힘을 더 쓰는 것보다, 오래 쓸 수 있는 바탕',balance_paras,a['need']+'을 받쳐줄 조건도 필요해요.',['balance','month','ten_gods'],'yong-role-application')
    add('closing',f"{address}, 잘하는 모습과 편안한 모습은 둘 다 당신이에요",[
        f"이 이야기의 중심은 {a['gift']}과 {p['private']}이 함께 있다는 점이에요. 밖에서 무엇을 잘하는지와 가까운 사이에서 무엇을 바라는지를 따로 살피면, 좋은 말 하나로는 보이지 않던 내 모습까지 이해할 수 있습니다.",
        f"{report['month']['season']}이라는 계절, {o['gift']}이 더해지는 일하는 방식, {p['need']}이 필요한 관계를 함께 읽었어요. 비슷한 기운을 가진 사람이라도 이 조합이 달라지면 잘하는 일과 약점이 드러나는 순간까지 달라질 수 있습니다.",
        f"마음에 남길 주의점은 {c['work_risk']}이에요. 장점을 버리라는 이야기가 아니라, 그 장점이 나와 다른 사람을 힘들게 하는 순간을 구분하는 이야기입니다. 내게 자연스러운 방식이 모두에게 편한 방식은 아닐 수 있어요.",
        '이 풀이의 생활 장면은 이해를 돕는 예시예요. 이미 겪은 일을 알아냈다고 쓴 이야기는 아닙니다. 맞는 부분은 내 경험과 나란히 놓아보고, 맞지 않는 부분까지 나의 성격으로 받아들이지는 않아도 괜찮아요. 자세한 글자와 계산은 각 항목의 근거에서 확인할 수 있습니다.'],
        '내가 잘하는 힘과 마음이 편한 조건을 함께 기억해요.',['daymaster','month','ten_gods'],'experience-comparison-closing')
    sections={'work':{0:'힘이 나는 일',2:'어떤 환경이 맞을까',3:'피곤해지는 업무 조건'},'money':{0:'돈이 만들어지는 방식',3:'돈이 새기 쉬운 지점'},'relationships':{0:'마음이 가는 표현',2:'서운함이 쌓이는 순간',3:'편안한 상대의 모습'},'shadow':{0:'일에서 드러나는 약점',1:'관계에서 드러나는 약점',3:'실제로 이런 순간이 있었나요?'}}
    for chapter in chapters:
        chapter['paragraph_labels']={str(i):label for i,label in sections.get(chapter['topic'],{}).items()}
        chapter['body']='\n\n'.join(chapter['paragraphs'])
        if chapter['topic'] in ['overview','work','money','charm','shadow']:chapter['rule_ids'].append('monthly-roles:'+root+'+'+outside)
        if chapter['topic'] in ['overview','work','money'] and c['root_group']=='식상' and GROUP_OF[outside]=='재성':chapter['source_ids'].append('saju-food-wealth')
    return chapters
