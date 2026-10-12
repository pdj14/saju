(() => {
  'use strict';
  const esc=v=>String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  let catalog;
  const ready=fetch('./assets/birthplaces.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(x=>{catalog=x;return true;}).catch(()=>false);
  function field(prefix,profile,required){
    const chosen=catalog.places.find(p=>p.id===profile.city);
    return `<fieldset class="birthplace-picker" data-place-prefix="${prefix}" data-place-initial="${esc(chosen?.id||'')}"><legend>태어난 지역 <span class="optional">국내 출생</span></legend><div class="form-row"><div class="form-field"><label for="${prefix}province">시·도</label><select id="${prefix}province"><option value="">지역 선택</option>${catalog.regions.map(r=>`<option value="${r.id}" ${chosen?.region===r.id?'selected':''}>${esc(r.label==='전남광주통합특별시'?'전남 · 광주':r.label)}</option>`).join('')}</select></div><div class="form-field"><label for="${prefix}city">시·군·구</label><select id="${prefix}city" ${required?'required':''}><option value="">시·도를 먼저 선택해 주세요</option></select></div></div><details class="place-detail" ${chosen?.locality?'open':''}><summary>읍·면·동까지 알고 있나요? <span class="optional">선택</span></summary><label class="sr-only" for="${prefix}locality">태어난 읍·면·동</label><select id="${prefix}locality"><option value="">시·군·구 대표지점 사용</option></select></details><input type="hidden" name="${prefix}city" value="${esc(chosen?.id||'')}"><p class="input-hint place-selection" aria-live="polite"></p><p class="input-hint">서울·경기·인천부터 모든 국내 지역을 선택할 수 있어요. 지역의 대표지점으로 시간을 보정하며, 읍·면·동을 더하면 범위를 좁힐 수 있어요. 행정구역이 바뀐 곳은 현재 지명으로 골라주세요. 해외 출생은 시간대 처리가 필요해 아직 지원하지 않아요.</p></fieldset>`;
  }
  function mount(form){
    form.querySelectorAll('.birthplace-picker').forEach(box=>{
      const prefix=box.dataset.placePrefix,province=box.querySelector(`#${prefix}province`),city=box.querySelector(`#${prefix}city`),locality=box.querySelector(`#${prefix}locality`),hidden=box.querySelector('input[type=hidden]'),note=box.querySelector('.place-selection'),birthDate=form.querySelector(`#${prefix}birth-date`);
      const selected=catalog.places.find(p=>p.id===box.dataset.placeInitial);
      function save(){
        hidden.value=locality.value||city.value;
        const p=catalog.places.find(p=>p.id===hidden.value);
        note.textContent=p?`선택한 출생지 · ${p.label} (${p.locality?'읍·면·동':'대표지점'} 기준)`:'태어난 곳을 골라주세요. 현재 사는 곳과 달라도 괜찮아요.';
        city.required=Boolean(birthDate?.required||birthDate?.value);province.required=city.required;
      }
      function towns(initial){
        const parent=catalog.places.find(p=>p.id===city.value);
        const options=parent?catalog.places.filter(p=>p.region===parent.region&&p.district===parent.district&&p.locality):[];
        locality.innerHTML='<option value="">시·군·구 대표지점 사용</option>'+options.map(p=>`<option value="${p.id}">${esc(p.locality)}</option>`).join('');
        if(initial&&options.some(p=>p.id===initial))locality.value=initial;
        locality.disabled=!parent||!options.length;save();
      }
      function districts(initial){
        const options=catalog.places.filter(p=>p.region===province.value&&!p.locality);
        city.innerHTML='<option value="">시·군·구 선택</option>'+options.map(p=>`<option value="${p.id}">${esc(p.label)}</option>`).join('');
        city.disabled=!province.value;
        if(initial){const parent=initial.locality?options.find(p=>p.district===initial.district):initial;if(parent)city.value=parent.id;}
        towns(initial?.locality?initial.id:null);
      }
      province.addEventListener('change',()=>districts());city.addEventListener('change',()=>towns());locality.addEventListener('change',save);birthDate?.addEventListener('input',save);
      districts(selected);
    });
  }
  window.MoaPlaces={ready,field,mount};
})();
