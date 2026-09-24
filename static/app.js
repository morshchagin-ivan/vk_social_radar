const state = { people: [], settings: {} };
const titles = {
  overview:["Обзор","Ключевые изменения социальных связей"],
  people:["Люди","Единая карточка контактов и их активности"],
  messages:["Сообщения","Количество, частота и инициатива общения"],
  dialogs:["Диалоги","Последние контакты из VK Messenger"],
  changes:["Изменения","Кто добавился, удалился или отписался"],
  collector:["Сбор из VK","Отдельный Chromium и предварительный просмотр"],
  import:["Импорт данных","Файлы и снимки остаются локально"],
  ai:["ИИ-анализ","Интерпретация метрик через LM Studio"],
  settings:["Настройки","Локальный сервер моделей и параметры анализа"],
};

function esc(v){return String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;").replaceAll("'","&#039;");}
function safeHref(v){try{const u=new URL(String(v));if(!["https:","http:"].includes(u.protocol)||u.username||u.password)return"#";return esc(u.href);}catch(_){return"#";}}
async function api(path,options={}){const r=await fetch(path,options);if(!r.ok){let d=`${r.status} ${r.statusText}`;try{d=(await r.json()).detail||d}catch(_){}throw new Error(d)}return r.json();}
function openView(name){document.querySelectorAll(".view").forEach(v=>v.classList.remove("active"));document.querySelectorAll(".nav-item").forEach(b=>b.classList.remove("active"));document.querySelector(`#view-${name}`).classList.add("active");document.querySelector(`.nav-item[data-view="${name}"]`).classList.add("active");document.querySelector("#page-title").textContent=titles[name][0];document.querySelector("#page-subtitle").textContent=titles[name][1];}
function metric(l,v,d,c="neutral"){return `<article class="metric"><div class="metric-label">${esc(l)}</div><div class="metric-value">${esc(v)}</div><div class="metric-delta ${c}">${esc(d)}</div></article>`;}
function eventLabel(t){return ({friend_added:"Новый друг",friend_removed:"Удалился из друзей",follower_added:"Новый подписчик",follower_removed:"Отписался",friend_to_follower:"Друг → подписчик"})[t]||t;}
function eventClass(t){if(t.includes("added"))return"good";if(t.includes("removed"))return"bad";return"";}

async function loadDashboard(){const d=await api("/api/dashboard");document.querySelector("#metric-grid").innerHTML=[
metric("Друзья",d.friends.current,`+${d.friends.added} / −${d.friends.removed}`,d.friends.removed?"negative":"positive"),
metric("Подписчики",d.followers.current,`+${d.followers.added} / −${d.followers.removed}`,d.followers.removed?"negative":"positive"),
metric("Сообщения",d.message_total,"за загруженные периоды"),metric("Импорты",d.recent_imports.length,"последние задания")].join("");
document.querySelector("#overview-changes").innerHTML=d.changes.length?d.changes.map(i=>`<div class="list-item"><div><div class="list-title">${esc(i.full_name)}</div><div class="list-meta">${esc(i.details||i.event_date)}</div></div><span class="badge ${eventClass(i.event_type)}">${esc(eventLabel(i.event_type))}</span></div>`).join(""):`<div class="empty">Изменений пока нет</div>`;
document.querySelector("#top-people").innerHTML=d.top_people.map(i=>`<div class="list-item"><div><div class="list-title">${esc(i.full_name)}</div><div class="list-meta">${esc(i.active_days)} активных дней · ответ ${esc(i.median_reply_minutes??"—")} мин</div></div><span class="badge">${esc(i.total_messages)} сообщений</span></div>`).join("");}

async function loadPeople(){state.people=await api("/api/people");renderPeople();renderAIPeople();}
function renderPeople(){const q=document.querySelector("#people-search").value.trim().toLowerCase();const rows=state.people.filter(p=>p.full_name.toLowerCase().includes(q));document.querySelector("#people-table-wrap").innerHTML=`<table><thead><tr><th>Человек</th><th>Статус</th><th>Сообщения</th><th>Активные дни</th><th>Медиана ответа</th></tr></thead><tbody>${rows.map(p=>`<tr class="clickable" data-person-id="${esc(p.id)}"><td><strong>${esc(p.full_name)}</strong></td><td>${p.is_friend?'<span class="badge good">Друг</span>':""} ${p.is_follower?'<span class="badge">Подписчик</span>':""}</td><td>${esc(p.total_messages)}</td><td>${esc(p.active_days)}</td><td>${esc(p.median_reply_minutes??"—")} мин</td></tr>`).join("")}</tbody></table>`;document.querySelectorAll("[data-person-id]").forEach(r=>r.onclick=()=>openPerson(Number(r.dataset.personId)));}

async function openPerson(id){const d=await api(`/api/people/${id}`),p=d.person,s=d.message_stats[0]||{},total=(s.incoming_count||0)+(s.outgoing_count||0),starts=(s.initiated_by_person||0)+(s.initiated_by_me||0),initiative=starts?Math.round(100*s.initiated_by_person/starts):0;let insight="";if(d.insights?.length){const x=d.insights[0];insight=`<div class="insight-box"><strong>Последний ИИ-вывод: ${esc(x.status)}</strong><p>${esc(x.summary)}</p><small>${esc(x.model)} · уверенность ${Math.round(x.confidence*100)}%</small></div>`;}
document.querySelector("#person-detail").innerHTML=`<h2>${esc(p.full_name)}</h2><p><a href="${safeHref(p.profile_url||"#")}" target="_blank" rel="noopener noreferrer">Открыть профиль VK</a></p><div class="detail-grid"><div class="detail-card"><span>Сообщений</span><strong>${total}</strong></div><div class="detail-card"><span>Активных дней</span><strong>${esc(s.active_days??0)}</strong></div><div class="detail-card"><span>Инициатива человека</span><strong>${initiative}%</strong></div></div><h3>Баланс</h3><p>Входящие: <strong>${esc(s.incoming_count??0)}</strong> · Исходящие: <strong>${esc(s.outgoing_count??0)}</strong></p>${insight}<h3>События</h3><div class="list">${d.events.length?d.events.map(e=>`<div class="list-item"><div><div class="list-title">${esc(eventLabel(e.event_type))}</div><div class="list-meta">${esc(e.details||"")}</div></div><span>${esc(e.event_date)}</span></div>`).join(""):'<div class="empty">Событий нет</div>'}</div>`;document.querySelector("#person-dialog").showModal();}

async function loadMessages(){const rows=await api("/api/messages/leaderboard");document.querySelector("#messages-table-wrap").innerHTML=`<table><thead><tr><th>Человек</th><th>Всего</th><th>Входящие</th><th>Исходящие</th><th>Активные дни</th><th>Инициатива</th><th>Медиана ответа</th></tr></thead><tbody>${rows.map(i=>`<tr><td><strong>${esc(i.full_name)}</strong></td><td>${esc(i.total_messages)}</td><td>${esc(i.incoming_count)}</td><td>${esc(i.outgoing_count)}</td><td>${esc(i.active_days)}</td><td>${esc(i.person_initiative_pct)}%</td><td>${esc(i.median_reply_minutes??"—")} мин</td></tr>`).join("")}</tbody></table>`;}
async function loadChanges(){const rows=await api("/api/changes");document.querySelector("#changes-list").innerHTML=rows.length?rows.map(i=>`<div class="list-item"><div><div class="list-title">${esc(i.full_name)}</div><div class="list-meta">${esc(i.details||"")} · ${esc(i.event_date)}</div></div><span class="badge ${eventClass(i.event_type)}">${esc(eventLabel(i.event_type))}</span></div>`).join(""):'<div class="empty">Журнал пока пуст</div>';}

function renderAIPeople(){document.querySelector("#ai-people").innerHTML=state.people.map(p=>`<article class="person-card"><h3>${esc(p.full_name)}</h3><p>${esc(p.total_messages)} сообщений · ${esc(p.active_days)} активных дней</p><div class="actions"><span class="badge">${p.is_friend?"Друг":p.is_follower?"Подписчик":"Контакт"}</span><button class="primary ai-run" data-ai-person="${esc(p.id)}">Анализировать</button></div><div id="ai-result-${esc(p.id)}"></div></article>`).join("");document.querySelectorAll(".ai-run").forEach(b=>b.onclick=()=>runInsight(Number(b.dataset.aiPerson),b));}
async function runInsight(id,button){const box=document.querySelector(`#ai-result-${id}`);button.disabled=true;button.innerHTML='<span class="spinner"></span>';box.innerHTML="";try{const x=await api(`/api/people/${id}/insight`,{method:"POST"});box.innerHTML=`<div class="insight-box"><strong>${esc(x.status)} · ${Math.round(x.confidence*100)}%</strong><p>${esc(x.summary)}</p><ul>${x.evidence.map(e=>`<li>${esc(e)}</li>`).join("")}</ul>${x.cautions.length?`<small>Ограничения: ${esc(x.cautions.join("; "))}</small>`:""}</div>`;}catch(e){box.innerHTML=`<div class="insight-box negative">Ошибка: ${esc(e.message)}</div>`;}finally{button.disabled=false;button.textContent="Анализировать";}}

async function loadSettings(){state.settings=await api("/api/settings");document.querySelector("#lm-base-url").value=state.settings.lmstudio_base_url||"http://127.0.0.1:1234/v1";document.querySelector("#lm-temperature").value=state.settings.lmstudio_temperature||"0.2";await loadModels(false);}
async function loadModels(showStatus=true){const sel=document.querySelector("#lm-model"),status=document.querySelector("#settings-status");try{const models=await api("/api/lmstudio/models");const current=state.settings.lmstudio_model||"";sel.innerHTML='<option value="">Автовыбор первой доступной</option>'+models.map(m=>`<option value="${esc(m.id)}" ${m.id===current?"selected":""}>${esc(m.id)}</option>`).join("");document.querySelector("#ai-status").textContent=`LM Studio доступна. Моделей: ${models.length}.`;document.querySelector("#ai-status").className="notice positive";if(showStatus){status.textContent=`Найдено моделей: ${models.length}`;status.className="positive";}}catch(e){document.querySelector("#ai-status").textContent=`LM Studio недоступна: ${e.message}`;document.querySelector("#ai-status").className="notice negative";if(showStatus){status.textContent=e.message;status.className="negative";}}}

async function refreshAll(){await Promise.all([loadDashboard(),loadPeople(),loadMessages(),loadChanges()]);}

document.querySelectorAll(".nav-item").forEach(b=>b.onclick=()=>openView(b.dataset.view));
document.querySelectorAll("[data-open-view]").forEach(b=>b.onclick=()=>openView(b.dataset.openView));
document.querySelector("#refresh-btn").onclick=refreshAll;
document.querySelector("#people-search").oninput=renderPeople;
document.querySelector("#dialog-close").onclick=()=>document.querySelector("#person-dialog").close();
document.querySelector("#snapshot-date").valueAsDate=new Date();
document.querySelector("#file-snapshot-date").valueAsDate=new Date();

document.querySelector("#import-btn").onclick=async()=>{const s=document.querySelector("#import-status");s.textContent="Импорт...";try{const payload={relation_type:document.querySelector("#relation-type").value,snapshot_date:document.querySelector("#snapshot-date").value,people:JSON.parse(document.querySelector("#snapshot-json").value)};const r=await api("/api/import/snapshot",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(payload)});s.textContent=`Готово: ${r.count}, +${r.added}, −${r.removed}`;s.className="positive";await refreshAll();}catch(e){s.textContent=`Ошибка: ${e.message}`;s.className="negative";}};

document.querySelector("#file-import-type").onchange=(e)=>{document.querySelector("#file-relation-type").disabled=e.target.value!=="relations";};
document.querySelector("#file-import-btn").onclick=async()=>{const s=document.querySelector("#file-import-status"),f=document.querySelector("#import-file").files[0];if(!f){s.textContent="Выберите файл";s.className="negative";return;}const form=new FormData();form.append("file",f);form.append("import_type",document.querySelector("#file-import-type").value);form.append("relation_type",document.querySelector("#file-relation-type").value);form.append("snapshot_date",document.querySelector("#file-snapshot-date").value);s.textContent="Обработка...";try{const r=await api("/api/import/file",{method:"POST",body:form});s.textContent=`Готово: ${r.count??r.imported??0} записей`;s.className="positive";await refreshAll();}catch(e){s.textContent=`Ошибка: ${e.message}`;s.className="negative";}};

document.querySelector("#settings-save-btn").onclick=async()=>{const s=document.querySelector("#settings-status");try{state.settings=await api("/api/settings",{method:"PUT",headers:{"Content-Type":"application/json"},body:JSON.stringify({lmstudio_base_url:document.querySelector("#lm-base-url").value,lmstudio_model:document.querySelector("#lm-model").value,lmstudio_temperature:document.querySelector("#lm-temperature").value})});s.textContent="Сохранено";s.className="positive";}catch(e){s.textContent=e.message;s.className="negative";}};
document.querySelector("#lm-test-btn").onclick=()=>loadModels(true);
document.querySelector("#ai-refresh-btn").onclick=()=>loadModels(true);

Promise.all([refreshAll(),loadSettings()]).catch(e=>{console.error(e);alert(`Ошибка запуска интерфейса: ${e.message}`);});


async function updateCollectorStatus(){
  try{
    const s=await api("/api/collector/status");
    const badge=document.querySelector("#collector-state-badge");
    badge.textContent=s.status==="running"?(s.authenticated?"Запущен · вход OK":"Запущен · нужен вход"):"Остановлен";
    badge.className=`badge ${s.authenticated?"good":""}`;
    document.querySelector("#collector-status").innerHTML=
      `<strong>Статус:</strong> ${esc(s.status)}<br>`+
      `<strong>Авторизация:</strong> ${s.authenticated?"OK":"не подтверждена"}<br>`+
      `<strong>URL:</strong> ${esc(s.current_url||"—")}`+
      (s.last_error?`<br><span class="negative"><strong>Ошибка:</strong> ${esc(s.last_error)}</span>`:"")+
      (s.blocked_hosts?.length?`<br><strong>Заблокированные внешние хосты:</strong> ${esc(s.blocked_hosts.slice(0,8).join(", "))}`:"");
  }catch(e){
    document.querySelector("#collector-status").textContent=`Ошибка статуса: ${e.message}`;
  }
}

function renderCollectorPreview(p){
  const report=p.report||{};
  document.querySelector("#collector-report").innerHTML=
    `<div class="report-grid">`+
    Object.entries(report).slice(0,9).map(([k,v])=>`<div class="report-item"><span>${esc(k)}</span><strong>${esc(v)}</strong></div>`).join("")+
    `</div><p><strong>${esc(p.kind)}</strong> · найдено ${esc(p.count)} · ${esc(p.collected_at)}</p>`;
  const isDialogs=p.kind==="dialogs";
  document.querySelector("#collector-preview").innerHTML=
    `<table><thead><tr><th>Имя</th><th>${isDialogs?"Peer ID":"VK ID"}</th><th>Ссылка</th></tr></thead><tbody>`+
    p.items.slice(0,250).map(i=>`<tr><td><strong>${esc(i.full_name)}</strong></td><td>${esc(isDialogs?(i.peer_id??"—"):(i.vk_id??i.screen_name??"—"))}</td><td><a href="${safeHref(i.dialog_url||i.profile_url||"#")}" target="_blank" rel="noopener noreferrer">Открыть</a></td></tr>`).join("")+
    `</tbody></table>`+
    (p.items.length>250?`<p class="list-meta">Показаны первые 250 из ${p.items.length}</p>`:"");
  document.querySelector("#collector-save").disabled=false;
}

async function collectorAction(path, button, successText){
  const old=button.textContent;
  button.disabled=true;
  button.innerHTML='<span class="spinner"></span>';
  try{
    const result=await api(path,{method:"POST"});
    if(result.items) renderCollectorPreview(result);
    await updateCollectorStatus();
    return result;
  }catch(e){
    document.querySelector("#collector-status").innerHTML=`<span class="negative"><strong>Ошибка:</strong> ${esc(e.message)}</span>`;
    throw e;
  }finally{
    button.disabled=false;
    button.textContent=old;
  }
}

document.querySelector("#collector-start").onclick=async function(){await collectorAction("/api/collector/start",this);};
document.querySelector("#collector-auth").onclick=async function(){await collectorAction("/api/collector/check-auth",this);};
document.querySelector("#collector-friends").onclick=async function(){await collectorAction("/api/collector/collect/friends",this);};
document.querySelector("#collector-followers").onclick=async function(){await collectorAction("/api/collector/collect/followers",this);};
document.querySelector("#collector-dialogs").onclick=async function(){await collectorAction("/api/collector/collect/dialogs",this);};
document.querySelector("#collector-close").onclick=async function(){await collectorAction("/api/collector/close",this);};
document.querySelector("#collector-delete").onclick=async function(){
  if(!confirm("Удалить отдельный Chromium-профиль и завершить сессию VK?")) return;
  const old=this.textContent; this.disabled=true;
  try{
    await api("/api/collector/profile",{method:"DELETE"});
    document.querySelector("#collector-preview").innerHTML="";
    document.querySelector("#collector-report").className="empty";
    document.querySelector("#collector-report").textContent="Локальная сессия удалена.";
    document.querySelector("#collector-save").disabled=true;
    await updateCollectorStatus();
  }catch(e){alert(e.message)}finally{this.disabled=false;this.textContent=old;}
};
document.querySelector("#collector-save").onclick=async function(){
  const old=this.textContent;this.disabled=true;this.innerHTML='<span class="spinner"></span>';
  try{
    const r=await api("/api/collector/save-preview",{method:"POST"});
    const notice=r.status==="INCOMPLETE"?"Наблюдение сохранено. Полнота не подтверждена; текущие связи не изменены.":"Сохранено:";
    document.querySelector("#collector-report").insertAdjacentHTML("beforeend",`<p><strong>${esc(notice)}</strong> ${esc(JSON.stringify(r))}</p>`);
    await refreshAll();
  }catch(e){alert(e.message)}finally{this.textContent=old;this.disabled=false;}
};

updateCollectorStatus();
setInterval(updateCollectorStatus,5000);

let collectedDialogs=[];
async function loadDialogs(){collectedDialogs=await api("/api/dialogs");renderDialogs();}
function renderDialogs(){const q=(document.querySelector("#dialogs-search")?.value||"").toLowerCase();const rows=collectedDialogs.filter(d=>d.full_name.toLowerCase().includes(q)||String(d.preview||"").toLowerCase().includes(q));document.querySelector("#dialogs-summary").innerHTML=[metric("Диалогов",collectedDialogs.length,"последний снимок"),metric("Непрочитанных",collectedDialogs.filter(d=>d.unread).length,"требуют внимания"),metric("Последнее от меня",collectedDialogs.filter(d=>d.outgoing).length,"диалогов"),metric("Верифицированных",collectedDialogs.filter(d=>d.verified).length,"аккаунтов")].join("");document.querySelector("#dialogs-list").innerHTML=rows.length?rows.map(d=>`<div class="list-item"><div><div class="list-title"><a href="${safeHref(d.dialog_url||"#")}" target="_blank" rel="noopener noreferrer">${esc(d.full_name)}</a></div><div class="list-meta">${d.outgoing?"Вы: ":""}${esc(d.preview||"Нет превью")} · ${esc(d.date_label||"")}</div></div>${d.unread?`<span class="badge bad">${esc(d.unread_count??"новое")}</span>`:""}</div>`).join(""):'<div class="empty">Сохранённых диалогов нет</div>';}
document.querySelector("#dialogs-search").oninput=renderDialogs;loadDialogs().catch(console.error);
