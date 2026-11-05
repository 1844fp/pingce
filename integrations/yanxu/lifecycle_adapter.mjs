import {pathToFileURL} from 'node:url';
globalThis.fetch=async()=>{throw Error('network forbidden');};
const root='E:/AI/codex/writing-site/src/';
const {makeProject}=await import(pathToFileURL(root+'core.mjs'));
const {executeWorkflow}=await import(pathToFileURL(root+'workflow.mjs'));
let text='';for await(const c of process.stdin)text+=c;
const {operation}=JSON.parse(text).input;
if(!['references_empty','resume_success'].includes(operation))throw Error('unsupported scenario');
let p=makeProject({title:'SYNTHETIC LIFECYCLE'}),durable=structuredClone(p),search_calls=0,model_calls=0,saves=0,outage=false,receiptSaved=false,first_error=null,resume_error=null;
const save=async()=>{saves++;if(outage)throw Error('synthetic checkpoint outage');const r=p.workflow?.runs.at(-1);durable=structuredClone(p);if(operation==='resume_success'&&r?.searchResult&&!r.effectDone){receiptSaved=true;outage=true;}};
const run=options=>executeWorkflow({project:p,stage:'references',options,credentials:{},save,emit:()=>{},search:async()=>{search_calls++;return operation==='references_empty'?[]:[{title:'SYNTHETIC RECORD',synthetic:true}];},model:async()=>{model_calls++;throw Error('model forbidden');},legacy:async()=>{throw Error('legacy forbidden');}});
try{await run({query:'SYNTHETIC'});}catch(e){first_error=e.code||e.message;}
const interrupted=first_error!==null;
if(operation==='resume_success'&&receiptSaved){p=structuredClone(durable);outage=false;try{await run({resume:true});}catch(e){resume_error=e.code||e.message;}}
const r=p.workflow?.runs.at(-1),records=p.outputs.references?.records;
const output={scenario:operation,interrupted,first_error,resume_error,search_calls,model_calls,saves,records_count:records?.length??null,run_status:r?.status??null,stage_status:p.stageStates.references?.status??null,checks:{no_model:model_calls===0,search_once:search_calls===1,completed:r?.status==='completed',records_expected:records?.length===(operation==='references_empty'?0:1),lifecycle_expected:operation==='references_empty'?!interrupted:interrupted&&receiptSaved&&resume_error===null}};
console.log(JSON.stringify({output,actions:['execute_synthetic_lifecycle'],trace:[{name:'executeWorkflow',status:'OK',mode:'real_orchestration_synthetic_dependencies',checkpoint_outage_injected:operation==='resume_success'}],usage:{cost:0,currency:'USD',modelCalls:model_calls}}));
