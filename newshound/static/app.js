const $=id=>document.getElementById(id);
async function post(url){await fetch(url,{method:'POST'}); await refreshStatus();}
function fmt(t){if(!t)return '—';try{return new Date(t).toLocaleString()}catch{return t}}
async function refreshStatus(){
 const s=await (await fetch('/api/status')).json();
 $('runState').textContent=s.running?'RUNNING':'STOPPED'; $('runDot').className='dot'+(s.running?' on':'');
 $('bzState').textContent=s.benzinga||'—'; $('fhState').textContent=s.finnhub||'—'; $('avState').textContent=s.alphavantage||'—'; $('secState').textContent=s.sec||'—'; $('lastEvent').textContent=fmt(s.last_event);
}
function esc(s){return String(s??'').replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]))}
async function loadWatchlist(){
 const j=await (await fetch('/api/watchlist')).json(); $('watchTickers').value=(j.tickers||[]).join(',');
}
async function saveWatchlist(){
 const value=$('watchTickers').value;
 $('watchState').textContent='Applying…';
 const r=await fetch('/api/watchlist',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tickers:value})});
 const j=await r.json();
 $('watchTickers').value=(j.tickers||[]).join(','); $('watchState').textContent=j.ok?'Sources restarted':'Failed';
 await refreshStatus(); await refreshFeed();
}
async function clearFeed(){
 if(!confirm('Clear all intelligence currently displayed on the board? Evidence files will be preserved.'))return;
 await fetch('/api/feed/clear',{method:'POST'}); await refreshStatus(); await refreshFeed();
}
async function refreshFeed(){
 let q=new URLSearchParams({source:$('source').value,importance:$('importance').value});
 let items=await (await fetch('/api/feed?'+q)).json(); window.__nhFeed=items; $('count').textContent=items.length+' items';
 $('feed').innerHTML=items.map(e=>`<article class="card ${esc(e.importance)}">
 <div class="meta"><b class="importance">${esc(e.importance)}</b><span class="badge">${esc(e.source)}</span><span>${esc(e.category)}</span><span>${esc(fmt(e.received_at))}</span><span class="tickers">${esc((e.tickers||[]).join(' · '))}</span><span class="analyze-wrap ${activeThesisId===String(e.evidence_id)?'active':''}"><input class="analyze-toggle" type="checkbox" data-id="${esc(e.evidence_id)}" ${activeThesisId===String(e.evidence_id)?'checked':''} onchange="toggleAnalyze(this)"><label>ANALYZE</label></span></div>
 <div class="title">${esc(e.title)}</div>${e.summary?`<div class="summary">${esc(e.summary)}</div>`:''}
 <div class="evidence">Published ${esc(e.published_at||'—')} · Received ${esc(e.received_at)} · Evidence ${esc(e.evidence_id)}</div>
 ${e.url?`<div class="links"><a href="${esc(e.url)}" target="_blank" rel="noopener">OPEN SOURCE ↗</a></div>`:''}</article>`).join('') || '<div class="doctrine">Listening. No matching intelligence yet.</div>';
}
async function openSetup(){
 $('modal').classList.remove('hidden'); tab('sources');
 let c=await (await fetch('/api/setup')).json();
 $('bzEnabled').checked=c.benzinga_enabled;$('bzLanguage').value=c.benzinga_language_pref||'english';$('bzKey').placeholder=c.benzinga_key_set?'Saved key present — leave blank to preserve':'Enter Benzinga API key';
 $('fhEnabled').checked=c.finnhub_enabled;$('fhPoll').value=c.finnhub_poll_seconds||30;$('fhKey').placeholder=c.finnhub_key_set?'Saved key present — leave blank to preserve':'Enter Finnhub API key';
 $('avEnabled').checked=c.alphavantage_enabled;$('avPoll').value=c.alphavantage_poll_minutes||60;$('avKey').placeholder=c.alphavantage_key_set?'Saved key present — leave blank to preserve':'Enter Alpha Vantage API key';
 $('secEnabled').checked=c.sec_enabled;$('secUA').value=c.sec_user_agent||'';$('pollSeconds').value=c.poll_seconds||2;$('feedLimit').value=c.feed_limit||250;$('openaiModel').value=c.openai_model||'gpt-5.6-luna';$('openaiKey').placeholder=c.openai_key_set?'Saved key present — leave blank to preserve':'Enter OpenAI API key';
}
function closeSetup(){$('modal').classList.add('hidden')}
function tab(which){$('sourcesTab').classList.toggle('hidden',which!=='sources');$('updateTab').classList.toggle('hidden',which!=='update')}
async function saveSetup(){
 let p={benzinga_enabled:$('bzEnabled').checked,benzinga_api_key:$('bzKey').value,benzinga_language_pref:$('bzLanguage').value,
 finnhub_enabled:$('fhEnabled').checked,finnhub_api_key:$('fhKey').value,finnhub_poll_seconds:+$('fhPoll').value,
 alphavantage_enabled:$('avEnabled').checked,alphavantage_api_key:$('avKey').value,alphavantage_poll_minutes:+$('avPoll').value,
 sec_enabled:$('secEnabled').checked,sec_user_agent:$('secUA').value,poll_seconds:+$('pollSeconds').value,feed_limit:+$('feedLimit').value,openai_api_key:$('openaiKey').value,openai_model:$('openaiModel').value};
 let r=await fetch('/api/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(p)});let j=await r.json();alert(j.ok?'Saved. Sources restarted.':j.message||'Save failed');refreshStatus();
}
async function testBz(){let r=await fetch('/api/test/benzinga',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({benzinga_api_key:$('bzKey').value})});let j=await r.json();$('bzTest').textContent=j.message;}
async function testFh(){let r=await fetch('/api/test/finnhub',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({finnhub_api_key:$('fhKey').value})});let j=await r.json();$('fhTest').textContent=j.message;}
async function testAv(){let r=await fetch('/api/test/alphavantage',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({alphavantage_api_key:$('avKey').value})});let j=await r.json();$('avTest').textContent=j.message;}
async function testSec(){let r=await fetch('/api/test/sec',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({sec_user_agent:$('secUA').value})});let j=await r.json();$('secTest').textContent=j.message;}
async function uploadUpdate(){
 let f=$('updateFile').files[0];if(!f){$('updateResult').textContent='Select a ZIP first.';return}
 let d=new FormData();d.append('package',f);$('updateResult').textContent='Uploading / validating...';
 let r=await fetch('/api/update',{method:'POST',body:d});let j=await r.json();$('updateResult').textContent=j.message||JSON.stringify(j);
}

// hf12 — AI Thesis
let activeThesisId=null;
let activeThesisReceipt=null;
let activeSavedReportName=null;
function storyById(id){return window.__nhFeed?.find(x=>String(x.evidence_id)===String(id))}
function thesisField(label,value){return `<div class="thesis-section"><h4>${esc(label)}</h4><p>${esc(value||'—')}</p></div>`}
function renderThesis(receipt){
 activeThesisReceipt=receipt; activeSavedReportName=null; $('saveThesisBtn').classList.remove('hidden'); $('exportThesisBtn').classList.remove('hidden');
 const a=receipt.analysis||{}, s=receipt.story||{}, sources=receipt.web_sources||[];
 $('thesisStory').innerHTML=`${esc((s.tickers||[]).join(' · '))}${s.tickers?.length?' — ':''}${esc(s.title||'Selected intelligence')}<div class="evidence">${esc(s.source||'')} · analyzed ${esc(fmt(receipt.analyzed_at))}</div>`;
 $('thesisBody').innerHTML=
  thesisField('WHAT HAPPENED',a.what_happened)+thesisField("WHAT'S NEW",a.what_is_new)+thesisField('MARKET EXPECTATION',a.market_expectation)+
  thesisField('EXPECTATION DELTA',a.expectation_delta)+thesisField('ECONOMIC TRANSMISSION',a.economic_transmission)+thesisField('MAGNITUDE / MATERIALITY',a.magnitude_materiality)+
  thesisField('TIME HORIZON',a.time_horizon)+thesisField('DURABILITY',a.durability)+thesisField('EVIDENCE QUALITY',a.evidence_quality)+thesisField('WHO ELSE IS AFFECTED',a.affected_entities)+
  thesisField('COUNTER-THESIS',a.counter_thesis)+thesisField('INVALIDATION',a.invalidation)+thesisField('PRICE WOULD SUPPORT',a.price_support)+thesisField('PRICE WOULD CONTRADICT',a.price_contradiction)+
  thesisField('WORKING THESIS',a.working_thesis)+thesisField('WATCH FOR',a.watch_for)+
  `<div class="thesis-verdict"><div class="thesis-kicker">ANALYST VERDICT</div><div class="thesis-grid"><b>Bias</b><span>${esc(a.bias||'—')}</span><b>State</b><span>${esc(a.thesis_state||'—')}</span><b>Confidence</b><span>${esc(a.confidence??'—')}%</span><b>Source access</b><span>${esc(a.source_access||'—')}</span><b>Retrieval</b><span>${esc(a.retrieval_note||'—')}</span></div></div>`+
  (sources.length?`<div class="thesis-section thesis-sources"><h4>WEB EVIDENCE USED</h4>${sources.map(x=>`<a href="${esc(x.url)}" target="_blank" rel="noopener">${esc(x.title||x.url)}</a>`).join('')}</div>`:'')+
  `<button class="reanalyze" onclick="analyzeStory('${esc(receipt.evidence_id)}',true)">REANALYZE WITH FRESH EVIDENCE</button>`;
}
function openThesis(id){activeThesisId=String(id);document.querySelector('main').classList.add('thesis-open');$('thesisPane').classList.remove('hidden');document.querySelectorAll('.analyze-toggle').forEach(x=>{x.checked=x.dataset.id===activeThesisId;x.closest('.analyze-wrap')?.classList.toggle('active',x.checked)});}
function closeThesis(){activeThesisId=null;activeThesisReceipt=null;activeSavedReportName=null;$('saveThesisBtn').classList.add('hidden');$('exportThesisBtn').classList.add('hidden');$('thesisPane').classList.add('hidden');document.querySelector('main').classList.remove('thesis-open');document.querySelectorAll('.analyze-toggle').forEach(x=>{x.checked=false;x.closest('.analyze-wrap')?.classList.remove('active')});}
async function toggleAnalyze(el){if(!el.checked){closeThesis();return} await analyzeStory(el.dataset.id,false)}
async function analyzeStory(id,force=false){
 openThesis(id);activeThesisReceipt=null;activeSavedReportName=null;$('saveThesisBtn').classList.add('hidden');$('exportThesisBtn').classList.add('hidden');let story=storyById(id);$('thesisStory').textContent=story?.title||'Selected intelligence';$('thesisBody').innerHTML='<div class="thesis-loading">LUNA IS DEVELOPING THE THESIS…<br><span class="evidence">Retrieving evidence • testing counter-thesis • defining invalidation</span></div>';
 try{
  if(!force){let c=await fetch('/api/thesis/'+encodeURIComponent(id));if(c.ok){let cj=await c.json();if(activeThesisId===String(id))renderThesis(cj.receipt);return}}
  let r=await fetch('/api/thesis/'+encodeURIComponent(id),{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({force})});let j=await r.json();if(!r.ok||!j.ok)throw new Error(j.message||'Analysis failed');if(activeThesisId===String(id))renderThesis(j.receipt);
 }catch(e){if(activeThesisId===String(id))$('thesisBody').innerHTML=`<div class="thesis-error">${esc(e.message||e)}</div>`}
}

setInterval(()=>{refreshStatus();refreshFeed()},2000);refreshStatus();refreshFeed();loadWatchlist();


// hf14 — operator-designated finished intelligence products
async function loadSavedReports(){
 try{
  let r=await fetch('/api/reports?limit=12'),j=await r.json();let rows=j.reports||[];
  $('savedReportCount').textContent=rows.length+' recent';
  $('savedReports').innerHTML=rows.map(x=>`<div class="saved-report"><div class="saved-report-title">${esc((x.tickers||[]).join(' · '))}${x.tickers?.length?' — ':''}${esc(x.title||x.name)}</div><div class="saved-report-meta">${esc(fmt(x.saved_at))} · ${esc(x.source||'')}<br>${esc(x.name)}</div><div class="saved-report-actions"><a href="/api/reports/${encodeURIComponent(x.name)}/pdf">PDF</a><a href="/api/reports/${encodeURIComponent(x.name)}/json">JSON</a><button onclick="deleteSavedReport('${esc(x.name)}')">DELETE</button></div></div>`).join('')||'<div class="doctrine">No archived intelligence products yet.</div>';
 }catch(e){$('savedReports').innerHTML=`<div class="thesis-error">${esc(e.message||e)}</div>`}
}
async function saveThesisReport(downloadPdf=false){
 if(!activeThesisId||!activeThesisReceipt)return;
 if(downloadPdf&&activeSavedReportName){location.href='/api/reports/'+encodeURIComponent(activeSavedReportName)+'/pdf';return}
 let old=document.querySelector('.report-status');if(old)old.remove();
 let r=await fetch('/api/thesis/'+encodeURIComponent(activeThesisId)+'/report',{method:'POST'}),j=await r.json();
 if(!r.ok||!j.ok){let d=document.createElement('div');d.className='report-status error';d.textContent=j.message||'Report save failed';$('thesisStory').after(d);return}
 activeSavedReportName=j.report.name;
 let d=document.createElement('div');d.className='report-status';d.textContent='ARCHIVED — '+j.report.name;$('thesisStory').after(d);
 await loadSavedReports();
 if(downloadPdf) location.href='/api/reports/'+encodeURIComponent(j.report.name)+'/pdf';
}
async function deleteSavedReport(name){
 if(!confirm('Delete archived PDF and JSON receipt for this report?'))return;
 let r=await fetch('/api/reports/'+encodeURIComponent(name),{method:'DELETE'});if(r.ok)await loadSavedReports();
}
loadSavedReports();
