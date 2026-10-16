const $ = (id) => document.getElementById(id);
const demo = JSON.parse($('demo-data').textContent);
const names = {soft:'浅色柔光网格',orange:'暖橙渐变网格',radial:'对称径向网格'};
const categories = {brand:'品牌素材', 'layout-reference':'总体参考', 'background-reference':'底图参考',background:'可用底图',static:'已有静图',other:'其他素材'};
let state = {mode:'cover',background:'soft',template:'minimal',title:'Partnership Announcement',subtitle:'Approved copy goes here.',format:'png',duration:5,uploads:[],brand_pack:null,logo_id:null,partner_logo_id:null};
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
  return {mode:state.mode,background:state.background,template:$('template').value,title:$('title').value,subtitle:$('subtitle').value,format:$('format').value,duration:Number($('duration').value),logo_id:state.logo_id,partner_logo_id:state.partner_logo_id};
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
function backgroundAssets() {
  if(state.brand_pack?.backgrounds?.length) return state.brand_pack.backgrounds;
  return Object.entries(demo.backgrounds).map(([id,url])=>({id,url,name:names[id]}));
}
function rebuildBackgroundOptions() {
  $('background-options').replaceChildren();
  for(const asset of backgroundAssets()) {
    const button=document.createElement('button');button.className='background-option';button.dataset.background=asset.id;
    const image=document.createElement('img');image.src=asset.url;image.alt=asset.name;
    const label=document.createElement('span');label.textContent=asset.name;button.append(image,label);
    button.addEventListener('click',()=>{state.background=asset.id;syncBackgrounds();renderNow().catch(()=>{});});
    $('background-options').append(button);
  }
}
function syncBackgrounds() {
  const assets=backgroundAssets();
  const selected=assets.find(asset=>asset.id===state.background) || assets[0];
  if(!selected)return;
  document.querySelectorAll('[data-background]').forEach(b=>b.classList.toggle('active',b.dataset.background===selected.id));
  $('selected-bg-image').src=selected.url;
  $('selected-bg-name').textContent=selected.name;
}
function syncBrandPack() {
  const pack=state.brand_pack;
  const logos=pack?.logos || [];
  const brand=logos.find(asset=>asset.id===state.logo_id) || logos[0];
  const partner=state.partner_logo_id ? logos.find(asset=>asset.id===state.partner_logo_id) : null;
  $('brand-asset').src=brand?.url || demo.logo;
  $('partner-asset').src=partner?.url || demo.partner;
  $('brand-pack-name').textContent=pack ? `${pack.display_name} · ${pack.version || '未标版本'}` : '默认演示素材';
  $('brand-pack-help').textContent=pack ? '已载入当前项目的品牌包，Logo 与底图来自包内清单。' : '当前使用演示素材；可通过 Codex 会话安装品牌包。';
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
  refreshBackgroundReferences();
  const count = (state.uploads || []).length;
  $('handoff-session').querySelector('span').textContent = count ? `准备当前会话任务（${count} 个素材）` : '准备当前会话任务';
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
  syncMode(); rebuildBackgroundOptions(); syncBackgrounds(); syncBrandPack(); syncTemplate(); updatePaths(); displayFiles();
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
async function handoffSession() {
  if(!online) return toast('请先启动本地服务。',true);
  const button=$('handoff-session'); button.disabled=true;
  try {
    const result=await api('/api/session-handoff',{instruction:$('session-instruction').value.trim()});
    acceptResult(result.state);
    const prompt=result.handoff.prompt;
    let copied=false;
    try {await navigator.clipboard.writeText(prompt);copied=true;} catch(error) {}
    $('session-handoff-status').textContent = copied
      ? `任务已生成：${result.handoff.markdown_file}；提示词已复制，请回到当前会话粘贴。`
      : `任务已生成：${result.handoff.markdown_file}；请复制任务路径到当前会话。`;
    toast(copied?'会话任务已准备，提示词已复制。':'会话任务已准备，请查看任务路径。');
  } catch(error) {toast(error.message,true);}
  finally {button.disabled=false;}
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

$('preview').src=demo.cover;
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
$('handoff-session').onclick=handoffSession;
for(const event of ['dragenter','dragover']) $('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.add('dragover');});
for(const event of ['dragleave','drop']) $('dropzone').addEventListener(event,e=>{e.preventDefault();$('dropzone').classList.remove('dragover');if(event==='drop')uploadFiles(Array.from(e.dataTransfer.files));});
$('duration').oninput=()=>{$('duration-label').textContent=$('duration').value+' 秒';};
async function saveRequest(kind) {
  if(!online)return toast('请先启动本地服务。',true);
  const brief=$('motion-brief').value.trim();
  if(!brief)return toast('请先填写希望制作的效果。',true);
  try {await renderNow();const result=await api('/api/request',{kind,brief});toast('需求已保存到 requests/，尚未执行。');}
  catch(error){toast(error.message,true);}
}
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
// Background intent stays in the workbench; image understanding runs in the current chat.
let selectedReferenceIds = new Set(), backgroundResultTimer, shownBackgroundResult = '', ignoreBackgroundResult = false;
function markBackgroundTaskDirty() {$('background-task-output').hidden=true;}
function resetBackgroundAnalysis() {
  markBackgroundTaskDirty();
  ignoreBackgroundResult=true;clearTimeout(backgroundResultTimer);
  $('background-analysis').hidden=true;$('background-style-prompt').value='';
}
function backgroundSource() {return document.querySelector('[name="reference-source"]:checked').value;}
function backgroundIntent() {return document.querySelector('[name="background-intent"]:checked').value;}
function refreshBackgroundReferences() {
  const list=$('background-reference-list'); list.replaceChildren();
  const files=(state.uploads || []).filter(file=>['background-reference','layout-reference'].includes(file.category) && /\.(png|jpe?g|webp|gif)$/i.test(file.name));
  if(!files.length) {const hint=document.createElement('p');hint.className='field-help';hint.textContent='还没有参考图，先上传一张喜欢的图片。';list.append(hint);}
  for(const file of files) {
    const label=document.createElement('label');label.className='reference-item';
    const input=document.createElement('input');input.type='checkbox';input.value=file.id;input.checked=selectedReferenceIds.has(file.id);
    input.onchange=()=>{resetBackgroundAnalysis();if(input.checked)selectedReferenceIds.add(file.id);else selectedReferenceIds.delete(file.id);};
    const image=document.createElement('img');image.src='/workspace/'+file.relative_path.split('/').map(encodeURIComponent).join('/');image.alt='';
    const name=document.createElement('span');name.textContent=file.name;
    label.append(input,image,name);list.append(label);
  }
}
function syncBackgroundWorkflow() {
  const panel=backgroundSource()==='panel';
  $('reference-panel').hidden=!panel;$('reference-chat-help').hidden=panel;
  $('prepare-background-task').textContent=backgroundIntent()==='generate'?'准备新底图生成任务':'准备风格分析任务';
}
function showBackgroundTask(receipt, message) {
  $('background-task-output').hidden=false;
  $('background-task-prompt').value=receipt.prompt;
  $('background-task-status').textContent=message || '任务已保存，等待在 Codex 对话发送。';
}
function restoreBackgroundWorkflow() {
  const request=state.background_request;
  if(request) {
    $('background-brief').value=request.brief || '';
    $('background-ratio').value=request.aspect_ratio;
    $('background-text-space').value=request.text_space;
    document.querySelectorAll('[name="reference-source"]').forEach(input=>input.checked=input.value===request.reference_source);
    document.querySelectorAll('[name="background-intent"]').forEach(input=>input.checked=input.value===request.intent);
    selectedReferenceIds=new Set(request.reference_ids || []);
    $('background-style-prompt').value=request.style_prompt || '';
    if(request.style_prompt)$('background-analysis').hidden=false;
  }
  refreshBackgroundReferences();syncBackgroundWorkflow();
  if(state.background_handoff) {showBackgroundTask(state.background_handoff);pollBackgroundResult();}
}
async function uploadBackgroundReferences(files) {
  if(!online)return toast('请启动本地服务后上传参考图。',true);
  const button=$('background-reference-dropzone');button.disabled=true;
  let completed=0;
  try {
    for(const file of files) {
      if(!/\.(png|jpe?g|webp|gif)$/i.test(file.name))throw new Error('请选择 PNG、JPG、WebP 或 GIF 图片。');
      if(file.size>20*1024*1024)throw new Error(file.name+' 超过 20 MB。');
      const data=await new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve(reader.result.split(',')[1]);reader.onerror=()=>reject(new Error('无法读取图片'));reader.readAsDataURL(file);});
      const result=await api('/api/upload',{category:'background-reference',name:file.name,data});
      resetBackgroundAnalysis();state.uploads=result.state.uploads;selectedReferenceIds.add(result.asset.id);completed++;
      displayFiles();refreshBackgroundReferences();
    }
    if(completed)toast(completed+' 张参考图已保留原件并选中。');
  } catch(error) {toast((completed?'已保存 '+completed+' 张。':'')+error.message,true);}
  finally {button.disabled=false;$('background-reference-input').value='';}
}
async function copyBackgroundTask() {
  const field=$('background-task-prompt');
  try {await navigator.clipboard.writeText(field.value);toast('任务已复制，回到当前 Codex 对话粘贴发送。');return true;}
  catch(error) {field.focus();field.select();toast('请手动复制已选中的任务提示。');return false;}
}
async function prepareBackgroundTask() {
  if(!online)return toast('请先启动本地服务，保存任务与参考原件。',true);
  const source=backgroundSource();
  if(source==='panel' && !selectedReferenceIds.size)return toast('请先上传或勾选本次参考图。',true);
  const payload={reference_source:source,intent:backgroundIntent(),reference_ids:[...selectedReferenceIds],
    brief:$('background-brief').value.trim(),text_space:$('background-text-space').value,
    aspect_ratio:$('background-ratio').value,style_prompt:$('background-style-prompt').value.trim()};
  const button=$('prepare-background-task');button.disabled=true;
  try {
    // Save the current copy without rendering or replacing the selected background.
    const saved=await api('/api/save',draft());Object.assign(state,saved);
    const result=await api('/api/background-handoff',payload);
    Object.assign(state,result.state);shownBackgroundResult='';ignoreBackgroundResult=false;
    showBackgroundTask(result.handoff);
    const copied=await copyBackgroundTask();
    $('background-task-status').textContent=(copied?'任务已保存，提示已复制。':'任务已保存，请复制下方提示。')+(source==='chat'?' 回到 Codex 对话，把参考图和这段提示一起发送。':' 回到 Codex 对话粘贴发送。')+' AI 尚未执行。';
    savedText('底图任务已保存');pollBackgroundResult();
  } catch(error) {toast(error.message,true);}
  finally {button.disabled=false;}
}
async function pollBackgroundResult() {
  clearTimeout(backgroundResultTimer);
  const receipt=state.background_handoff;
  if(!online || !receipt || ignoreBackgroundResult)return;
  try {
    const response=await api('/api/background-result');
    if(response.task_id!==receipt.id || state.background_handoff?.id!==receipt.id || ignoreBackgroundResult)return;
    const result=response.result;
    if(result?.error) $('background-task-status').textContent=result.error+'；请让 Codex 按任务协议补全结果。';
    else if(result && shownBackgroundResult!==receipt.id) {
      $('background-analysis').hidden=false;$('background-style-summary').textContent=result.summary;
      const facts=$('background-style-facts');facts.replaceChildren();
      for(const [key,label] of [['palette','配色'],['material','材质'],['lighting','光影'],['composition','构图与留白']]) {
        const dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=result[key];facts.append(dt,dd);
      }
      // A pending task must not overwrite edits made while Codex was working.
      if(!$('background-style-prompt').value.trim() || $('background-style-prompt').value.trim()===(state.background_request?.style_prompt || ''))$('background-style-prompt').value=result.prompt;
      $('background-style-exclusions').textContent='排除：'+result.negative_prompt;
      $('background-task-status').textContent=result.generated_file?'分析与新底图已保存；请在对话中查看图片并选择是否采用。':'风格提示词已返回。可以直接修改，再选择生成新底图。';
      shownBackgroundResult=receipt.id;
    }
    if(result && !result.error)return;
  } catch(error) { /* Keep the saved prompt usable if the service temporarily stops. */ }
  backgroundResultTimer=setTimeout(()=>{if(!document.hidden)pollBackgroundResult();},4000);
}
function setupBackgroundWorkflow() {
  document.querySelectorAll('[name="reference-source"]').forEach(input=>input.onchange=()=>{resetBackgroundAnalysis();syncBackgroundWorkflow();});
  document.querySelectorAll('[name="background-intent"]').forEach(input=>input.onchange=()=>{markBackgroundTaskDirty();syncBackgroundWorkflow();});
  ['background-brief','background-ratio','background-text-space','background-style-prompt'].forEach(id=>$(id).addEventListener('input',markBackgroundTaskDirty));
  $('prepare-background-task').onclick=prepareBackgroundTask;$('copy-background-task').onclick=copyBackgroundTask;
  const dropzone=$('background-reference-dropzone');dropzone.onclick=()=>$('background-reference-input').click();
  $('background-reference-input').onchange=()=>uploadBackgroundReferences(Array.from($('background-reference-input').files));
  for(const event of ['dragenter','dragover'])dropzone.addEventListener(event,e=>{e.preventDefault();dropzone.classList.add('dragover');});
  for(const event of ['dragleave','drop'])dropzone.addEventListener(event,e=>{e.preventDefault();dropzone.classList.remove('dragover');if(event==='drop')uploadBackgroundReferences(Array.from(e.dataTransfer.files));});
  dropzone.addEventListener('paste',event=>{
    const files=Array.from(event.clipboardData?.files || []);
    if(files.length) {event.preventDefault();uploadBackgroundReferences(files);}
  });
  document.addEventListener('visibilitychange',()=>{if(!document.hidden && state.background_handoff && shownBackgroundResult!==state.background_handoff.id)pollBackgroundResult();});
  syncBackgroundWorkflow();refreshBackgroundReferences();
}

applyState();
setupBackgroundWorkflow();
(async()=>{
  try {
    state=await api('/api/state');online=true;applyState();restoreBackgroundWorkflow();
    if(state.submission)showFinalization();
    await renderNow();
  } catch(error) {savedText('离线外观预览');$('action-status').textContent='需启动服务才能保存与导出';toast('当前为外观预览。运行 server.py 可启用上传、合成和导出。',true);}
})();
