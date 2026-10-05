/* Engineering simulation only. Synthetic review comments are never user-study results. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');const{chromium}=require('playwright');
const root=path.resolve(__dirname,'..'),base=process.env.SITE_URL||'http://127.0.0.1:8765/';
const out=process.env.WORKFLOW_QA_OUTPUT||'reports/workflow_release/browser_qa.json';
const shots=path.resolve(root,process.env.WORKFLOW_SCREENSHOTS||'work/sprint/screenshots');fs.mkdirSync(shots,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'chrome'});const report={label:'post-hoc engineering simulation; no human participants or real reviewer feedback',url:base,credits_used:0,devices:[],reliability:{}};
for(const mobile of [false,true]){
 const opts=mobile?{viewport:{width:390,height:844},isMobile:true,hasTouch:true}:{viewport:{width:1365,height:1000}};
 const context=await browser.newContext(opts),page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});page.on('dialog',d=>d.accept());
 await page.goto(base,{waitUntil:'networkidle'});await page.getByRole('button',{name:'A measured value',exact:true}).click();await page.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='number with source',null,{timeout:120000});
 await page.locator('#ask-answer .discovery-trail summary').first().click();assert.match(await page.locator('#ask-answer .discovery-trail').first().innerText(),/Saved search history/);
 await page.getByRole('button',{name:'Save answer to evidence note'}).click();await page.waitForFunction(()=>document.querySelectorAll('.note-entry').length===1);
 const saved=JSON.parse(await page.evaluate(()=>localStorage.getItem('jaldrishti.research-note.v1')));
 await page.locator('.review-decision').selectOption('needs_correction');await page.locator('.review-comment').fill('Synthetic QA comment: check the sampling period; not real user feedback.');await page.getByRole('button',{name:'Save reviewer comment',exact:true}).click();
 const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export review JSON',exact:true}).click();const download=await downloadPromise;const file=path.join(shots,`synthetic-note-${mobile?'mobile':'desktop'}.json`);await download.saveAs(file);const exported=JSON.parse(fs.readFileSync(file));assert.deepEqual(exported.entries,saved.entries);assert.equal(exported.reviews.length,1);
 const mdPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Download readable Markdown',exact:true}).click();const md=await mdPromise;const mdFile=path.join(shots,'synthetic-note.md');await md.saveAs(mdFile);assert.match(fs.readFileSync(mdFile,'utf8'),/#page=/);
 await page.locator('#note-panel').screenshot({path:path.join(shots,`note-${mobile?'mobile':'desktop'}.png`)});
 // Fresh browser storage models a manual file handoff, not a second real participant.
 const reviewer=await browser.newContext(opts),rp=await reviewer.newPage();rp.on('pageerror',e=>errors.push(e.message));rp.on('dialog',d=>d.accept());await rp.goto(base,{waitUntil:'networkidle'});await rp.locator('#note-panel').evaluate(e=>e.open=true);await rp.locator('#note-import').setInputFiles(file);await rp.waitForFunction(()=>document.querySelectorAll('.note-entry').length===1);assert.match(await rp.locator('#note-status').innerText(),/not authenticated/);
 await rp.getByRole('button',{name:'Recheck with Python',exact:true}).click();await rp.waitForFunction(()=>document.querySelector('.note-check-state')?.textContent.includes('Exact answer'),null,{timeout:120000});
 const tampered=JSON.parse(JSON.stringify(exported));tampered.entries[0].answer.items[0].value='999999';tampered.title='<img src=x onerror=alert(1)>';
 await rp.locator('#note-import').setInputFiles({name:'edited-note.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(tampered))});await rp.waitForFunction(()=>document.querySelector('#note-title').value.includes('<img'));
 await rp.getByRole('button',{name:'Recheck with Python',exact:true}).click();await rp.waitForFunction(()=>document.querySelector('.note-check-state')?.textContent.includes('Recheck differs'));assert.equal(await rp.locator('#note-panel img').count(),0);
 // A malformed import must leave the existing note intact.
 await rp.locator('#note-import').setInputFiles({name:'bad.json',mimeType:'application/json',buffer:Buffer.from('{"schema":"unknown"}')});await rp.waitForFunction(()=>document.querySelector('#note-status').textContent.includes('Import failed'));assert.equal(await rp.locator('.note-entry').count(),1);
 // Runtime already loaded: answering works with network disconnected. A reload isn't promised.
 await reviewer.setOffline(true);await rp.getByRole('button',{name:'Use this question',exact:true}).click();await rp.locator('#ask-form').evaluate(f=>f.requestSubmit());await rp.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='number with source');await reviewer.setOffline(false);
 assert(!await rp.evaluate(()=>document.documentElement.scrollWidth>innerWidth));assert.deepEqual(errors,[]);
 report.devices.push({device:mobile?'mobile emulation':'desktop',export_import_roundtrip:true,original_evidence_unchanged_by_review:true,import_rechecked_with_python:true,edited_measurement_detected:true,malformed_import_preserves_note:true,unsafe_html_not_executed:true,offline_after_loaded:true,horizontal_overflow:false,page_errors:errors});
 await reviewer.close();await context.close();console.log(mobile?'mobile':'desktop','workflow passed');
}
// Deliberately injected CDN failure, followed by retry in the same page.
const c=await browser.newContext(),p=await c.newPage();await p.goto(base,{waitUntil:'networkidle'});
await c.route('https://cdn.jsdelivr.net/pyodide/**/pyodide.mjs',r=>r.abort('failed'));
await p.getByRole('button',{name:'A measured value',exact:true}).click();await p.waitForFunction(()=>document.querySelector('#ask-status').textContent.includes('Could not run'),null,{timeout:30000});
await c.unroute('https://cdn.jsdelivr.net/pyodide/**/pyodide.mjs');
await p.getByRole('button',{name:'A measured value',exact:true}).click();await p.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='number with source',null,{timeout:120000});
report.reliability={injected_cdn_failure_shows_error:true,retry_same_page_recovers:true,limitation:'Offline check is after runtime/data loaded; no cold-start offline or physical-phone claim. Injected failure intentionally produces a failed request.'};
await c.close();await browser.close();fs.writeFileSync(path.resolve(root,out),JSON.stringify(report,null,2)+'\n');})().catch(e=>{console.error(e);process.exit(1)});
