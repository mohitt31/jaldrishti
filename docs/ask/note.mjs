/* Portable research notes. Review comments are separate; source evidence is never edited. */
export const SCHEMA='jaldrishti-evidence-note/v1';
export const MAX_BYTES=1024*1024;
export const DECISIONS=['not_checked','matches_my_reading','needs_correction'];
export const clone=x=>JSON.parse(JSON.stringify(x));
const fail=m=>{throw new Error(m);};
const text=(s,max,name)=>{if(typeof s!=='string'||s.length>max)fail('Invalid '+name);};
function jsonSafe(root){const stack=[[root,0]];let seen=0;while(stack.length){const [v,d]=stack.pop();if(++seen>50000||d>18)fail('Note is too complex');if(typeof v==='string'&&v.length>16000)fail('Note text is too long');if(v&&typeof v==='object'){if(Array.isArray(v)&&v.length>500)fail('Too many records');for(const [k,x] of Object.entries(v)){if(['__proto__','constructor','prototype'].includes(k))fail('Unsupported object key');stack.push([x,d+1]);}}}}
export function stable(value){if(value===null||typeof value!=='object')return JSON.stringify(value);if(Array.isArray(value))return '['+value.map(stable).join(',')+']';return '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+stable(value[k])).join(',')+'}';}
const timestamp=()=>new Date().toISOString();
const id=()=>globalThis.crypto.randomUUID();
export function createNote(){return {schema:SCHEMA,note_id:id(),created_at:timestamp(),title:'Groundwater evidence note',entries:[],reviews:[]};}
export function validateNote(value){
 jsonSafe(value);if(!value||value.schema!==SCHEMA)fail('Not a supported NeerTathya note');text(value.note_id,80,'note ID');text(value.created_at,60,'creation time');text(value.title,120,'title');
 if(!Array.isArray(value.entries)||value.entries.length>20||!Array.isArray(value.reviews)||value.reviews.length>100)fail('Note limit: 20 answers and 100 review comments');
 const validAnswer=a=>{
  for(const key of ['items','related']){if(a[key]===undefined&&key==='related')continue;if(!Array.isArray(a[key])||a[key].length>100)fail('Invalid citation list');for(const i of a[key]){if(!i||typeof i!=='object'||Array.isArray(i))fail('Invalid citation');for(const field of ['value','unit','title','url','quote','place','district','source_type','well_id','date','period','period_quote','statistic','contaminant','spatial_support','evidence_id'])if(i[field]!=null&&!['string','number'].includes(typeof i[field]))fail('Invalid citation field');if(i.page!=null&&(!Number.isInteger(i.page)||i.page<1))fail('Invalid source page');for(const field of ['row_verified','page_verified'])if(i[field]!==undefined&&typeof i[field]!=='boolean')fail('Invalid verification flag');}}
  if(a.reasons!==undefined&&(!Array.isArray(a.reasons)||a.reasons.some(r=>typeof r!=='string')))fail('Invalid comparison reasons');
  for(const field of ['reason','note'])if(a[field]!=null&&typeof a[field]!=='string')fail('Invalid answer explanation');
 };
 const ids=new Set();for(const e of value.entries){text(e.entry_id,80,'entry ID');if(ids.has(e.entry_id))fail('Duplicate entry ID');ids.add(e.entry_id);text(e.question,2000,'question');text(e.saved_at,60,'saved time');if(!['library','reference'].includes(e.scope))fail('Invalid scope');if(!e.answer||!['number_with_source','not_comparable','comparable','insufficient_evidence'].includes(e.answer.answer_type)||!Array.isArray(e.answer.items))fail('Invalid saved answer');validAnswer(e.answer);if(!e.snapshot||typeof e.snapshot!=='object')fail('Missing snapshot identity');}
 for(const r of value.reviews){text(r.review_id,80,'review ID');text(r.created_at,60,'review time');text(r.comment,4000,'review comment');if(!ids.has(r.entry_id)||!DECISIONS.includes(r.decision))fail('Invalid review reference or decision');}
 if(new TextEncoder().encode(JSON.stringify(value)).length>MAX_BYTES)fail('Note exceeds 1 MB');return clone(value);
}
export function parseNote(raw){if(typeof raw!=='string'||new TextEncoder().encode(raw).length>MAX_BYTES)fail('Choose a JSON note smaller than 1 MB');return validateNote(JSON.parse(raw));}
export function addAnswer(note,{question,scope,answer,snapshot}){const n=validateNote(note);if(n.entries.length>=20)fail('Note limit reached; export this note and start another.');n.entries.push({entry_id:id(),saved_at:timestamp(),question,scope,answer:clone(answer),snapshot:clone(snapshot)});return validateNote(n);}
export function addReview(note,entry_id,decision,comment){const n=validateNote(note);n.reviews.push({review_id:id(),created_at:timestamp(),entry_id,decision,comment});return validateNote(n);}
export function removeEntry(note,entry_id){const n=validateNote(note);n.entries=n.entries.filter(e=>e.entry_id!==entry_id);n.reviews=n.reviews.filter(r=>r.entry_id!==entry_id);return n;}
export function safeLink(url,page){try{const u=new URL(url);if(!['http:','https:'].includes(u.protocol))return null;if(page)u.hash='page='+Number(page);return u.href;}catch{return null;}}
// Encode raw user/source strings as Markdown text, never active HTML or injected links.
export function mdText(value){return String(value??'not stated').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/([\\`*_{}\[\]()!#|])/g,'\\$1');}
export function markdown(note){const n=validateNote(note);let lines=['# '+mdText(n.title),'','Exported research note. Imported content and review statuses are not independently authenticated. Recheck against the loaded NeerTathya snapshot before relying on it.','No household safety conclusion; different surveys are not a district risk ranking.','','Note ID: '+mdText(n.note_id),'Created: '+mdText(n.created_at),''];
 for(const [index,e] of n.entries.entries()){
  lines.push('## '+(index+1)+'. '+mdText(e.question),'','Evidence scope: '+mdText(e.scope),'Recorded answer type: '+mdText(e.answer.answer_type),'Saved: '+mdText(e.saved_at),'');
  if(e.answer.reason)lines.push(mdText(e.answer.reason),'');if(e.answer.note)lines.push(mdText(e.answer.note),'');for(const reason of e.answer.reasons||[])lines.push('- Failed check: '+mdText(reason));
  const renderItem=(i,related=false)=>{lines.push('','### '+(related?'Related record — not a complete answer':'Cited record'),'','Value: '+mdText(i.value)+' '+mdText(i.unit||'unit not stated'),'Statistic: '+mdText(i.statistic),'Contaminant: '+mdText(i.contaminant),'Place: '+mdText(i.place||'not stated'),'District: '+mdText(i.district),'Well / source type: '+mdText(i.well_id||'not stated')+' / '+mdText(i.source_type||'not stated'),'Spatial support: '+mdText(i.spatial_support),'Sampling: '+mdText(i.date||i.period||'not stated'),'Publication year: '+mdText(i.publication_year||'not stated'),'Source title as recorded: '+mdText(i.title),'Physical PDF page: '+mdText(i.page||'abstract / not stated'));
   const link=safeLink(i.url,i.page);lines.push('Source: '+(link?'<'+link.replace(/</g,'%3C').replace(/>/g,'%3E')+'>':'invalid or unavailable URL'),'Evidence ID: '+mdText(i.evidence_id),'Verification recorded at build time: '+(i.row_verified?'row check':i.page_verified?'page/abstract number check only':'not verified'),'Extracted row / excerpt: '+mdText(i.quote),'Period evidence: '+mdText(i.period_quote||'not stated'));};
  for(const i of e.answer.items)renderItem(i);for(const i of e.answer.related||[])renderItem(i,true);
  lines.push('','Snapshot SHA-256: '+mdText(e.snapshot.sha256?.['evidence.json.gz']||'not provided'),'Engine SHA-256: '+mdText(e.snapshot.sha256?.['engine.zip']||'not provided'),'');
  const reviews=n.reviews.filter(r=>r.entry_id===e.entry_id);lines.push('### Reviewer comments — self-reported, not expert certification','');if(!reviews.length)lines.push('Not reviewed.');for(const r of reviews)lines.push('- '+mdText(r.created_at)+' · '+mdText(r.decision)+': '+mdText(r.comment));lines.push('');
 }
 return lines.join('\n')+'\n';
}
export function answerMatches(entry,currentAnswer){return stable(entry.answer)===stable(currentAnswer);}
