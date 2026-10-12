"""Build a licensed, reading-indexed dictionary for the local and hosted chooser."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
# Korean summaries translated from each record's kDefinition, not auspicious-name ratings.
GLOSSES='''佳 아름다움·좋음
可 가능함
嘉 훌륭함·기쁨
家 집·가족
歌 노래
江 큰 강
康 평안함·건강함
剛 굳셈
基 기초·바탕
起 일어남·시작
琪 옥의 한 종류
祺 복·좋은 운
圭 끝이 뾰족한 옥
均 고름·공평함
根 뿌리·바탕
錦 비단
南 남쪽
丹 붉은 빛
大 큼
代 대신함·세대
德 덕·도덕
東 동쪽
童 아이
朗 밝음·분명함
蓮 연꽃
連 이어짐
律 법·규칙
率 이끎·비율
帥 이끎·우두머리
䢦 앞장섬·이끎
倫 사람 사이의 관계
潾 맑은 물
璘 옥의 빛
麟 기린(상상 속 동물)
琳 아름다운 옥
林 숲
立 섬·세움
莉 흰 재스민
麗 아름다움
利 이익·이로움
理 이치·다스림
路 길
露 이슬
鹿 사슴
綠 초록
流 흐름
柳 버드나무
留 머묾
瑠 보석
俐 영리함
璃 유리
曼 넓음·아름다움
滿 가득함
明 밝음·분명함
銘 새김
茂 무성함
武 무예
舞 춤
文 글·문화
聞 들음·소식
珮 옥 장식
培 기름·쌓음
白 흼·깨끗함
凡 보통·모두
範 본보기·규칙
寶 보물
保 보호함
本 근본·바탕
富 풍부함
備 준비함
飛 날음
思 생각
沙 모래
相 서로
祥 상서로움·기쁨
常 늘·일상
桑 뽕나무
生 삶·태어남
星 별
聖 성스러움·성인
盛 풍성함·번성
世 세상·세대
昭 밝음
紹 이어감
素 흼·꾸밈없음
韶 아름다움·음악
松 소나무
頌 칭송
水 물
守 지킴
受 받음
首 머리·처음
壽 장수
淑 착함·맑음
順 따름
純 순수함
崇 높임·공경
承 이음·받음
丞 도움
勝 이김·뛰어남
始 시작
時 때·시간
詩 시
施 베풂
植 심음·식물
信 믿음
新 새로움
伸 펼침
兒 아이
安 평안함
岸 언덕·물가
言 말
硯 벼루
演 펼침·공연
燕 제비
溫 따뜻함
玉 옥·보석
沃 기름짐
完 완성·온전함
旺 번성
曜 햇빛·빛남
耀 빛남
瑤 아름다운 옥
勇 용기
容 모습
瑢 허리띠의 옥 장식
溶 녹음
友 친구
雨 비
遇 만남
雲 구름
元 처음·근원
原 근원
源 샘·근원
遠 멂·깊음
媛 아름다운 여자
有 있음
柔 부드러움
裕 넉넉함
悠 멂·여유
維 유지·지킴
愉 즐거움
宥 용서
侑 도움
猷 계획·방법
瑜 흠 없는 옥
由 이유·근원
唯 오직
尹 다스림
胤 자손·후계자
殷 풍성함
垠 경계·물가
義 의로움
宜 알맞음
怡 기쁨·화목
益 이로움
引 이끎
印 도장·표시
任 맡음·책임
一 하나
日 해·날
紫 자주색
子 아이
慈 사랑·자비
姿 모습
資 재물·자원
長 길음·우두머리
章 글·문장
在 있음
材 재료·재능
栽 심음·기름
才 재능
載 실음
梓 개오동나무
齊 고름
濟 도움·건넘
辰 이른 아침·다섯째 지지
振 떨침·일으킴
進 나아감
晉 나아감
柱 기둥
珠 구슬·진주
主 주인
遵 따름
埈 높음
濬 깊음·파냄
中 가운데
芝 영지버섯
枝 가지
祉 복·기쁨
哲 지혜
澈 철저함
千 천·많음
川 시내·강
泉 샘
天 하늘
晴 맑은 날씨
淸 맑음
靑 푸름·젊음
初 처음
采 모음
彩 빛깔
採 고름·모음
泰 큼
太 큼·매우
賀 축하
泫 눈물·빛남
玹 옥과 비슷한 돌
絢 찬란함·무늬
現 나타남
赫 빛남
憲 법
軒 높음·수레
顯 드러남·분명함
衡 헤아림
香 향기
向 향함
湖 호수
豪 용맹함
好 좋음
虎 호랑이
護 보호함
花 꽃
華 빛남·꽃
和 화목·평화
煥 빛남
歡 기쁨
環 옥 고리
煌 빛남
會 모임
孝 효도
曉 새벽·분명함
厚 두터움
勳 공훈
訓 가르침
希 바람·드묾
姬 아름다운 여자
稀 드묾
曦 햇빛·새벽
禧 기쁨·축하
熈 밝음
金 금·금속
李 오얏나무·성씨
朴 소박함·꾸밈없음·성씨
崔 높음·성씨
鄭 정나라·성씨
姜 생강·성씨
趙 조나라·성씨
張 펼침·늘임
韓 한국·성씨
吳 오나라·성씨
申 펼침·아룀
權 권한·권세
黃 누런빛·성씨
宋 송나라·성씨
劉 성씨·죽임
宮 궁궐·집'''
data=json.loads((ROOT/'knowledge/hanja-unihan.json').read_text())
for line in GLOSSES.splitlines():
    char,meaning=line.split(' ',1)
    assert data.get(char,{}).get('definition'),f'No source definition for {char}'
    data[char]['meaning_ko']=meaning
# Meanings depend on the selected reading: 率 is not the ratio sense at 솔.
data['率']['reading_meanings']={'솔':'거느림·이끎','률':'비율·정도','율':'비율·정도'}
data['帥']['reading_meanings']={'솔':'거느림·이끎','수':'장수·우두머리'}
(ROOT/'knowledge/hanja-unihan.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':'))+'\n')
registry_path=ROOT/'knowledge/name-registry.json'
registry=json.loads(registry_path.read_text()) if registry_path.exists() else {'readings':{},'checked_at':None}
index={}
for char,row in data.items():
    readings=set(row.get('readings',[]))
    readings.update(r for r,chars in registry['readings'].items() if char in chars)
    for reading in sorted(readings):
        if len(reading)==1 and '가'<=reading<='힣':
            index.setdefault(reading,[]).append({'c':char,'m':row.get('reading_meanings',{}).get(reading) or row.get('meaning_ko',''),'d':row.get('definition',''),'legal':None if reading not in registry['readings'] else char in registry['readings'][reading]})
for candidates in index.values():
    candidates.sort(key=lambda r:(not bool(r['m']),ord(r['c'])))
output={'source':'Unicode 17.0.0 Unihan','license':'./licenses/UNICODE-LICENSE.txt','readings':index,'registry_checked_at':registry['checked_at']}
(ROOT/'dist/assets/hanja-choices.json').write_text(json.dumps(output,ensure_ascii=False,separators=(',',':'))+'\n')
print({'readings':len(index),'korean_meanings':sum(bool(v.get('meaning_ko')) for v in data.values()),'bytes':(ROOT/'dist/assets/hanja-choices.json').stat().st_size})
