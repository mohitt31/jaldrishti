/* Post-hoc interface checks; no users, live searches or evaluation reruns. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require('playwright');
const base=process.env.SITE_URL||'http://127.0.0.1:8765/';
const out=process.env.DESIGN_QA_OUTPUT||'reports/design_release/browser_qa.json';
const shots=process.env.DESIGN_SCREENSHOTS||'work/design/screenshots';
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'chrome'});
 const report={label:'post-hoc engineering UI checks; browser emulation, not a user study',url:base,credits_used:0,devices:[]};fs.mkdirSync(shots,{recursive:true});
 for(const [name,width,height,dark] of [['desktop',1440,1040,false],['mobile',390,844,false],['narrow-mobile',320,740,false],['dark-desktop',1280,900,true]]){
  const context=await browser.newContext({viewport:{width,height},isMobile:width<500,hasTouch:width<500,colorScheme:dark?'dark':'light',reducedMotion:'reduce'}),p=await context.newPage(),errors=[];
  p.on('pageerror',e=>errors.push(e.message));p.on('console',m=>{if(m.type()==='error')errors.push(m.text())});p.on('request',r=>assert(!r.url().includes('serpapi.com/search')));
  await p.goto(base,{waitUntil:'networkidle'});assert.equal(await p.title(),'NeerTathya');assert.equal(await p.locator('h1').count(),1);
  await p.keyboard.press('Tab');assert.equal(await p.locator(':focus').innerText(),'Skip to question');await p.keyboard.press('Enter');assert.equal(await p.locator(':focus').getAttribute('id'),'ask-question');
  const initialBytes=await p.evaluate(()=>performance.getEntriesByType('navigation').concat(performance.getEntriesByType('resource')).reduce((s,r)=>s+r.decodedBodySize,0));assert(initialBytes<3000000);
  await p.evaluate(()=>window.scrollTo(0,0));await p.screenshot({path:path.join(shots,`${name}-home.png`)});
  await p.locator('#open-note').click();assert(await p.locator('#note-panel').evaluate(e=>e.open));await p.locator('#note-summary').click();
  await p.locator('#district-select').selectOption('Purulia');await p.locator('#map-to-ask').waitFor({state:'visible'});assert.match(await p.locator('#map-to-ask').innerText(),/Purulia/);await p.locator('#map-to-ask').click();assert.equal(await p.locator(':focus').getAttribute('id'),'ask-question');assert.match(await p.locator('#ask-question').inputValue(),/Purulia/);
  // A stored legacy note must remain readable under the new public name.
  const legacy=await p.evaluate(async()=>{const n=await import('./ask/note.mjs');const note=n.createNote();note.title='Existing JalDrishti note';localStorage.setItem('jaldrishti.research-note.v1',JSON.stringify(note));return note;});await p.reload({waitUntil:'networkidle'});await p.locator('#open-note').click();assert.equal(await p.locator('#note-title').inputValue(),legacy.title);
  if(name==='desktop'||name==='mobile'){
   await p.getByRole('button',{name:'332 vs 329 µg/L: comparable?'}).click();await p.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='not comparable',null,{timeout:120000});
   assert.match(await p.locator('.answered-question').innerText(),/Karimpur/);assert(await p.locator('#ask-answer .badge').evaluate(e=>{const r=e.getBoundingClientRect();return r.top>=0&&r.bottom<=innerHeight;}),'Answer result in viewport');assert(await p.locator('#answer-placeholder').isHidden());
   await p.locator('#ask-answer .card details').first().locator('summary').click();await p.locator('#ask').screenshot({path:path.join(shots,`${name}-comparison.png`)});
   await p.getByRole('button',{name:'Save answer to evidence note'}).click();const downloadPromise=p.waitForEvent('download');await p.getByRole('button',{name:'Download readable Markdown',exact:true}).click();const download=await downloadPromise;assert.equal(download.suggestedFilename(),'neertathya-evidence-note.md');
   await p.locator('#ask-question').fill('What is the population-weighted mean fluoride in Nadia?');assert.equal(await p.locator('#ask-answer').innerText(),'');assert(await p.locator('#note-add').isDisabled());
   await p.locator('#ask-question').press('Control+Enter');await p.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='insufficient evidence');
   await p.locator('#ask-scope').selectOption('library');assert(await p.locator('#answer-placeholder').isVisible());
   await p.locator('#map').screenshot({path:path.join(shots,`${name}-map.png`)});
  }
  assert(!await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth),'Horizontal overflow '+name);
  const targets=await p.locator('#ask-submit,#ask-examples button,.nav-row nav a').evaluateAll(es=>es.map(e=>({text:e.textContent,height:e.getBoundingClientRect().height})));assert(targets.every(x=>x.height>=44),'Touch targets');
  assert.deepEqual(errors,[]);report.devices.push({name,width,height,dark,initial_decoded_bytes:initialBytes,overflow:false,console_errors:errors,checks:['skip link focus','note navigation','map-to-question action','legacy saved-note compatibility','44px primary touch targets',...(name==='desktop'||name==='mobile'?['actual Python comparison','branded export filename','edited question clears stale answer','keyboard submit','scope reset']:[])]});
  await context.close();console.log(name,'design checks passed');
 }
 await browser.close();fs.mkdirSync(path.dirname(out),{recursive:true});fs.writeFileSync(out,JSON.stringify(report,null,2)+'\n');
})().catch(e=>{console.error(e);process.exit(1)});
