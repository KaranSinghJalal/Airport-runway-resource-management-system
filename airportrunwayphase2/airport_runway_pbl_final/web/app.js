const $ = (id) => document.getElementById(id);
let dashboard = {flights:[], runways:[], logs:[], counts:{}};
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, body) {
  const res = await fetch(path, body === undefined ? {headers:{'Accept':'application/json'}} : {method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(body)});
  const data = await res.json().catch(()=>({error:'The server returned an unreadable response.'}));
  if (!res.ok) throw new Error(data.error || 'Request failed.');
  return data;
}
function toast(message){const el=$('toast');el.textContent=message;el.classList.add('show');clearTimeout(toast.timer);toast.timer=setTimeout(()=>el.classList.remove('show'),3200)}
function flash(message, error=false){const el=$('flash');el.textContent=message;el.className='flash '+(error?'error':'success');}
function fmtDate(v){if(!v)return 'Just now';return String(v)}
function renderFlights(){
 const q=$('flightSearch').value.trim().toLowerCase(), filter=$('statusFilter').value;
 const list=dashboard.flights.filter(f=>(filter==='all'||f.status===filter)&&[f.flight_code,f.destination,f.aircraft].some(v=>String(v).toLowerCase().includes(q)));
 $('flightRows').innerHTML=list.length?list.map(f=>`<tr><td><div class="flight-code">${esc(f.flight_code)}</div><div class="flight-dest">${esc(f.destination)} · ${esc(f.aircraft)}</div></td><td><span class="badge priority-${esc(f.priority)}">${esc(f.priority)}</span></td><td>${f.runway_code?`<b>${esc(f.runway_code)}</b>`:`<span style="color:#a1aaba">—</span>`}<div class="flight-dest">${esc(f.required_length_m)} m required</div></td><td><span class="badge status-${esc(f.status)}">${esc(f.status)}</span></td><td>${f.status==='assigned'?`<button class="action-btn" data-complete="${f.id}">Complete</button>`:f.status==='waiting'?`<button class="action-btn danger" data-cancel="${f.id}">Cancel</button>`:'—'}</td></tr>`).join(''):'<tr><td colspan="5" class="empty">No matching flights found.</td></tr>';
 $('flightSummary').textContent=`Showing ${list.length} of ${dashboard.flights.length} flights`;
}
function renderRunways(){
 $('runwayList').innerHTML=dashboard.runways.map(r=>{const f=dashboard.flights.find(x=>x.id===r.current_flight_id);const busy=r.status==='occupied';const max=Math.max(...dashboard.runways.map(x=>x.length_m),1);return `<div class="runway-card"><div class="runway-head"><div><div class="runway-name">${esc(r.code)}</div><div class="runway-desc">${esc(r.description)}</div></div><div class="runway-length">${esc(r.length_m.toLocaleString())} m</div></div><div class="runway-track"><div class="runway-fill ${busy?'busy':''}" style="width:${Math.max(10,Math.round(r.length_m/max*100))}%"></div></div><div class="runway-state"><span>${busy&&f?`Flight ${esc(f.flight_code)}`:'Ready for assignment'}</span><b class="${busy?'busy-text':''}">${busy?'OCCUPIED':'AVAILABLE'}</b></div></div>`}).join('')||'<div class="empty">No runway resources found.</div>';
 $('availableCount').textContent=dashboard.runways.filter(r=>r.status==='available').length;$('runwayFoot').textContent=`${dashboard.runways.length} total runway resources`;
}
function renderActivity(){const symbols={RUNWAY_ASSIGNED:'↗',FLIGHT_COMPLETED:'✓',FLIGHT_ADDED:'＋',FLIGHT_CANCELLED:'×',SYSTEM_READY:'✦',DEMO_RESET:'↻'};$('activityList').innerHTML=dashboard.logs.length?dashboard.logs.map(a=>`<div class="activity-item"><div class="activity-symbol">${symbols[a.event]||'•'}</div><div><b>${esc(a.event.replaceAll('_',' '))}</b><p>${esc(a.details)}</p><time>${esc(fmtDate(a.created_at))}</time></div></div>`).join(''):'<div class="empty">No activity recorded yet.</div>'}
function render(){ $('waitingCount').textContent=dashboard.counts.waiting??0;$('assignedCount').textContent=dashboard.counts.assigned??0;$('completedCount').textContent=dashboard.counts.completed??0;renderFlights();renderRunways();renderActivity(); }
async function refresh(){try{dashboard=await api('/api/dashboard');render()}catch(e){toast(e.message)}}
$('refreshBtn').addEventListener('click',refresh);$('flightSearch').addEventListener('input',renderFlights);$('statusFilter').addEventListener('change',renderFlights);
$('addFlightToggle').addEventListener('click',()=>{$('flightForm').classList.toggle('hidden');if(!$('flightForm').classList.contains('hidden'))$('flightForm').elements.flight_code.focus()});
$('cancelFormBtn').addEventListener('click',()=>$('flightForm').classList.add('hidden'));
$('flightForm').addEventListener('submit',async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;try{const fd=new FormData(e.currentTarget);const data=Object.fromEntries(fd.entries());data.required_length_m=Number(data.required_length_m);const r=await api('/api/flights',data);e.currentTarget.reset();$('flightForm').classList.add('hidden');await refresh();toast(r.message)}catch(err){toast(err.message)}finally{btn.disabled=false}});
$('scheduleBtn').addEventListener('click',async()=>{const b=$('scheduleBtn');b.disabled=true;try{const r=await api('/api/schedule',{});flash(r.message);await refresh();toast(r.message)}catch(e){flash(e.message,true)}finally{b.disabled=false}});
$('flightRows').addEventListener('click',async e=>{const c=e.target.closest('[data-complete]'),x=e.target.closest('[data-cancel]');if(!c&&!x)return;const data=c?{flight_id:Number(c.dataset.complete)}:{flight_id:Number(x.dataset.cancel)};try{const r=await api(c?'/api/complete':'/api/cancel',data);await refresh();toast(r.message)}catch(err){toast(err.message)}});
$('resetBtn').addEventListener('click',async()=>{if(!confirm('Restore the initial demo flights and release all runways? This will reset the local demo data.'))return;try{const r=await api('/api/reset-demo',{});await refresh();flash(r.message);toast(r.message)}catch(e){toast(e.message)}});
refresh();


// Operating Systems lab UI: process table, CPU scheduling, semaphores and kernel event trace.
let osSnapshot = null;
async function refreshOS(){
  try{ osSnapshot=await api('/api/os'); renderOS(); }
  catch(e){ toast('OS lab: '+e.message); }
}
function renderOS(){
 if(!osSnapshot)return;
 const m=osSnapshot.metrics||{}, counts=osSnapshot.counts||{};
 $('osProcessCount').textContent=m.process_count??0; $('osReadyCount').textContent=m.ready_queue_size??0; $('osRunCount').textContent=m.scheduler_runs??0;
 const procs=osSnapshot.processes||[];
 $('osProcessRows').innerHTML=procs.length?procs.map(p=>`<tr><td><b>PID ${p.pid}</b><div class="flight-dest">${esc(p.name)}</div></td><td>${p.burst} units<div class="flight-dest">Remaining: ${p.remaining}</div></td><td><span class="badge priority-${esc(p.priority)}">${esc(p.priority)}</span></td><td><span class="os-state state-${esc(p.state.toLowerCase())}">${esc(p.state)}</span></td><td>${p.state==='TERMINATED'?'—':`<button class="action-btn danger" data-os-terminate="${p.pid}">Terminate</button>`}</td></tr>`).join(''):'<tr><td colspan="5" class="empty">No processes yet. Create one above to populate the process table.</td></tr>';
 const resources=osSnapshot.resources||[];
 $('osResources').innerHTML=resources.map(r=>`<article class="os-resource ${r.available?'resource-free':'resource-busy'}"><div class="os-resource-top"><b>${esc(r.name)}</b><span>${r.available?'AVAILABLE':'LOCKED'}</span></div><div class="os-resource-owner">${r.available?'No process owns this resource':'Owner: '+esc(r.owner)}</div><div class="os-resource-actions">${r.available?`<input aria-label="Owner for ${esc(r.name)}" id="owner-${esc(r.name)}" placeholder="Process label (e.g. P1001)" maxlength="40"><button class="btn btn-primary" data-os-acquire="${esc(r.name)}">Acquire</button>`:`<button class="btn btn-quiet" data-os-release="${esc(r.name)}" data-owner="${esc(r.owner)}">Release resource</button>`}</div><small>Semaphore permits: ${r.semaphore_permits}</small></article>`).join('');
 $('osEventList').innerHTML=(osSnapshot.events||[]).length?osSnapshot.events.map(e=>`<div class="os-event"><span class="os-event-dot"></span><div><b>${esc(e.event.replaceAll('_',' '))}</b><p>${esc(e.details)}</p><time>${new Date(e.time*1000).toLocaleTimeString()}</time></div></div>`).join(''):'<div class="empty">No kernel events recorded.</div>';
}
$('osProcessForm').addEventListener('submit',async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const data=Object.fromEntries(fd.entries());data.burst=Number(data.burst);try{const r=await api('/api/os/process',data);toast(r.message);e.currentTarget.reset();await refreshOS()}catch(err){toast(err.message)}});
$('osSchedulerForm').addEventListener('submit',async e=>{e.preventDefault();const fd=new FormData(e.currentTarget);const data=Object.fromEntries(fd.entries());data.quantum=Number(data.quantum);const box=$('osSchedulerResult');try{const r=await api('/api/os/simulate',data);const bars=r.timeline||[];const max=Math.max(...bars.map(x=>x.end),1);box.innerHTML=`<div class="os-result-head"><b>${esc(r.algorithm)} complete</b><span>${bars.length} CPU slices</span></div><p>${esc(r.message)}</p><div class="gantt-labels"><span>0</span><span>${max} CPU units</span></div><div class="gantt">${bars.map(x=>`<div class="gantt-bar" style="flex:${Math.max(x.units,0.3)}" title="${esc(x.name)}: ${x.start}–${x.end}"><b>${esc(x.name)}</b><small>${x.start}–${x.end}</small></div>`).join('')}</div><div class="os-average-grid"><div><span>Average waiting</span><b>${r.averages.waiting}</b></div><div><span>Average turnaround</span><b>${r.averages.turnaround}</b></div><div><span>Total CPU units</span><b>${r.total_cpu_units??0}</b></div></div><p class="muted">Timeline uses simulated CPU units, not real elapsed time.</p>`;await refreshOS();toast('CPU scheduling simulation completed.')}catch(err){toast(err.message)}});
$('osProcessRows').addEventListener('click',async e=>{const b=e.target.closest('[data-os-terminate]');if(!b)return;try{const r=await api('/api/os/terminate',{pid:Number(b.dataset.osTerminate)});toast(r.message);await refreshOS()}catch(err){toast(err.message)}});
$('osResources').addEventListener('click',async e=>{const a=e.target.closest('[data-os-acquire]'),r=e.target.closest('[data-os-release]');if(!a&&!r)return;try{let out;if(a){const input=$('owner-'+a.dataset.osAcquire);out=await api('/api/os/resource/acquire',{runway:a.dataset.osAcquire,owner:input.value.trim()})}else{out=await api('/api/os/resource/release',{runway:r.dataset.osRelease,owner:r.dataset.owner})}toast(out.message);await refreshOS()}catch(err){toast(err.message);await refreshOS()}});
$('osResetBtn').addEventListener('click',async()=>{if(!confirm('Clear all simulated OS processes? This does not reset airport flight records.'))return;try{const r=await api('/api/os/reset',{});$('osSchedulerResult').innerHTML='<b>Process table reset</b><p>Create new processes to run another scheduling simulation.</p>';toast(r.message);await refreshOS()}catch(err){toast(err.message)}});
$('osRefreshBtn').addEventListener('click',refreshOS);
// Add navigation active-state behavior for section links.
document.querySelectorAll('.sidebar .nav').forEach(link=>link.addEventListener('click',()=>{document.querySelectorAll('.sidebar .nav').forEach(x=>x.classList.remove('active'));link.classList.add('active')}));
refreshOS();
