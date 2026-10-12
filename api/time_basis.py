"""Compare declared time conventions without changing the selected birth chart."""
from calendar import isleap
from datetime import timedelta
from math import cos, sin, pi
from korean_saju import Saju


def equation_of_time_minutes(moment):
    """NOAA fractional-year approximation, minutes; not a saju judgement."""
    hour=moment.hour+moment.minute/60+moment.second/3600
    gamma=2*pi/(366 if isleap(moment.year) else 365)*(moment.timetuple().tm_yday-1+(hour-12)/24)
    return 229.18*(.000075+.001868*cos(gamma)-.032077*sin(gamma)-.014615*cos(2*gamma)-.040849*sin(2*gamma))


def compare_time_bases(saju, terms):
    moment=saju.kst_moment;longitude=saju.longitude
    longitude_offset=(longitude-135)*4
    equation=equation_of_time_minutes(moment)
    conventions=[('standard','한국 표준시',0),('mean','경도 보정 · 현재 풀이 기준',longitude_offset),
                 ('apparent','경도 + 균시차 보정 · 근사 비교',longitude_offset+equation)]
    options=[]
    for key,label,offset in conventions:
        # The library applies only longitude offset to day/hour, while keeping
        # the absolute birth moment for solar month/year. An equivalent offset
        # longitude is used only for comparison; it is never the birthplace.
        compared=saju if key=='mean' else Saju.from_birth(kst_moment=moment,solar_terms=terms,longitude=135+offset/4,yaja_si_separated=True)
        corrected=moment+timedelta(minutes=offset)
        options.append({'key':key,'label':label,'time':corrected.strftime('%H:%M:%S'),
                        'date':corrected.date().isoformat(),'day':compared.day_pillar.hanja,'hour':compared.hour_pillar.hanja,
                        'offset_minutes':round(offset,4),'selected':key=='mean'})
    return {'options':options,'changes_pillars':len({(o['day'],o['hour']) for o in options})>1,
            'equation_of_time_minutes':round(equation,4),'approximate':True,
            'note':'비교값은 보정 방식의 차이를 보여줘요. 균시차는 NOAA 근사식이며 다른 서비스가 어떤 방식을 썼는지는 그 서비스의 기준을 확인해야 합니다. 현재 풀이 기준을 자동으로 바꾸지 않아요.',
            'source_id':'saju-solar-time'}
