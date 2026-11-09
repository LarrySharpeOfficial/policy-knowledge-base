"use strict";
const results=document.querySelector("#policy-results"),search=document.querySelector("#policy-search"),status=document.querySelector("#search-status");let policies=[];
const esc=value=>String(value).replace(/[&<>"']/g,char=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"})[char]);
function render(items){status.textContent=`${items.length} ${items.length===1?"policy":"policies"} found`;results.innerHTML=items.map(p=>`<article class="card"><p class="meta">${esc(p.editorial_status.replaceAll("_"," "))}</p><h3><a href="policies/${encodeURIComponent(p.slug)}.html">${esc(p.title)}</a></h3><p>${esc(p.problem)}</p><ul class="tags">${p.topics.map(t=>`<li>${esc(t)}</li>`).join("")}</ul></article>`).join("")}
function filter(){const q=search.value.trim().toLowerCase();render(q?policies.filter(p=>JSON.stringify(p).toLowerCase().includes(q)):policies)}
fetch("policy-snapshot-v0.1.0.json").then(r=>{if(!r.ok)throw new Error(`HTTP ${r.status}`);return r.json()}).then(data=>{policies=data.policies;render(policies);search.addEventListener("input",filter)}).catch(()=>{status.textContent="Search is unavailable. Use the policy links below."});
