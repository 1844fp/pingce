import {pathToFileURL} from 'node:url';
globalThis.fetch=async()=>{throw Error('network forbidden');};
const root='E:/AI/codex/writing-site/src/';
let raw='';for await(const c of process.stdin)raw+=c;
const {operation}=JSON.parse(raw).input;let checks={},observed={};
if(operation==='topic_constraints'){
 const {generateTopics,writingHandoff}=await import(pathToFileURL(root+'topic-contract.mjs'));
 const {qualityBatch}=await import(pathToFileURL(root+'topic-quality.mjs'));
 const c={id:'ok',title:'SYNTHETIC',question:'SYNTHETIC question',discipline:'教育学',method:'访谈',object:'A',mechanism:'B',context:'C',dataIds:['missing'],keywords:['A'],days:3};
 const constraints={discipline:'教育学',methods:['访谈'],availableData:[],maxDays:5};
 const batch=await generateTopics({projectId:'synthetic',constraints,pool:{version:'synthetic-v1',candidates:[c,{...c,id:'method',method:'实验'},{...c,id:'deadline',days:20}]},seed:'fixed',count:3});
 let handoffError=null;try{await writingHandoff(batch,{taskId:'t',projectId:'synthetic',candidateId:'ok',expectedBatchHash:batch.batchHash,confirmed:true,currentConstraints:constraints});}catch(e){handoffError=e.message;}
 const quality=await qualityBatch({projectId:'synthetic',input:{discipline:'未知学科'},seed:'fixed',count:2});
 checks={method_rejected:batch.rejected.some(x=>x.id==='method'&&x.reasons.includes('method')),deadline_rejected:batch.rejected.some(x=>x.id==='deadline'&&x.reasons.includes('deadline')),data_handoff_blocked:!!handoffError?.includes('data unavailable'),quality_scope_blocked:quality.status==='needs_scope'};observed={rejected:batch.rejected,handoff_error:handoffError,quality_status:quality.status};
}else if(operation==='runtime_cancel'){
 const {makeProject}=await import(pathToFileURL(root+'core.mjs'));const {handleAPI}=await import(pathToFileURL(root+'runtime.mjs'));
 const p=makeProject({title:'SYNTHETIC',discipline:'教育学',direction:'SYNTHETIC'});let stored=structuredClone(p),calls=0,release,entered;
 const enteredPromise=new Promise(r=>entered=r),gate=new Promise(r=>release=r);
 const repo={get:async id=>id===stored.id?structuredClone(stored):null,save:async x=>{if(x._etag!==stored._etag)throw Error('CAS conflict');x.revision++;x._etag=String(x.revision);stored=structuredClone(x);}};
 const fetcher=async()=>{calls++;entered();await gate;return new Response(JSON.stringify({choices:[{finish_reason:'stop',message:{content:JSON.stringify({candidates:[{title:'SYNTHETIC',question:'SYNTHETIC'}]})}}]}));};
 const req=(action,body)=>new Request(`https://synthetic.invalid/api/v2/projects/${p.id}/${action}`,{method:'POST',headers:{'content-type':'application/json','x-llm-key':'synthetic-not-a-secret'},body:JSON.stringify(body)});
 const response=await handleAPI(req('run',{stage:'topic'}),repo,fetcher);
 if(response.status!==200)throw Error('run rejected '+response.status+' '+await response.text());
 if(!response.headers.get('content-type')?.includes('text/event-stream'))throw Error('run did not return SSE');
 await Promise.race([enteredPromise,new Promise((_,reject)=>setTimeout(()=>reject(Error('provider not entered '+JSON.stringify(stored.job))),3000))]);
 const cancel=await handleAPI(req('cancel',{}),repo,fetcher);release();const events=await response.text();
 checks={cancel_http:cancel.status===200,job_cancelled:stored.job?.status==='cancelled',run_interrupted:stored.workflow?.runs.at(-1)?.status==='interrupted',no_output:!stored.outputs.topic,one_fetch:calls===1,error_event:events.includes('event: error')||events.includes('"type":"error"')};observed={cancel_http_status:cancel.status,job_status:stored.job?.status,run_status:stored.workflow?.runs.at(-1)?.status,output_present:!!stored.outputs.topic,fetch_calls:calls};
}else throw Error('unsupported scenario');
console.log(JSON.stringify({output:{scenario:operation,checks,...observed},actions:['execute_synthetic_boundaries'],trace:[{name:operation,status:'OK',mode:'real_modules_synthetic_dependencies'}],usage:{cost:0,currency:'USD',modelCalls:0}}));






