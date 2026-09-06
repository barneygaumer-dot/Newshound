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
 let items=await (await fetch('/api/feed?'+q)).json(); $('count').textContent=items.length+' items';
 $('feed').innerHTML=items.map(e=>`<article class="card ${esc(e.importance)}">
 <div class="meta"><b class="importance">${esc(e.importance)}</b><span class="badge">${esc(e.source)}</span><span>${esc(e.category)}</span><span>${esc(fmt(e.received_at))}</span><span class="tickers">${esc((e.tickers||[]).join(' · '))}</span></div>
 <div class="title">${esc(e.title)}</div>${e.summary?`<div class="summary">${esc(e.summary)}</div>`:''}
 <div class="evidence">Published ${esc(e.published_at||'—')} · Received ${esc(e.received_at)} · Evidence ${esc(e.evidence_id)}</div>
 ${e.url?`<div class="links"><a href="${esc(e.url)}" target="_blank" rel="noopener">OPEN SOURCE ↗</a></div>`:''}</article>`).join('') || '<div class="doctrine">Listening. No matching intelligence yet.</div>';
}
async function openSetup(){
 $('modal').classList.remove('hidden'); tab('sources');
 let c=await (await fetch('/api/setup')).json();
 $('bzEnabled').checked=c.benzinga_enabled;$('bzKey').placeholder=c.benzinga_key_set?'Saved key present — leave blank to preserve':'Enter Benzinga API key';
 $('fhEnabled').checked=c.finnhub_enabled;$('fhPoll').value=c.finnhub_poll_seconds||30;$('fhKey').placeholder=c.finnhub_key_set?'Saved key present — leave blank to preserve':'Enter Finnhub API key';
 $('avEnabled').checked=c.alphavantage_enabled;$('avPoll').value=c.alphavantage_poll_minutes||60;$('avKey').placeholder=c.alphavantage_key_set?'Saved key present — leave blank to preserve':'Enter Alpha Vantage API key';
 $('secEnabled').checked=c.sec_enabled;$('secUA').value=c.sec_user_agent||'';$('pollSeconds').value=c.poll_seconds||2;$('feedLimit').value=c.feed_limit||250;
}
function closeSetup(){$('modal').classList.add('hidden')}
function tab(which){$('sourcesTab').classList.toggle('hidden',which!=='sources');$('updateTab').classList.toggle('hidden',which!=='update')}
async function saveSetup(){
 let p={benzinga_enabled:$('bzEnabled').checked,benzinga_api_key:$('bzKey').value,
 finnhub_enabled:$('fhEnabled').checked,finnhub_api_key:$('fhKey').value,finnhub_poll_seconds:+$('fhPoll').value,
 alphavantage_enabled:$('avEnabled').checked,alphavantage_api_key:$('avKey').value,alphavantage_poll_minutes:+$('avPoll').value,
 sec_enabled:$('secEnabled').checked,sec_user_agent:$('secUA').value,poll_seconds:+$('pollSeconds').value,feed_limit:+$('feedLimit').value};
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
setInterval(()=>{refreshStatus();refreshFeed()},2000);refreshStatus();refreshFeed();loadWatchlist();
