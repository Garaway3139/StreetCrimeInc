// simple game client that calls /api/action on crime click and updates HUD
const $ = id => document.getElementById(id);
async function postJSON(url, body){ const r = await fetch(url, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body)}); return r.json(); }

async function doCrime(){
  const res = await postJSON('/api/action', {action:'crime'});
  if(res.ok){
    document.getElementById('cash').textContent = Math.floor(res.cash);
    document.getElementById('rep').textContent = Math.floor(res.rep);
  } else {
    console.warn('action failed', res);
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  const btn = document.getElementById('crimeBtn');
  if(btn) btn.onclick = doCrime;
  // Poll players for initial HUD
  fetch('/api/players').then(r=>r.json()).then(list=>{
    const usernameSpan = document.querySelector('header .top-right span');
    let me = null;
    if(usernameSpan){
      const name = usernameSpan.textContent.replace('Hi, ','').trim();
      me = list.find(x=>x.username==name);
    }
    if(!me) me = list.find(x=>x.role=='player') || list[0];
    if(me){
      document.getElementById('cash').textContent = Math.floor(me.cash);
      document.getElementById('rep').textContent = Math.floor(me.rep);
      document.getElementById('rank').textContent = ['Rookie','Hustler','Capo','Boss','Don'][me.rank_index] || 'Rookie';
    }
  });
});
