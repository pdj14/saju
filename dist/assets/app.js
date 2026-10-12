(() => {
  'use strict';
  const $ = (s, root = document) => root.querySelector(s);
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const icon = name => `<svg class="icon" aria-hidden="true"><use href="#i-${name}"/></svg>`;
  const dialog = $('#reading-dialog');
  const body = $('#dialog-body');
  const info = $('#info-dialog');
  const apiBase = (window.MOA_API_BASE || '').replace(/\/$/, '');
  const local = ['localhost', '127.0.0.1'].includes(location.hostname);
  let currentService = 'name';
  let lastProfile = null;
  let currentResult = null;
  let currentRequest = null;
  let readController = null;
  let questionPending = false;
  let toastTimer;
  let loadingTimer;
  let favorites = [];
  try {
    const saved = JSON.parse(localStorage.getItem('moa-favorite-names') || '[]');
    if (Array.isArray(saved)) favorites = saved.filter(n => typeof n === 'string' && /^[가-힣]{1,12}$/.test(n)).slice(0,12);
  } catch {}
  const incoming = new URLSearchParams(location.search);
  const cleanName = value => /^[가-힣]{1,12}$/.test(value || '') ? value : '';
  const entryName = cleanName(incoming.get('name') || incoming.get('candidate'));
  const entrySurname = /^[가-힣]{1,4}$/.test(incoming.get('surname') || '') ? incoming.get('surname') : '';
  if (entryName) {
    $('#entry-message').hidden = false;
    $('#entry-message').textContent = `마음에 둔 ‘${entrySurname}${entryName}’, 여기서 이어서 살펴봐요.`;
  }
  const healthPromise = fetch(apiBase + '/api/health', {signal:AbortSignal.timeout(12000)})
    .then(async r => r.ok ? await r.json() : {ready:false,demo:!local})
    .catch(() => ({ready:false,demo:!local}));

  const services = {
    name:{eyebrow:'A LITTLE NAME',title:'우리 아이 이름을 함께 골라볼까요?',description:'글자마다 뜻을 읽고, 출생 정보와 함께 살펴봐요. 같은 이름의 다른 한자 조합도 추천해드려요.',submit:'이름 상담 리포트 보기',label:'아이 이름 상담'},
    saju:{eyebrow:'SAJU ANALYSIS',title:'나의 사주를 풀어볼까요?',description:'생년월일시로 타고난 사주를 읽어요. 성향·적성·재물·관계를 근거와 함께 자세히 풀어드려요.',submit:'나의 사주 분석하기',label:'사주 원국 풀이'},
    compatibility:{eyebrow:'BETTER TOGETHER',title:'어떤 두 사람이 궁금한가요?',description:'각자의 사주부터 보완되는 기운, 애정 표현과 돈·약속에서 부딪히는 점까지 비교해요.',submit:'우리의 조합 알아보기',label:'우리 궁합'},
    stars:{eyebrow:'UNDER YOUR SKY',title:'태어난 날의 하늘을 만나봐요.',description:'태양과 달, 행성의 위치를 계산하고 같은 생일의 사주도 함께 살펴봐요.',submit:'내 별자리 알아보기',label:'별자리 이야기'}
  };

  function toast(message) {
    clearTimeout(toastTimer);
    $('#toast').textContent = message;
    $('#toast').classList.add('show');
    toastTimer = setTimeout(() => $('#toast').classList.remove('show'), 2800);
  }
  function syncBodyLock() {
    document.body.classList.toggle('dialog-open', dialog.open || info.open);
  }
  function openDialog() { if (!dialog.open) dialog.showModal(); syncBodyLock(); }
  function closeDialog() { readController?.abort(); clearInterval(loadingTimer); dialog.close(); syncBodyLock(); }
  $('#close-dialog').addEventListener('click', closeDialog);
  $('#close-info').addEventListener('click', () => { info.close(); syncBodyLock(); });
  for (const d of [dialog,info]) {
    d.addEventListener('close', syncBodyLock);
    d.addEventListener('cancel', () => { if (d === dialog) {readController?.abort();clearInterval(loadingTimer);} });
    d.addEventListener('click', e => {
      if (e.target !== d) return;
      const rect = d.getBoundingClientRect();
      if (e.clientX < rect.left || e.clientX > rect.right || e.clientY < rect.top || e.clientY > rect.bottom) {
        if (d === dialog) closeDialog(); else {info.close();syncBodyLock();}
      }
    });
  }

  function dateFields(prefix = '', profile = {}, required = true, includeLuck = true) {
    return `<div class="form-field"><label for="${prefix}birth-date">생일 <span class="optional">양력${required ? '' : ' · 선택'}</span></label><input id="${prefix}birth-date" name="${prefix}birth_date" type="date" min="1900-01-01" max="2050-12-31" value="${esc(profile.birth_date)}" ${required?'required':''}>${!required?'<span class="input-hint">아이의 예정일로 볼 경우, 실제 출생 후 결과가 달라질 수 있어요.</span>':''}</div>
      <div class="form-field"><label for="${prefix}birth-time">태어난 시간 <span class="optional">모르면 비워두세요</span></label><input id="${prefix}birth-time" name="${prefix}birth_time" type="time" value="${esc(profile.birth_time)}"></div>${window.MoaPlaces.field(prefix,profile,required)}${includeLuck?`<div class="form-field"><label for="${prefix}gender">인생 흐름을 볼 계산 기준 <span class="optional">선택</span></label><select name="${prefix}gender" id="${prefix}gender"><option value="">선택하지 않음 · 시기별 흐름 생략</option><option value="male" ${profile.gender==='male'?'selected':''}>남성 기준</option><option value="female" ${profile.gender==='female'?'selected':''}>여성 기준</option></select><span class="input-hint">전통 대운의 순행·역행을 정하는 기준이에요. 출생 시간과 함께 선택하면 성장기·청년기·중년기·노년기의 흐름을 함께 읽을 수 있어요.</span></div>`:`<input type="hidden" name="${prefix}gender" value="${esc(profile.gender)}">`}`;
  }
  const hanjaField=(prefix='',profile={})=>window.MoaHanja.field(prefix,profile);
  function profileFields(prefix = '', profile = {}) {
    return `<div class="form-row"><div class="form-field surname-field"><label for="${prefix}person-surname">성 <span class="optional">선택</span></label><input id="${prefix}person-surname" name="${prefix}surname" placeholder="김" maxlength="4" value="${esc(profile.surname)}" autocomplete="off"></div><div class="form-field"><label for="${prefix}person-name">이름 <span class="optional">선택</span></label><input id="${prefix}person-name" name="${prefix}name" placeholder="이름을 넣으면 소리 풀이도 함께" value="${esc(profile.name)}" maxlength="12" autocomplete="off"></div></div>${currentService==='stars'?'':hanjaField(prefix,profile)}${dateFields(prefix,profile,true,currentService!=='stars')}`;
  }

  async function openService(service, options = {}) {
    if(!await window.MoaPlaces.ready){toast('출생지 목록을 불러오지 못했어요. 새로고침 후 다시 확인해 주세요.');return;}
    readController?.abort();clearInterval(loadingTimer);
    currentService = service;
    dialog.classList.remove('report-mode');
    const meta = services[service];
    const profile = options.profile || (options.reuse && lastProfile) || (service==='name' ? {name:entryName,surname:entrySurname} : {});
    $('#dialog-step').textContent = '정보 입력';
    let fields;
    if (service === 'name') {
      fields = `<div class="form-row"><div class="form-field surname-field"><label for="surname">성 <span class="optional">선택</span></label><input id="surname" name="surname" placeholder="김" maxlength="4" value="${esc(profile.surname)}" autocomplete="off"></div><div class="form-field"><label for="candidate-name">마음에 둔 이름</label><input id="candidate-name" name="name" placeholder="예: 하린" maxlength="12" value="${esc(profile.name)}" required autocomplete="off"></div></div>${hanjaField('',profile)}<details class="name-candidates-input" ${options.name_candidates?.length?'open':''}><summary>다른 이름 후보도 함께 비교하기 <span class="optional">최대 5개</span></summary><p class="input-hint">생일과 시간은 모두 같은 아이의 정보로 비교해요. 한자를 모르면 비워두세요.</p>${[0,1,2,3].map(i=>{const p=options.name_candidates?.[i]||{};return `<div class="name-candidate-input"><div class="form-field"><label for="candidate-${i}-name">이름 후보 ${i+2} <span class="optional">선택</span></label><input id="candidate-${i}-name" name="candidate-${i}-name" maxlength="4" placeholder="성은 빼고 입력해 주세요" value="${esc(p.name)}"></div>${hanjaField('candidate-'+i+'-',p)}</div>`;}).join('')}</details><details class="surname-hanja-options" ${profile.surname_hanja?'open':''}><summary>성의 한자도 알고 있나요? <span class="optional">선택</span></summary>${window.MoaHanja.field('',profile,'surname')}</details><div class="form-field naming-preference"><label for="naming-preference">이름에 담고 싶은 마음</label><select id="naming-preference" name="naming_preference">${[['balanced','뜻을 고르게 살펴보기'],['wisdom','지혜와 배움'],['warmth','따뜻함과 배려'],['growth','성장과 자기 길'],['grace','아름다움과 품격']].map(([v,l])=>`<option value="${v}" ${profile.naming_preference===v?'selected':''}>${l}</option>`).join('')}</select></div><div class="naming-birth-heading"><h3>아이의 출생 정보</h3><p>생년월일과 시간을 더하면 사주도 함께 살펴봐요.</p></div>${dateFields('',profile,false,false)}`;
    } else if (service === 'compatibility') {
      fields = `<p class="profile-divider" style="border-top:0;padding-top:0">첫 번째 사람</p>${profileFields('',profile)}<p class="profile-divider">두 번째 사람</p>${profileFields('partner-',options.partner||{})}`;
    } else fields = profileFields('',profile);
    body.innerHTML = `<h2 id="dialog-title" class="form-title">${meta.title}</h2><p class="form-description">${meta.description}</p><form id="reading-form">${fields}<div id="form-error" class="form-error" role="alert" hidden></div><button class="button primary form-submit" type="submit">${meta.submit}${icon('arrow')}</button><p class="form-footer" id="form-footer">입력한 정보로 사주·별자리·이름을 함께 살펴봐요.</p></form>`;
    $('#reading-form').addEventListener('submit', submitReading);
    window.MoaHanja.mount($('#reading-form'));
    window.MoaPlaces.mount($('#reading-form'));
    for(const event of ['input','change'])$('#reading-form').addEventListener(event,()=>{$('#form-error').hidden=true;});
    openDialog();
    dialog.scrollTop = 0;
    requestAnimationFrame(() => {
      if (!$('#reading-form')?.contains(document.activeElement)) {
        (service==='name' ? $('#candidate-name') : $('#person-name'))?.focus({preventScroll:true});
      }
    });
    const health = await healthPromise;
    if ($('#reading-form') && currentService === service && health.demo) $('#form-footer').textContent = '이 링크에서는 입력한 생일로 계산할 수 없어요. 홈의 예시 보기에서 샘플 풀이를 살펴볼 수 있어요.';
  }

  function formProfile(fd,prefix='') {
    return {name:String(fd.get(prefix+'name')||'').trim(),surname:String(fd.get(prefix+'surname')||'').trim(),name_hanja:String(fd.get(prefix+'name_hanja')||'').trim(),surname_hanja:String(fd.get(prefix+'surname_hanja')||'').trim(),naming_preference:String(fd.get(prefix+'naming_preference')||'balanced'),birth_date:fd.get(prefix+'birth_date')||null,birth_time:fd.get(prefix+'birth_time')||null,city:fd.get(prefix+'city')||(fd.get(prefix+'birth_date')?'':'seoul'),gender:fd.get(prefix+'gender')||null};
  }
  async function submitReading(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const hanjaError=window.MoaHanja.validate(form);
    if(hanjaError){$('#form-error').hidden=false;$('#form-error').textContent=hanjaError;return;}
    const fd = new FormData(form);
    const service = currentService;
    const profile = formProfile(fd);
    const partner = service==='compatibility' ? formProfile(fd,'partner-') : null;
    for (const p of [profile,partner].filter(Boolean)) {
      if ((p.name && !/^[가-힣]{1,12}$/.test(p.name)) || (p.surname && !/^[가-힣]{1,4}$/.test(p.surname))) {
        $('#form-error').hidden = false;$('#form-error').textContent = '이름과 성은 한글로 입력해 주세요.';return;
      }
    }
    for(const p of [profile,partner].filter(Boolean)) {
      if(p.name_hanja && (!/^[\p{Script=Han}]+$/u.test(p.name_hanja)||[...p.name_hanja].length!==[...p.name].length)) {
        $('#form-error').hidden=false;$('#form-error').textContent='이름 한자는 성을 제외하고, 한글 이름과 같은 글자 수로 입력해 주세요.';return;
      }
    }
    const name_candidates=service==='name'?[0,1,2,3].map(i=>({name:String(fd.get('candidate-'+i+'-name')||'').trim(),name_hanja:String(fd.get('candidate-'+i+'-name_hanja')||'').trim()})).filter(p=>p.name):[];
    if(service==='name'&&new Set([profile.name,...name_candidates.map(p=>p.name)]).size!==name_candidates.length+1){$('#form-error').hidden=false;$('#form-error').textContent='같은 이름은 한 번만 입력해 주세요. 한자는 이름별로 비교할 수 있어요.';return;}
    const request = {service,profile,partner,name_candidates};
    const health = await healthPromise;
    if (health.demo) {
      const error=$('#form-error');
      error.hidden=false;
      error.textContent='이 링크는 화면 미리보기라 입력한 정보로 분석할 수 없어요. 실제 분석은 이 PC에서 실행 중인 서비스에서 이용해 주세요.';
      if(['saju','name','compatibility','stars'].includes(service)) {
        const sample=document.createElement('button');sample.type='button';sample.className='button';sample.textContent=service==='name'?'이름 풀이 예시 보기':service==='compatibility'?'궁합 비교 예시 보기':service==='stars'?'별자리 해설 예시 보기':'사주 풀이 예시 보기';
        sample.addEventListener('click',()=>$(service==='name'?'#sample-trigger':service==='compatibility'?'#compatibility-sample-trigger':service==='stars'?'#stars-sample-trigger':'#saju-sample-trigger').click());error.append(document.createElement('br'),sample);
      }
      return;
    }
    if (!health.ready) {$('#form-error').hidden=false;$('#form-error').textContent=health.reason||'지금은 풀이를 연결하기 어려워요. 잠시 후 다시 시도해 주세요.';return;}
    currentRequest = request;
    currentResult = null;
    readController = new AbortController();
    renderLoading(service);
    try {
      const readingTask = fetch(apiBase+'/api/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal:readController.signal});
      readingTask.catch(()=>{});
      if(service==='name'||profile.birth_date) {
        try {
          const preliminary=await fetch(apiBase+(service==='name'?'/api/name/preview':service==='compatibility'?'/api/compatibility/preview':'/api/profile/preview'),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal:readController.signal});
          if(preliminary.ok&&dialog.open)showResult(await preliminary.json(),request);
        } catch(error) {if(error.name==='AbortError')throw error;}
      }
      const r = await readingTask;
      const result = await r.json();
      if (!r.ok) throw new Error(typeof result.detail==='string'?result.detail:'입력한 생일과 시간을 다시 확인해 주세요.');
      if (!dialog.open) return;
      lastProfile = profile;
      showResult(result, request);
    } catch (error) {
      if (error.name==='AbortError') return;
      if (!dialog.open) return;
      if(currentResult?.analysis_pending) {
        showResult({...currentResult,generation_error:error.message},request);
        return;
      }
      await openService(service,{profile,partner,name_candidates});
      $('#form-error').hidden=false;
      $('#form-error').textContent=error.message==='Failed to fetch'?'연결이 잠시 끊겼어요. 다시 시도해 주세요.':error.message;
    } finally {clearInterval(loadingTimer);}
  }

  function renderLoading(service) {
    $('#dialog-step').textContent='분석 중';
    body.innerHTML=`<div class="loading-view"><img class="loading-mark" src="./assets/mark.svg" alt=""><h2 id="dialog-title">${service==='name'?'이름의 뜻과 추천 조합을 살펴보고 있어요.':service==='stars'?'태어난 날의 별자리와 천체를 살펴보고 있어요.':'사주를 풀고 있어요.'}</h2><p id="loading-text">입력한 정보와 참고 자료를 함께 살펴봐요.<br>잠시만 기다려 주세요.</p><div class="loading-ticks" aria-hidden="true"><i></i><i></i><i></i></div></div>`;
    let tick=0; clearInterval(loadingTimer);
    loadingTimer=setInterval(()=>{tick++;const el=$('#loading-text');if(el&&tick>=3)el.innerHTML='입력한 정보와 참고 자료로 해설을 정리하고 있어요.<br>깊이 있는 해석에는 조금 더 시간이 걸릴 수 있어요.';},8000);
  }

  async function loadAdditional(service) {
    const previous=currentResult;
    const request={...currentRequest,service,partner:service==='compatibility'?currentRequest.partner:null};
    currentService=service;
    readController?.abort();readController=new AbortController();
    renderLoading(service);
    try {
      const r=await fetch(apiBase+'/api/read',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(request),signal:readController.signal});
      const result=await r.json();
      if(!r.ok)throw Error(typeof result.detail==='string'?result.detail:'풀이를 완성하지 못했어요.');
      if(dialog.open)showResult(result,request);
    } catch(error) {
      if(error.name==='AbortError')return;
      if(dialog.open&&previous){currentService=currentRequest.service;showResult(previous,currentRequest);toast(error.message);}
    } finally {clearInterval(loadingTimer);}
  }

  const demoSources=[{id:'name-sound',title:'이름의 음양오행 구성 원리',url:'https://namestory.kr/m/bbs/board.php?bo_table=sub3_1&page=17&wr_id=19',note:'참고 자료의 예시. 아래 내용은 실제 개인 분석 결과가 아니에요.'}];
  function demoResult(service) {
    const examples={
      name:{title:'‘하린’, 한번 소리 내어 불러볼까요?',summary:'이름은 매일 부르게 되는 말이에요. 마음에 드는 소리인지 먼저 느껴보세요.',tiles:[{label:'소리의 느낌',text:'이름을 천천히, 또 빠르게 불러보세요. 가족에게 익숙해질 소리인지 느껴봐요.'},{label:'한자의 뜻은 따로',text:'같은 한글 이름에도 여러 한자가 있어요. 뜻과 획수는 글자를 정한 뒤 확인해요.'},{label:'성을 붙여서도',text:'성과 이름을 붙여 불렀을 때 자연스러운지도 들어보세요.'}],suggestion:'“하린아, 잘 잤어?”처럼 일상 속 문장에 넣어 불러보세요.',caveat:'한글 이름만으로 한자의 뜻이나 아이의 미래를 판단할 수는 없어요.'},
      saju:{title:'나를 알아보는 새로운 질문.',summary:'사주를 나를 돌아보는 이야기로 읽어봐요. 내 경험과 함께 생각해 보는 것이 좋아요.',tiles:[{label:'내가 편한 방식',text:'새로운 일을 시작할 때 나는 무엇부터 하는지 떠올려보세요.'},{label:'내가 힘을 얻는 순간',text:'누군가와 이야기할 때인지, 혼자 정리할 때인지 살펴봐요.'},{label:'내 속도 찾기',text:'다른 사람의 속도보다 내가 편안한 리듬에 귀를 기울여봐요.'}],suggestion:'요즘 즐거웠던 순간을 세 가지만 적어보세요.',caveat:'이 화면은 특정 생일의 사주를 계산한 결과가 아닌 설명 예시예요.'},
      compatibility:{title:'같은 마음, 다른 표현일 수도 있어요.',summary:'서로 다른 방식으로 마음을 표현하는 순간을 떠올려봐요. 궁합은 대화를 시작하는 작은 계기로 읽어주세요.',tiles:[{label:'우리의 공통점',text:'함께 있을 때 편안한 순간이 언제인지 이야기해 보세요.'},{label:'다르게 느끼는 점',text:'각자 혼자 쉬고 싶은 시간도 존중해 주세요.'},{label:'함께 해볼 것',text:'요즘 고마웠던 일을 한 가지씩 나눠보세요.'}],suggestion:'“나는 이럴 때 힘이 나”라는 문장으로 대화를 시작해 보세요.',caveat:'이 화면은 두 사람의 생일을 비교한 실제 궁합 결과가 아니에요.'},
      stars:{title:'나를 비춰보는 또 다른 하늘.',summary:'태양과 달의 상징을 통해 새로운 질문을 만나봐요. 내 경험을 함께 떠올리며 읽어주세요.',tiles:[{label:'태양의 이야기',text:'내가 어떤 순간에 자신답다고 느끼는지 생각해 보세요.'},{label:'달의 이야기',text:'어떤 환경에서 편안함을 느끼는지 살펴봐요.'},{label:'함께 읽기',text:'여러 상징을 모두 나의 확정된 성격으로 받아들일 필요는 없어요.'}],suggestion:'편안한 하루를 만드는 나만의 습관을 하나 찾아보세요.',caveat:'이 화면은 태양·달의 위치를 계산한 실제 별자리 결과가 아니에요.'}
    };
    return {...examples[service],demo:true,reading_id:null,facts:{},sources:service==='name'?demoSources:[{title:'계산과 풀이의 기준',url:'https://github.com/glee1228/korean_saju',note:'서비스 구성의 참고 자료예요.'}]};
  }

  async function namingExample(){const r=await fetch('./assets/naming-example.json');if(!r.ok)throw new Error('이름 예시를 불러오지 못했어요.');return r.json();}
  async function sajuExample() {
    const response=await fetch('./assets/report-example.json');
    if(!response.ok)throw new Error('사주 예시를 불러오지 못했어요.');
    return response.json();
  }

  function safeLink(url) {try{const u=new URL(url);return u.protocol==='https:'?esc(u.href):'#';}catch{return '#';}}
  function sourcesMarkup(sources, facts={}) {
    let factsMarkup='';
    if(facts.chart){const c=facts.chart;factsMarkup=`<div class="facts-section">${c.pillars.map((p,i)=>`<span class="fact-pill">${['년','월','일','시'][i]} ${esc(p||'시간 모름')}</span>`).join('')}<small>양력 · 한국 시간 · 경도 보정 · 야자시 분리${c.solar_terms_approximate?' · 절기 경계는 추가 확인 필요':''}</small></div>`;}
    if(facts.sun)factsMarkup=`<div class="facts-section"><span class="fact-pill">태양 ${esc(facts.sun.sign)} · ${esc(facts.sun.longitude)}°</span>${facts.moon?`<span class="fact-pill">달 ${esc(facts.moon.sign)} · ${esc(facts.moon.longitude)}°</span>`:''}<small>열대황도 · 지심 위치${!facts.hour_known?' · 시간 미입력 시 정오 참고':''}</small></div>`;
    return `<details class="source-details"><summary>${icon('book')}참고 자료와 계산 기준${icon('chevron')}</summary><div class="source-body">${(sources||[]).map(s=>`<div><a href="${safeLink(s.url)}" target="_blank" rel="noopener noreferrer">${esc(s.title)} ↗</a><small>${esc(s.note)}</small></div>`).join('')}${factsMarkup}<small>여러 자료가 비슷한 해석을 하더라도 미래 예측의 정확도를 뜻하지는 않아요.</small></div></details>`;
  }

  function showResult(result,request) {
    clearInterval(loadingTimer);
    const preserved=currentResult?.analysis_pending&&result.report?{tab:body.querySelector('[data-report-tab][aria-selected="true"]')?.dataset.reportTab,scroll:dialog.scrollTop}:null;
    currentResult=result;currentRequest=request;
    questionPending=false;
    const service=request.service,meta=services[service];
    const report=result.report,naming=result.naming_report||report?.naming,pair=result.compatibility_report;
    dialog.classList.toggle('report-mode',Boolean(report||naming||pair));
    $('#dialog-step').textContent=result.demo?'분석 화면 미리보기':result.analysis_pending?(naming?'이름별 해설 작성 중':'자세한 풀이 작성 중'):naming?'이름 후보 비교':report?'나의 풀이':'핵심 분석';
    const candidate=naming?.name||naming?.candidate_reports?.find(p=>p.recommended_rank===1)?.name||request.profile.name;
    const next=report?[[service==='stars'?'saju':'stars',service==='stars'?'같은 정보로 사주도 읽어보기':'같은 정보로 별자리도 읽어보기'],['compatibility','같은 정보로 궁합도 알아보기']]:service==='name'?[['compatibility','우리 가족의 조합은?'],['saju','나의 사주도 알아보기']]:[['name','아이 이름도 알아볼래요'],[service==='stars'?'saju':'stars',service==='stars'?'사주로도 알아보기':'별자리로도 알아보기']];
    const hasReading=!result.demo&&result.reading_id;
    const pairExamples=pair&&result.demo&&!pair.generation?'<div class="pair-example-options"><button data-pair-example="support">서로 도움 되는 방향이 있는 예시</button><button data-pair-example="tension">보완과 충돌이 함께 있는 예시</button></div>':'';
    body.innerHTML=`${report||naming||pair?'':`<div class="result-label"><span class="dot green"></span>${meta.label}</div>`}<h2 class="result-title" id="dialog-title">${esc(result.title)}</h2>${result.demo?'<p class="demo-notice">화면 미리보기예요. 아래 내용은 입력한 정보로 분석한 결과가 아닌 예시입니다.</p>':''}<p class="result-summary">${esc(result.summary)}</p>${pairExamples}${pair?window.MoaCompatibility.render(pair):naming?window.MoaNaming.render(naming):report?window.MoaReport.render(report):`<div class="result-tiles">${result.tiles.map((t,i)=>`<div class="result-tile"><h3><span>0${i+1}</span>${esc(t.label)}</h3><p>${esc(t.text)}</p></div>`).join('')}</div>`}${!report&&!naming&&!pair&&result.facts?.name?.hanja_provided?window.MoaProfile.hanjaName(result.facts.name):''}${report||naming||pair?'':`<div class="result-suggestion">${icon('spark')}<p>${esc(result.suggestion)}</p></div>`}<p class="result-caveat">${esc(result.caveat)}</p>${sourcesMarkup(result.sources,result.facts)}<div class="result-tools">${service==='name'?`<button id="save-name">${icon('heart')}관심 이름에 담기</button><a href="https://www.namechart.kr/name/${encodeURIComponent(candidate)}" target="_blank" rel="noopener noreferrer">이 이름의 통계 찾아보기 ↗</a>`:''}${report||naming||pair?'<button id="print-report">리포트 인쇄 / PDF ↗</button>':''}<button id="share-reading">${icon('share')}${result.demo?'예시 내용 복사':'리포트 복사'}</button></div><section class="followup"><h3>조금 더 궁금한가요?</h3><div class="question-chips"><button data-question="어려운 말 없이 더 쉽게 설명해 줘.">더 쉽게 설명해 줘</button><button data-question="${service==='name'?'현재 한자 조합의 뜻과 추천 후보의 차이를 자세히 설명해 줘.':'타고난 성향의 장점과 약점, 그렇게 해석한 이유를 자세히 설명해 줘.'}">${service==='name'?'한자 조합의 추천 이유':'성향과 해석의 이유'}</button>${report?'<button data-question="사주와 점성술의 결과를 어떻게 함께 읽으면 좋을까?">사주와 점성술 함께 읽기</button>':''}${service==='name'?'<button data-question="이 이름의 글자 뜻과 인명용 독음은 어떻게 확인했어?">한자와 독음 확인</button>':''}</div><form class="ask-form" id="ask-form"><input name="question" id="question" aria-label="풀이에 대해 더 물어보기" placeholder="편하게 더 물어보세요" maxlength="400" required autocomplete="off"><button type="submit" aria-label="질문 보내기">${icon('arrow')}</button></form><div id="answers" aria-live="polite"></div></section><div class="continue"><p>이런 이야기도 만나볼까요?</p><div class="continue-buttons">${next.map(([s,label])=>`<button data-next-service="${s}">${label}${icon('arrow')}</button>`).join('')}<button id="edit-reading">다시 입력하기</button></div></div>`;
    dialog.scrollTop=0;
    if(report) {if(service==='name'){const nameTab=$('#tab-name');nameTab.textContent='이름 상담';nameTab.parentElement.prepend(nameTab);}else if(service==='stars'){const starTab=$('#tab-astrology');starTab.textContent='별자리 해설';starTab.parentElement.prepend(starTab);}window.MoaReport.mount(body,openInfo);$('#print-report').addEventListener('click',()=>window.print());if(preserved?.tab){$('#tab-'+preserved.tab)?.click();dialog.scrollTop=preserved.scroll;}else if(service==='name'){$('#tab-name').click();}else if(service==='stars'){$('#tab-astrology').click();}}
    body.querySelectorAll('[data-additional-service]').forEach(b=>b.addEventListener('click',()=>loadAdditional(b.dataset.additionalService)));
    if(result.generation_error) {
      const message=document.createElement('p');message.className='form-error';message.setAttribute('role','alert');message.textContent=result.generation_error;
      const retry=document.createElement('button');retry.className='button';retry.textContent='자세한 풀이 다시 받기';retry.addEventListener('click',()=>loadAdditional(service));
      body.querySelector('.result-summary').after(message,retry);
    }
    if(pair){body.querySelectorAll('[data-pair-example]').forEach(b=>b.addEventListener('click',()=>openPairExample(b.dataset.pairExample)));window.MoaCompatibility.mount(body,pair,openInfo);$('#print-report').addEventListener('click',()=>window.print());}
    if(naming){window.MoaNaming.mount(body,choice=>{const selected=typeof choice==='string'?{name:request.profile.name,name_hanja:choice}:choice;const others=[{name:request.profile.name,name_hanja:request.profile.name_hanja},...(request.name_candidates||[])].filter(p=>p.name!==selected.name);openService('name',{profile:{...request.profile,...selected},name_candidates:others});});if(!report)$('#print-report')?.addEventListener('click',()=>window.print());}
    $('#save-name')?.addEventListener('click',()=>saveName(candidate));
    $('#share-reading').addEventListener('click',async()=>{
      const text=(result.demo?'[모아 화면 예시]\n':'[모아 풀이]\n')+result.title+'\n\n'+result.summary+'\n\n'+result.tiles.map(t=>t.label+': '+t.text).join('\n')+(pair?'\n\n[두 사람 궁합]\n'+pair.chapters.map(c=>c.title+'\n'+c.body).join('\n\n')+'\n\n[각자의 사주]\n'+pair.people.map(p=>p.name+'\n'+p.report.chapters.map(c=>c.title+'\n'+c.body).join('\n\n')).join('\n\n'):'')+(report?'\n\n'+report.chapters.map(c=>c.title+'\n'+c.body+'\n'+c.reflection).join('\n\n'):'')+(report?.luck_cycles?.available?'\n\n[나이대별 흐름]\n'+report.luck_cycles.stages.map(s=>s.label+' · '+s.age_label+'\n'+s.title+'\n'+s.paragraphs.join('\n\n')).join('\n\n'):'')+(naming?.candidate_reports?'\n\n[이름 후보 비교]\n'+(naming.comparison?.paragraphs||[]).join('\n\n')+(naming.birth_reading?'\n\n[공통 출생 해설]\n'+naming.birth_reading.chapters.map(c=>c.title+'\n'+c.paragraphs.join('\n\n')).join('\n\n'):'')+'\n\n'+naming.candidate_reports.map(p=>p.display_name+'\n'+(p.verdict||'해설 작성 중')+'\n'+p.chapters.map(c=>c.title+'\n'+c.paragraphs.join('\n\n')).join('\n\n')+'\n'+p.recommendations.map(c=>c.name_hanja+': '+c.reason+'\n'+c.story+'\n'+c.explanation.join('\n')).join('\n\n')).join('\n\n'):naming?'\n\n[이름 상담]\n'+naming.chapters.map(c=>c.title+'\n'+c.paragraphs.join('\n')).join('\n\n')+'\n\n[비교할 한자 조합]\n'+naming.recommendations.map(c=>c.name_hanja+': '+c.reason+'\n'+c.story).join('\n\n'):'')+(report?.astrology?'\n\n[점성술]\n'+report.astrology.positions.map(p=>p.label+': '+(p.sign_confirmed?p.sign:(p.possible_signs||[]).join(' / '))+' '+p.degree_in_sign+'°'+(!report.astrology.hour_known?' (정오 참고)':'')).join('\n')+'\n\n'+(report.astrology.interpretation||[]).map(c=>c.title+'\n'+c.paragraphs.join('\n\n')).join('\n\n')+'\n'+report.comparison.note:'')+(report?.name_analysis?.available?'\n\n[이름]\n'+report.name_analysis.display_name+': '+report.name_analysis.letters.map(l=>l.syllable+'('+l.initial+'·'+l.element+')').join(' ')+(report.name_analysis.hanja_provided?'\n'+report.name_analysis.name_hanja+'\n'+report.name_analysis.hanja_explanation:''):'')+'\n\n'+result.caveat;
      try{await navigator.clipboard.writeText(text);toast('내용을 복사했어요.');}catch{toast('이 브라우저에서는 복사 권한을 확인해 주세요.');}
    });
    $('#ask-form').addEventListener('submit',e=>{e.preventDefault();askQuestion($('#question').value);});
    document.querySelectorAll('[data-question]').forEach(b=>b.addEventListener('click',()=>askQuestion(b.dataset.question)));
    document.querySelectorAll('[data-next-service]').forEach(b=>b.addEventListener('click',()=>openService(b.dataset.nextService,{reuse:Boolean(lastProfile)})));
    $('#edit-reading').addEventListener('click',()=>openService(service,{profile:request.profile,partner:request.partner}));
    if(result.analysis_pending) {
      $('#question').placeholder='자세한 풀이가 완성되면 질문할 수 있어요';
      $('#question').disabled=true;
      $('#ask-form button').disabled=true;
      document.querySelectorAll('[data-question]').forEach(b=>b.disabled=true);
      $('#print-report').disabled=true;
    } else if(!hasReading) $('#question').placeholder='미리보기에서도 질문 흐름을 체험해요';
  }

  async function askQuestion(question) {
    question=question.trim();if(!question||questionPending)return;
    questionPending=true;
    const input=$('#question');input.value='';
    const submit=$('#ask-form button');submit.disabled=true;
    const target=$('#answers'),card=document.createElement('div');card.className='answer-card';
    const title=document.createElement('h4');title.textContent=question;card.append(title);
    const answer=document.createElement('p');answer.textContent='이어서 살펴보고 있어요…';card.append(answer);target.append(card);
    card.scrollIntoView({behavior:'smooth',block:'nearest'});
    try {
      if(currentResult.demo) {
        answer.textContent='이곳에는 계산 결과와 참고 자료를 바탕으로 짧은 답변이 이어져요. 현재는 화면 미리보기라 개인 질문에 대한 실제 풀이는 제공하지 않아요.';
        const note=document.createElement('small');note.textContent='질문과 답변 흐름의 예시';card.append(note);
      } else {
        const result=await fetch(apiBase+'/api/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reading_id:currentResult.reading_id,question}),signal:AbortSignal.timeout(125000)});
        const data=await result.json();if(!result.ok)throw new Error(typeof data.detail==='string'?data.detail:'질문을 다시 보내주세요.');
        answer.textContent=data.answer;
        card.insertAdjacentHTML('beforeend',sourcesMarkup(data.sources));
      }
    } catch(e) {answer.textContent=e.name==='TimeoutError'?'답변이 조금 늦어지고 있어요. 잠시 후 다시 물어봐 주세요.':e.message;}
    finally {questionPending=false;if(submit.isConnected)submit.disabled=false;}
  }

  function updateFavorites() {$('#saved-count').hidden=favorites.length===0;$('#saved-count').textContent=favorites.length;}
  function saveName(name) {
    if(favorites.includes(name)){toast('이미 관심 이름에 담겨 있어요.');return;}
    if(favorites.length>=12){toast('관심 이름은 열두 개까지 담을 수 있어요.');return;}
    favorites.push(name);
    try{localStorage.setItem('moa-favorite-names',JSON.stringify(favorites));}catch{favorites.pop();toast('브라우저 저장 권한을 확인해 주세요.');return;}
    updateFavorites();toast(`‘${name}’, 이 브라우저에 담아뒀어요.`);
  }
  function openInfo(title,content) {$('#info-body').innerHTML=`<h2 id="info-title">${title}</h2>${content}`;if(!info.open)info.showModal();syncBodyLock();}
  function showSaved() {
    openInfo('마음에 담아둔 이름',favorites.length?`<div>${favorites.map(n=>`<div class="saved-item"><button data-saved="${esc(n)}">${esc(n)}</button><button data-remove="${esc(n)}">지우기</button></div>`).join('')}</div><p style="margin-top:15px">관심 이름만 이 브라우저에 저장해요. 생일이나 질문은 함께 저장하지 않아요.</p>`:'<p class="empty-saved">아직 담아둔 이름이 없어요.<br>풀이에서 마음에 드는 이름을 담아보세요.</p>');
    $('[data-saved]',info)?.focus();
    info.querySelectorAll('[data-saved]').forEach(b=>b.addEventListener('click',()=>{info.close();openService('name',{profile:{name:b.dataset.saved}});}));
    info.querySelectorAll('[data-remove]').forEach(b=>b.addEventListener('click',()=>{favorites=favorites.filter(n=>n!==b.dataset.remove);try{localStorage.setItem('moa-favorite-names',JSON.stringify(favorites));}catch{}updateFavorites();showSaved();}));
  }
  $('#saved-trigger').addEventListener('click',showSaved);
  $('#privacy-trigger').addEventListener('click',()=>openInfo('내 정보는 어떻게 쓰이나요?','<p>입력한 이름과 생일은 요청한 풀이를 계산하고 설명하는 데 사용해요. 기본 구성에서는 풀이와 추가 질문의 맥락을 최대 30분 동안만 보관하고, 따로 회원 정보로 저장하지 않아요.<br><br>직접 담은 관심 이름은 이 브라우저에만 남아요. 관심 이름에서 언제든 지울 수 있어요. 생일이나 질문은 관심 이름과 함께 저장하지 않아요.</p>'));
  $('#method-trigger').addEventListener('click',()=>openInfo('쉬운 말에도, 참고 기준은 있어요.','<p>사주 계산과 별자리 위치는 별도 프로그램이 계산해요. 이름은 확인된 한자 뜻과 독음, 실제 소리 구성과 가족의 바람을 비교해요. 계산값과 공통 자료를 바탕으로 AI가 개인별 해설을 새로 작성합니다. 같은 아이의 사주는 공통으로 한 번 읽고, 이름별 뜻과 아쉬운 점은 따로 설명해요.<br><br>참고 자료와 계산 기준은 각 결과에서 확인할 수 있어요. 서로 다른 전통의 해석을 미래 예측의 정확도나 성공 확률로 바꾸지는 않아요.<br><br><a href="https://github.com/glee1228/korean_saju" target="_blank" rel="noopener noreferrer">사주 계산 기준</a> · <a href="https://github.com/cosinekitty/astronomy" target="_blank" rel="noopener noreferrer">별자리 위치 계산</a><br>공개 사주 지식: Dangamsoft CAFE Ontology · CC BY 4.0.<br><br><a href="./method.html" target="_blank" rel="noopener noreferrer">계산에서 풀이로 이어지는 상세 기준 ↗</a></p>'));
  $('#sample-trigger').addEventListener('click',async()=>{try{currentService='name';openDialog();const result=await namingExample();showResult(result,result.example_request||{service:'name',profile:{surname:'박',name:'지민',birth_date:'2026-05-15',birth_time:'10:30',city:'seoul',naming_preference:'wisdom'}});}catch{toast('이름 예시를 불러오지 못했어요.');}});
  async function openPairExample(kind='tension'){try{const r=await fetch('./assets/compatibility-'+kind+'-example.json');if(!r.ok)throw new Error();const result=await r.json();currentService='compatibility';openDialog();showResult(result,result.example_request);}catch{toast('궁합 예시를 불러오지 못했어요.');}}
  $('#stars-sample-trigger').addEventListener('click',async()=>{try{const r=await fetch('./assets/stars-example.json');if(!r.ok)throw Error();currentService='stars';openDialog();showResult(await r.json(),{service:'stars',profile:{name:'지민',birth_date:'2004-05-15',birth_time:'10:30',city:'seoul'}});}catch{toast('별자리 예시를 불러오지 못했어요.');}});
  $('#compatibility-sample-trigger').addEventListener('click',()=>openPairExample());
  $('#saju-sample-trigger').addEventListener('click',async()=>{try{const result=await sajuExample();currentService='saju';openDialog();showResult(result,result.example_request||{service:'saju',profile:{name:'지민',birth_date:'2004-05-15',birth_time:'10:30',city:'seoul',gender:'male'}});}catch{toast('예시를 불러오지 못했어요. 잠시 후 다시 확인해 주세요.');}});
  document.querySelectorAll('[data-service]').forEach(b=>b.addEventListener('click',()=>openService(b.dataset.service)));
  document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{
    document.querySelectorAll('[data-filter]').forEach(p=>{p.classList.toggle('active',p===b);p.setAttribute('aria-pressed',String(p===b));});
    document.querySelectorAll('[data-category]').forEach(c=>{c.hidden=b.dataset.filter!=='all'&&c.dataset.category!==b.dataset.filter;});
  }));
  updateFavorites();
})();
