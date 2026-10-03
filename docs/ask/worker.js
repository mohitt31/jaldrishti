/* Run the packaged Python engine off the UI thread. No search requests or keys. */
let runtime;
self.onmessage = async ({data}) => {
  const {id, question, scope} = data;
  try {
    if (!runtime) {
      postMessage({id, status:'Loading Python from jsDelivr… First use needs an internet connection.'});
      const {loadPyodide} = await import('https://cdn.jsdelivr.net/pyodide/v314.0.7/full/pyodide.mjs');
      const py = await loadPyodide({indexURL:'https://cdn.jsdelivr.net/pyodide/v314.0.7/full/'});
      postMessage({id, status:'Loading the evidence index and source verification snapshot…'});
      const [code, evidence] = await Promise.all(['engine.zip','evidence.json.gz'].map(async url => {const r=await fetch(url); if(!r.ok)throw Error('Download failed: '+url);return new Uint8Array(await r.arrayBuffer());}));
      py.FS.writeFile('/engine.zip',code); py.FS.writeFile('/evidence.json.gz',evidence);
      py.runPython(`import sys, gzip, json, zipfile
with zipfile.ZipFile('/engine.zip') as z: z.extractall('/home/pyodide')
sys.path.insert(0, '/home/pyodide')
from jaldrishti.browser_runtime import BrowserRuntime
with gzip.open('/evidence.json.gz', 'rt') as f: browser = BrowserRuntime(json.load(f))`);
      runtime=py;
    }
    runtime.globals.set('question_text',question);runtime.globals.set('evidence_scope',scope);
    const answer=JSON.parse(runtime.runPython('json.dumps(browser.ask(question_text, evidence_scope), ensure_ascii=False)'));
    postMessage({id, answer});
  } catch (err) { postMessage({id,error:'Could not run the browser engine. Check your connection to jsDelivr, then retry. '+String(err.message || err).slice(0,180)}); }
};
