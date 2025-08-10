// Admin console JS: requests admin token and authenticates socket, shows live updates
const $ = id => document.getElementById(id);
async function fetchJSON(url, opts){ const r = await fetch(url, opts); return r.json(); }

function formatRow(u){
  return `<tr data-id="${u.id}">
    <td>${u.id}</td>
    <td>${u.username}</td>
    <td>${u.role}</td>
    <td>${Math.floor(u.cash)}</td>
    <td>${Math.floor(u.rep)}</td>
    <td>${['Rookie','Hustler','Capo','Boss','Don'][u.rank_index]||'Rookie'}</td>
    <td>
      <button class="editBtn" data-id="${u.id}">Edit</button>
      <button class="noteBtn" data-id="${u.id}">Note</button>
    </td>
  </tr>`;
}

async function loadPlayers(){
  const list = await fetchJSON('/api/players');
  const tbody = document.querySelector('#playersTable tbody');
  tbody.innerHTML = '';
  const filter = $('filter').value.toLowerCase();
  list.filter(u => u.username.toLowerCase().includes(filter)).forEach(u => tbody.insertAdjacentHTML('beforeend', formatRow(u)));
  document.querySelectorAll('.editBtn').forEach(b => b.onclick = onEdit);
  document.querySelectorAll('.noteBtn').forEach(b => b.onclick = onNote);
}

async function onEdit(e){
  const id = e.target.dataset.id;
  const cash = prompt("Set cash value (number):");
  if(cash===null) return;
  const rep = prompt("Set rep value (number):");
  if(rep===null) return;
  const res = await fetchJSON('/api/modify', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:id, cash: parseFloat(cash), rep: parseInt(rep)})});
  if(res.ok) addConsole(`Modified ${id} cash=${cash} rep=${rep}`);
  loadPlayers();
}

async function onNote(e){
  const id = e.target.dataset.id;
  const text = prompt("Add note for user:");
  if(!text) return;
  await fetchJSON('/api/notes', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({user_id:id, text})});
  addConsole(`Note saved for ${id}`);
}

function addConsole(msg){
  const c = $('console');
  const line = document.createElement('div');
  line.textContent = new Date().toLocaleTimeString() + " - " + msg;
  c.prepend(line);
  while(c.children.length>200) c.lastChild.remove();
}

document.addEventListener('DOMContentLoaded', async ()=>{
  $('refreshBtn').onclick = loadPlayers;
  $('filter').addEventListener('input', loadPlayers);
  loadPlayers();

  const socket = io();
  socket.on('connect', async ()=> {
    addConsole("Socket connected — requesting token...");
    const res = await fetch('/api/admin_token');
    const j = await res.json();
    if(j.token){
      addConsole('Received token, authenticating socket...');
      socket.emit('admin_auth', {token: j.token});
    } else addConsole('No token received: ' + JSON.stringify(j));
  });
  socket.on('admin_auth_result', d => {
    addConsole('Auth result: ' + JSON.stringify(d));
  });
  socket.on('initial_snapshot', data => {
    addConsole('Initial snapshot received: ' + data.length + ' players');
    loadPlayers();
  });
  socket.on('admin_update', d => {
    addConsole(`Update: ${d.username} cash=${Math.floor(d.cash)} rep=${Math.floor(d.rep)} role=${d.role}`);
    loadPlayers();
  });
});
