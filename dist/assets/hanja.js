(() => {
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let dictionary;
  const load=()=>dictionary||(dictionary=fetch('./assets/hanja-choices.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(d=>d.readings).catch(e=>{dictionary=null;throw e;}));
  function field(prefix='',profile={},kind='name') {
    const surname=kind==='surname',part=surname?'surname':'name',initial=profile[part+'_hanja']||'',statusId=prefix+(surname?'surname-':'')+'hanja-status';
    return `<fieldset class="hanja-picker" data-hanja-picker="${esc(prefix)}" data-hanja-kind="${part}" data-initial="${esc(initial)}"><legend>${surname?'성의 한자':'이름 한자'} <span class="optional">${surname?'선택':'선택 · 성 제외'}</span></legend><input type="hidden" id="${prefix}${part}-hanja" name="${prefix}${part}_hanja" value="${esc(initial)}"><div class="hanja-selects"></div><p class="hanja-status input-hint" id="${statusId}" role="status">${surname?'성을':'이름을'} 한글로 입력하면, 글자별로 한자를 고를 수 있어요.</p><button class="hanja-clear" type="button" hidden>한자 없이 보기</button><details class="hanja-dictionary-note"><summary>어떤 한자를 보여주나요?</summary><p>사전의 한글 독음에 맞는 한자를 보여줘요. 이름은 공식 조회 목록과 한국어 뜻이 확인된 글자가 먼저 나옵니다. 조회일 기준의 참고이며 최신 정보는 공식 조회에서 확인해 주세요.</p></details></fieldset>`;
  }
  function mount(form) {
    form.querySelectorAll('[data-hanja-picker]').forEach(picker=>{
      const prefix=picker.dataset.hanjaPicker,part=picker.dataset.hanjaKind||'name',surname=part==='surname',statusId=prefix+(surname?'surname-':'')+'hanja-status';
      const name=form.elements.namedItem(prefix+part);
      const hidden=form.elements.namedItem(prefix+part+'_hanja');
      const slots=picker.querySelector('.hanja-selects');
      const status=picker.querySelector('.hanja-status');
      const clear=picker.querySelector('.hanja-clear');
      let current=name.value.trim(),chosen=[...picker.dataset.initial],index,composing=false;
      function sync() {
        const letters=[...current],count=chosen.filter(Boolean).length;
        hidden.value=count===letters.length?chosen.join(''):'';
        picker.dataset.partial=String(count>0&&count<letters.length);
        clear.hidden=!count;
        status.textContent=count===letters.length&&count?`선택한 이름: ${current} (${hidden.value})`:count?`${letters.length}글자 중 ${count}글자를 골랐어요. 나머지도 선택하거나 ‘한자 없이 보기’를 눌러주세요.`:(surname?'성의 한자를 모르면 비워두어도 돼요.':'한자를 모르면 선택하지 않아도 돼요. 사주는 생일로 볼 수 있어요.');
      }
      function draw() {
        if(!picker.isConnected)return;
        if(!current||! /^[가-힣]{1,12}$/.test(current)) {
          slots.innerHTML='';hidden.value='';clear.hidden=true;picker.dataset.partial='false';
          status.textContent=(surname?'성을':'이름을')+' 한글로 입력하면, 글자별로 한자를 고를 수 있어요.';return;
        }
        if(!index){status.textContent='한자 후보를 불러오는 중이에요.';return;}
        slots.innerHTML=[...current].map((syllable,i)=>{
          const rows=index[syllable]||[];
          const groups=surname?[['뜻을 한글로 읽기',rows.filter(c=>c.m)],['다른 한자 · 한국어 뜻 미정리',rows.filter(c=>!c.m)]]:[['공식 독음·한국어 뜻 확인',rows.filter(c=>c.legal===true&&c.m)],['한국어 뜻 확인 · 공식 독음 추가 확인',rows.filter(c=>c.legal!==true&&c.m)],['다른 한자 · 원자료 뜻 확인',rows.filter(c=>!c.m)]];
          const old=chosen[i]&&!rows.some(c=>c.c===chosen[i])?`<option value="${esc(chosen[i])}" selected>${esc(chosen[i])} — 기존 입력 · 독음 확인 필요</option>`:'';
          const selected=rows.find(c=>c.c===chosen[i]);
          return `<div class="hanja-slot"><label for="${prefix}${part}-hanja-${i}"><b>${esc(syllable)}</b>에 쓸 한자</label><select id="${prefix}${part}-hanja-${i}" data-hanja-slot="${i}" aria-describedby="${statusId}"><option value="">선택 안 함</option>${old}${groups.filter(([,rs])=>rs.length).map(([label,rs])=>`<optgroup label="${label}">${rs.map(c=>`<option value="${esc(c.c)}" ${chosen[i]===c.c?'selected':''}>${esc(c.c)} — ${esc(c.m||'한국어 뜻 미정리')}${!surname&&c.legal===true?' · 공식 독음 확인':''}</option>`).join('')}</optgroup>`).join('')}</select><span class="hanja-choice-meaning">${selected?esc(selected.m||'사전 원문에서 뜻을 확인해 주세요.'):rows.length?'같은 소리라도 뜻이 달라요.':'현재 자료에서 이 독음의 후보를 확인하지 못했어요.'}</span>${selected&&!selected.m?`<details class="hanja-original"><summary>사전 원문 뜻</summary><p>${esc(selected.d||'등록된 뜻이 없어요.')}</p></details>`:''}</div>`;
        }).join('');sync();
        slots.querySelectorAll('select').forEach(select=>select.addEventListener('change',()=>{
          chosen[Number(select.dataset.hanjaSlot)]=select.value;
          // Update descriptions without replacing the select that currently has focus.
          const slot=select.closest('.hanja-slot'),row=(index[[...current][Number(select.dataset.hanjaSlot)]]||[]).find(c=>c.c===select.value);
          slot.querySelector('.hanja-choice-meaning').textContent=row?row.m||'사전 원문에서 뜻을 확인해 주세요.':'같은 소리라도 뜻이 달라요.';
          slot.querySelector('.hanja-original')?.remove();
          if(row&&!row.m)slot.insertAdjacentHTML('beforeend',`<details class="hanja-original"><summary>사전 원문 뜻</summary><p>${esc(row.d||'등록된 뜻이 없어요.')}</p></details>`);
          sync();
        }));
      }
      const update=()=>{const next=name.value.trim();if(next!==current){current=next;chosen=[];hidden.value='';}draw();};
      name.addEventListener('compositionstart',()=>{composing=true;});
      name.addEventListener('compositionend',()=>{composing=false;update();});
      name.addEventListener('input',()=>{if(!composing)update();});
      clear.addEventListener('click',()=>{chosen=[];draw();picker.querySelector('select')?.focus();});
      function fetchChoices(){draw();load().then(d=>{index=d;draw();}).catch(()=>{
        if(!picker.isConnected)return;
        slots.innerHTML='<button type="button" class="hanja-retry">후보 다시 불러오기</button>';
        status.textContent='한자 후보를 불러오지 못했어요. 다시 시도하거나 한글 이름으로 먼저 볼 수 있어요.';
        slots.querySelector('button').addEventListener('click',fetchChoices);
      });}
      fetchChoices();
    });
  }
  const validate=form=>form.querySelector('[data-partial="true"]')?'각 한자 선택란을 모두 선택하거나 해당 항목의 ‘한자 없이 보기’를 눌러주세요.':'';
  window.MoaHanja={field,mount,validate};
})();
