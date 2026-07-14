const CANDIDATE_KEY='bld-research-candidates-v1';
const escapeHtml=value=>String(value??'').replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
let queue=[], catalog=null, candidates=JSON.parse(localStorage.getItem(CANDIDATE_KEY)||'null');
const $=selector=>document.querySelector(selector);
const save=()=>localStorage.setItem(CANDIDATE_KEY,JSON.stringify(candidates));

async function init(){
  try{let seeded;[queue,catalog,seeded]=await Promise.all([fetch('data/research-queue.json').then(r=>r.json()),fetch('data/catalog.json').then(r=>r.json()),fetch('data/candidate-reviews.json').then(r=>r.json())]);if(!candidates)candidates=seeded.candidates||[];bind();render();}
  catch(error){$('#researchRoot').innerHTML=`<div class="notice">Could not load research data: ${escapeHtml(error.message)}</div>`;}
}
function bind(){
  $('#researchRoot').addEventListener('click',event=>{const button=event.target.closest('[data-add]');if(button)openForm(button.dataset.add);});
  $('[data-close]').addEventListener('click',()=>$('#candidateDialog').close());
  $('#candidateForm').addEventListener('submit',event=>{event.preventDefault();const data=Object.fromEntries(new FormData(event.target));data.id=`candidate_${crypto.randomUUID()}`;data.retrieval_date=new Date().toISOString().slice(0,10);data.asset_hash='';data.review_status='pending';candidates.push(data);save();event.target.reset();$('#candidateDialog').close();render();});
  $('#exportCandidates').addEventListener('click',()=>{const blob=new Blob([JSON.stringify({schema_version:'1.0.0',exported_at:new Date().toISOString(),candidates},null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='candidate-reviews.json';a.click();URL.revokeObjectURL(url);});
  $('#clearCandidates').addEventListener('click',()=>{if(confirm('Clear locally saved research candidates?')){candidates=[];save();render();}});
}
function openForm(id){$('#candidateForm').elements.record_id.value=id;$('#candidateDialog').showModal();}
function render(){
  $('#queueSummary').textContent=`${queue.length} records prioritized · ${candidates.length} locally recorded candidates`;
  $('#researchRoot').innerHTML=`<table class="research-table"><thead><tr><th>Priority</th><th>Photograph</th><th>Reason and search terms</th><th>Candidates</th><th></th></tr></thead><tbody>${queue.map(item=>{const record=catalog.records.find(r=>r.id===item.record_id);const found=candidates.filter(c=>c.record_id===item.record_id);return `<tr><td><span class="priority">${item.priority}</span></td><td><strong>${escapeHtml(item.title)}</strong><br><small>${escapeHtml(item.record_id)} · ${record?.print_viability.classification||''}</small></td><td>${escapeHtml(item.reason)}<br><small>${escapeHtml((item.search_terms||[]).join(', '))}</small></td><td><div class="candidate-list">${found.length?found.map(c=>`<div class="candidate"><strong>${escapeHtml(c.institution)}</strong> · ${escapeHtml(c.match_classification)} · ${escapeHtml(c.rights_status)}<br><a href="${escapeHtml(c.source_page)}" target="_blank" rel="noopener">Source page</a> · retrieved ${escapeHtml(c.retrieval_date)}</div>`).join(''):'None yet'}</div></td><td><button class="secondary-button" data-add="${item.record_id}">Add candidate</button></td></tr>`}).join('')}</tbody></table>`;
}
init();
