const $ = (id) => document.getElementById(id);
const demo = JSON.parse($('demo-data').textContent);
const names = {soft:'浅色柔光网格',orange:'暖橙渐变网格',radial:'对称径向网格'};
const categories = {brand:'品牌素材', 'layout-reference':'总体参考', 'background-reference':'底图参考',background:'可用底图',static:'已有静图',other:'其他素材'};
let state = {mode:'cover',background:'soft',template:'minimal',title:'Partnership Announcement',subtitle:'Approved copy goes here.',format:'png',duration:5,uploads:[]};
let online = false, timer, toastTimer, sequence = 0, renderChain = Promise.resolve();

function toast(message, error = false) {
  clearTimeout(toastTimer); $('toast').textContent = message;
  $('toast').classList.toggle('error',error); $('toast').hidden = false;
  toastTimer = setTimeout(() => $('toast').hidden = true, error ? 8000 : 4500);
}
async function api(path, body) {
  const response = await fetch(path,{method:body === undefined ? 'GET':'POST',headers:body === undefined ? {}:{'Content-Type':'application/json'},body:body === undefined ? undefined:JSON.stringify(body)});
  const result = await response.json();
  if (!response.ok) throw new Error(result.error || '操作未完成');
  return result;
}
function draft() {
  return {mode:state.mode,background:state.background,template:$('template').value,title:$('title').value,subtitle:$('subtitle').value,format:$('format').value,duration:Number($('duration').value)};
}
function showTab(tab) {
  document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));
  ['content','backgrounds','delivery'].forEach(t=>$('tab-'+t).hidden=t!==tab || state.mode==='motion');
}
function syncMode() {
  document.querySelectorAll('[data-mode]').forEach(b=>b.classList.toggle('active',b.dataset.mode===state.mode));
  const motion = state.mode==='motion';
  $('motion-settings').hidden=!motion; $('motion-strip').hidden=!motion;
  document.querySelector('.inspector-tabs').hidden=motion;
  const selected = document.querySelector('[data-tab][aria-selected=true]')?.dataset.tab || 'content';
  showTab(state.mode==='background' ? 'backgrounds' : selected);
  $('preview-kind').textContent = motion ? '静态母版 · 动效待制作' : state.mode==='background' ? '无字底图' : '静态母版';
  $('preview-note').textContent = motion ? '已确认构图保持不变' : state.mode==='background' ? '无文字 · 无 Logo' : '独立底图 · Logo 分层保留';
  $('export').disabled=motion;
  $('export').querySelector('span').textContent=motion?'待补充运动素材':'导出图片';
  $('finalize').disabled=motion;
  if(motion) $('action-status').textContent='动效尚未制作 · 可先保存需求';
  else $('action-status').textContent='本地制作 · 素材不外传';
  $('finalization').hidden=!(state.finalized && state.dismissed_revision!==state.render_key) || motion;
}
function syncBackgrounds() {
  document.querySelectorAll('[data-background]').forEach(b=>b.classList.toggle('active',b.dataset.background===state.background));
  $('selected-bg-image').src=demo.backgrounds[state.background];
  $('selected-bg-name').textContent=names[state.background];
}
function syncTemplate() {
  $('copy-fields').hidden=$('template').value==='minimal';
  $('template-help').textContent=$('template').value==='minimal'?'只展示双方品牌，保持充足留白。':'在既有模板区域中排版，预览与导出共用合成器。';
}
function savedText(value) { $('save-status').querySelector('span').textContent=value; }
function updatePaths() {
  $('workspace-path').textContent=state.workspace || '请通过本地服务打开，启用真实文件保存';
  $('knowledge-path').textContent=state.knowledge_root ? state.knowledge_root+'/assets/video' : '可选，正式版首次设置';
  const date = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Hong_Kong',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const cat=$('upload-category').value;
  const suffix={brand:'materials/'+date+'-partnership-demo/brand/', 'layout-reference':'materials/'+date+'-partnership-demo/references/layout/', 'background-reference':'materials/'+date+'-partnership-demo/references/background/',background:'backgrounds/'+date+'-partnership-demo/',static:'materials/'+date+'-partnership-demo/existing-static/',other:'materials/'+date+'-partnership-demo/other/'}[cat];
  $('upload-destination').textContent='inbox/'+suffix;
}
function displayFiles() {
  $('uploaded-files').replaceChildren();
  for(const file of state.uploads || []) {
    const row=document.createElement('div'); row.className='file-row';
    row.innerHTML='<svg><use href="#i-image"/></svg><div class="file-info"><div class="file-name"></div><small></small></div><span class="micro-tag"></span>';
    row.querySelector('.file-name').textContent=file.name;
    row.querySelector('small').textContent=file.relative_path;
    row.querySelector('.micro-tag').textContent=categories[file.category];
    $('uploaded-files').append(row);
  }
}
function acceptResult(result) {
  Object.assign(state,result);
  if(result.preview && state.mode!=='motion') $('preview').src=result.preview;
  displayFiles(); updatePaths(); syncMode();
  savedText('已保存到本地');
}
function renderNow() {
  clearTimeout(timer);
  const snapshot=draft(), serial=++sequence;
  Object.assign(state,snapshot);
  if(!online) {toast('请启动本地服务后更新预览与保存文件。',true);return Promise.resolve();}
  $('render-overlay').hidden=state.mode==='motion';
  savedText('更新中…');
  const task=renderChain.catch(()=>{}).then(()=>api('/api/render',snapshot));
  renderChain=task;
  return task.then(result=>{
    if(serial===sequence) {acceptResult(result); $('render-overlay').hidden=true;}
    return result;
  }).catch(error=>{
    if(serial===sequence) {$('render-overlay').hidden=true;savedText('修改未完成');toast(error.message,true);}
    throw error;
  });
}
function scheduleRender() {
  savedText('有修改'); clearTimeout(timer);
  timer=setTimeout(()=>renderNow().catch(()=>{}),500);
}
function applyState() {
  $('template').value=state.template; $('title').value=state.title;
  $('subtitle').value=state.subtitle; $('format').value=state.format;
  $('duration').value=state.duration; $('duration-label').textContent=state.duration+' 秒';
  if(state.preview) $('preview').src=state.preview;
  syncMode(); syncBackgrounds(); syncTemplate(); updatePaths(); displayFiles();
}
async function uploadFiles(files) {
  if(!online) return toast('请通过本地服务打开后上传，确保原文件实际落盘。',true);
  const category=$('upload-category').value;
  const button=$('dropzone'); button.disabled=true;
  let completed=0;
  try {
    for(const file of files) {
      if(file.size>20*1024*1024) throw new Error(file.name+' 超过 20 MB，请选择较小文件。');
      const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=reject;reader.readAsDataURL(file);});
      const result=await api('/api/upload',{category,name:file.name,data});
      state.uploads=result.state.uploads; displayFiles();completed++;
    }
    savedText('原素材已保存');toast(completed+' 个文件已按“'+categories[category]+'”归档，原件保留。');
  } catch(error) {toast((completed?'已保存 '+completed+' 个文件。':'')+error.message,true);}
  finally {button.disabled=false;$('file-input').value='';}
}
async function finalize() {
  if(!online) return toast('请先启动本地服务。',true);
  try {
    await renderNow();
    acceptResult(await api('/api/finalize',{}));
    showFinalization();toast('已生成本地候选工程包，未提交知识库。');
    $('finalization').scrollIntoView({behavior:'smooth',block:'center'});
  } catch(error) {toast(error.message,true);}
}
function showFinalization() {
  const sub=state.submission;
  if(!sub)return;
  $('submission-target').textContent=sub.target;
  $('download-package').href='/workspace/'+sub.package;
  $('download-package').download='partnership-demo.zip';
  $('file-count').textContent='查看 '+sub.files.length+' 个入库文件';
  $('submission-files').replaceChildren(...sub.files.map(file=>{const li=document.createElement('li');li.textContent=file;return li;}));
  $('finalization').hidden=state.dismissed_revision===state.render_key;
}

$('brand-asset').src=demo.logo;
$('partner-asset').src=demo.partner; $('preview').src=demo.cover;
for(const key of Object.keys(names)) {
  const button=document.createElement('button');button.className='background-option';button.dataset.background=key;
  const image=document.createElement('img');image.src=demo.backgrounds[key];image.alt=names[key];
  const label=document.createElement('span');label.textContent=names[key];button.append(image,label);
  button.addEventListener('click',()=>{state.background=key;syncBackgrounds();renderNow().catch(()=>{});});
  $('background-options').append(button);
}
document.querySelectorAll('[data-mode]').forEach(button=>button.addEventListener('click',()=>{
  state.mode=button.dataset.mode;syncMode();
  renderNow().catch(()=>{});
}));
document.querySelectorAll('[data-tab]').forEach(button=>button.addEventListener('click',()=>showTab(button.dataset.tab)));
$('choose-background').onclick=$('selected-bg').onclick=()=>showTab('backgrounds');
$('settings').onclick=()=>{$('paths').hidden=!$('paths').hidden;};
$('close-paths').onclick=()=>$('paths').hidden=true;
$('template').onchange=()=>{syncTemplate();renderNow().catch(()=>{});};
['title','subtitle'].forEach(id=>$(id).addEventListener('input',scheduleRender));
$('format').onchange=()=>{if(online)api('/api/save',draft()).then(result=>{state.format=result.format;savedText('已保存到本地');}).catch(e=>toast(e.message,true));};
$('upload-category').onchange=updatePaths;
$('dropzone').onclick=()=>$('file-input').click();
$('file-input').onchange=()=>uploadFiles(Array.from($('file-input').files));
for(const event of ['dragenter','dragover']) $('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.add('dragover');});
for(const event of ['dragleave','drop']) $('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.remove('dragover');if(event==='drop')uploadFiles(Array.from(e.dataTransfer.files));});
$('duration').oninput=()=>{$('duration-label').textContent=$('duration').value+' 秒';};
async function saveRequest(kind) {
  if(!online)return toast('请先启动本地服务。',true);
  const brief=$(kind==='motion'?'motion-brief':'background-brief').value.trim();
  if(!brief)return toast('请先填写希望制作的效果。',true);
  try {await renderNow();const result=await api('/api/request',{kind,brief});toast('需求已保存到 requests/，尚未执行。');}
  catch(error){toast(error.message,true);}
}
$('save-background-request').onclick=()=>saveRequest('background');
$('save-motion-request').onclick=()=>saveRequest('motion');
$('export').onclick=async()=>{
  $('export').disabled=true;
  try {await renderNow();const link=document.createElement('a');link.href='/api/download';link.download='nopic-partnership.'+$('format').value;link.click();toast('图片已导出，完整项目同步保存在本地。');}
  catch(error){toast(error.message,true);}
  finally{$('export').disabled=state.mode==='motion';}
};
$('finalize').onclick=$('finalize-inspector').onclick=finalize;
$('dismiss').onclick=async()=>{try{acceptResult(await api('/api/dismiss',{}));$('finalization').hidden=true;toast('已保留本地，此版本不再提醒。');}catch(e){toast(e.message,true);}};
$('expand').onclick=()=>{$('lightbox-image').src=$('preview').src;$('lightbox').showModal();};
$('close-lightbox').onclick=()=>$('lightbox').close();
$('lightbox').addEventListener('click',event=>{if(event.target===$('lightbox'))$('lightbox').close();});
applyState();
(async()=>{
  try {
    state=await api('/api/state');online=true;applyState();
    if(state.submission)showFinalization();
    await renderNow();
  } catch(error) {savedText('离线外观预览');$('action-status').textContent='需启动服务才能保存与导出';toast('当前为外观预览。运行 server.py 可启用上传、合成和导出。',true);}
})();
