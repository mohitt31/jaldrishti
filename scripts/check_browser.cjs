/* Playwright: actual Pyodide/CLI parity, interactions, initial transfer and mobile QA. */
const fs=require('fs'),path=require('path'),assert=require('assert/strict');
const {chromium}=require('playwright');
const root=path.resolve(__dirname,'..');
const base=process.env.SITE_URL||'http://127.0.0.1:8765/';
const output=process.env.QA_OUTPUT||'reports/browser_release/browser_qa.json';
const screenshotDir=process.env.SCREENSHOT_DIR||'docs/screenshots';
(async()=>{
 const browser=await chromium.launch({headless:true,channel:process.env.BROWSER_CHANNEL||'chrome'});
 const cases=JSON.parse(fs.readFileSync(path.join(root,'reports/browser_release/parity.json'))).cases;
 const report={label:'post-hoc engineering/dev browser checks, not accuracy evaluation',url:base,pyodide_version:'314.0.7',credits_used:0,devices:[]};
 fs.mkdirSync(path.resolve(root,screenshotDir),{recursive:true});
 for(const mobile of [false,true]){
  const context=await browser.newContext(mobile?{viewport:{width:390,height:844},isMobile:true,hasTouch:true,deviceScaleFactor:1}:{viewport:{width:1365,height:1000},deviceScaleFactor:1});
  const page=await context.newPage(),errors=[],failed=[],requests=[];let initial=true;
  page.on('pageerror',e=>errors.push(e.message));page.on('console',e=>{if(e.type()==='error')errors.push(e.text())});page.on('requestfailed',r=>failed.push({url:r.url(),error:r.failure()?.errorText}));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+' '+r.url());});page.on('request',r=>{if(initial)requests.push(r.url());assert(!r.url().includes('serpapi.com/search'),'Must never call SerpApi');});
  await page.goto(base,{waitUntil:'networkidle'});await page.waitForFunction(()=>document.querySelectorAll('.district-shape').length===23&&document.getElementById('district-evidence').querySelector('details'));
  const initialBytes=await page.evaluate(()=>performance.getEntriesByType('navigation').concat(performance.getEntriesByType('resource')).reduce((s,r)=>s+r.decodedBodySize,0));
  assert(initialBytes<3000000,`Initial decoded payload ${initialBytes}`);assert(!requests.some(u=>u.includes('cdn.jsdelivr.net/pyodide')));
  initial=false;
  const device=mobile?'mobile':'desktop';
  const parity=[];
  // Each browser runs all ten inputs through WASM and compares the complete answer JSON to CLI.
  for(const c of cases){
   const actual=await page.evaluate(async c=>await window.jaldrishtiBrowser.ask(c.question,c.scope),c);
   assert.deepEqual(actual,c.answer,c.id+' Python CLI parity');parity.push({id:c.id,exact_match:true});
  }
  await page.getByRole('button',{name:'332 vs 329 µg/L: comparable?'}).click();
  await page.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='not comparable');
  assert((await page.locator('#ask-answer').innerText()).includes('332 µg/L vs 329 µg/L'));
  assert(await page.locator('#ask-answer').getByText('Failed comparison checks').count());
  await page.locator('#ask-answer details').first().locator('summary').click();
  assert((await page.locator('#ask-answer').innerText()).includes('0.332'));
  await page.locator('#ask').screenshot({path:path.resolve(root,screenshotDir,`ask-${device}.png`)});
  await page.locator('#district-select').selectOption('Purulia');
  await page.waitForFunction(()=>document.getElementById('ask-question').value.includes('Purulia'));
  assert(await page.locator('#district-evidence details').count()>0);
  await page.locator('#map').screenshot({path:path.resolve(root,screenshotDir,`map-${device}.png`)});
  const svgNadia=page.locator('.district-shape[data-name="Nadia"]');await svgNadia.focus();await page.keyboard.press('Enter');
  await page.waitForFunction(()=>document.getElementById('district-heading').textContent==='Nadia');
  await page.getByRole('button',{name:'When evidence is missing'}).click();
  await page.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='insufficient evidence');
  for(const label of ['हिन्दी में पूछें','বাংলায় প্রশ্ন করুন']){
   await page.getByRole('button',{name:label}).click();
   await page.waitForFunction(()=>!document.getElementById('ask-submit').disabled&&document.querySelector('#ask-answer .badge')?.textContent==='number with source');
   assert(await page.locator('#ask-answer p[lang]').count());
  }
  await page.locator('#ask-scope').selectOption('library');await page.locator('#ask-form').evaluate(f=>f.requestSubmit());
  await page.waitForFunction(()=>document.querySelector('#ask-answer .badge')?.textContent==='insufficient evidence');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth);assert(!overflow,'Horizontal overflow');
  assert.equal(await page.locator('#cards .card').count(),3);assert.equal(await page.locator('#holdout-cards .card').count(),2);
  assert.deepEqual(errors,[]);assert.deepEqual(failed,[]);
  report.devices.push({device,viewport:page.viewportSize(),initial_decoded_bytes:initialBytes,initial_requests:requests.length,pyodide_loaded_before_interaction:false,parity,console_errors:errors,failed_requests:failed,horizontal_overflow:overflow,checks:['comparison values, failed checks, row disclosure','district click/keyboard/dropdown and question fill','insufficient evidence','Hindi/Bengali headers','reference/library separation','historical result cards']});
  console.log(device,'passed;',initialBytes,'initial bytes;',parity.length,'exact Pyodide/CLI matches');await context.close();
 }
 await browser.close();fs.writeFileSync(path.resolve(root,output),JSON.stringify(report,null,2)+'\n');
})().catch(e=>{console.error(e);process.exit(1)});
