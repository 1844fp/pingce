import {pathToFileURL} from 'node:url';
globalThis.fetch=async()=>{throw Error('network forbidden');};
const root='E:/AI/codex/writing-site/src/';
const {makeProject}=await import(pathToFileURL(root+'core.mjs'));
const {executeWorkflow}=await import(pathToFileURL(root+'workflow.mjs'));
let text='';for await(const c of process.stdin)text+=c;
const {operation}=JSON.parse(text).input;
if(!['references','missing_material','resume_parameters_changed','resume_input_changed'].includes(operation))throw Error('unsupported scenario');
const p=makeProject({title:'SYNTHETIC ONLY'});let search_calls=0,model_calls=0,saves=0,error_code=null;
const run=(stage,options)=>executeWorkflow({project:p,stage,options,credentials:{},save:async()=>{saves++;},emit:()=>{},search:async()=>{search_calls++;return [{title:'SYNTHETIC RECORD',synthetic:true}];},model:async()=>{model_calls++;throw Error('model forbidden');},legacy:async()=>{throw Error('legacy forbidden');}});
try{
 if(operation==='missing_material')await run('draft',{});
 else{await run('references',{query:'SYNTHETIC'});
 if(operation==='resume_parameters_changed')await run('references',{resume:true,query:'CHANGED'});
 if(operation==='resume_input_changed'){p.profile.title='CHANGED';await run('references',{resume:true});}}
}catch(e){error_code=e.code||e.message;}
const expected={references:null,missing_material:'workflow.requirements',resume_parameters_changed:'workflow.parameters_changed',resume_input_changed:'workflow.input_changed'}[operation];
const output={scenario:operation,status:error_code?'rejected':'completed',error_code,search_calls,model_calls,saves,checks:{expected_error:error_code===expected,no_model:model_calls===0,search_count:search_calls===(operation==='missing_material'?0:1)}};
console.log(JSON.stringify({output,actions:['execute_synthetic_workflow'],trace:[{name:'executeWorkflow',status:'OK',mode:'real_orchestration_synthetic_dependencies'}],usage:{cost:0,currency:'USD',modelCalls:model_calls}}));
