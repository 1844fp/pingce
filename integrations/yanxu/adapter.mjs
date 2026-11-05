import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {readFile} from 'node:fs/promises';
import {createServer} from 'node:http';
const root='E:/AI/codex/writing-site/src/';
const files=['writing-evidence.mjs','workflow.mjs','research-audit.mjs'];
export async function manifest(){return {schema:1,mode:'real_module_offline',modelCalls:0,files:await Promise.all(files.map(async file=>({file,sha256:createHash('sha256').update(await readFile(root+file)).digest('hex')})))};}
export async function evaluate(request){
 if(!request||typeof request!=='object'||!request.input||typeof request.input!=='object')throw Error('input object required');
 const {operation,payload}=request.input;
 if(!['audit','repair'].includes(operation))throw Error('unsupported operation');
 const module=await import(pathToFileURL(root+'writing-evidence.mjs'));
 const output=operation==='audit'?module.audit(payload.bundle,payload.currentSources):module.repair(payload);
 return {output,actions:['execute_offline_contract'],trace:[{name:operation,status:'OK',mode:'real_module_offline',source:(await manifest()).files[0]}],usage:{cost:0,currency:'USD',modelCalls:0}};
}
if(process.argv[2]==='--serve'){
 const server=createServer(async(req,res)=>{
  if(req.method!=='POST'||req.url!=='/evaluate'){res.writeHead(404).end();return;}
  try{let body='';for await(const chunk of req){body+=chunk;if(Buffer.byteLength(body)>262144)throw Error('request too large');}
   const result=await evaluate(JSON.parse(body));res.writeHead(200,{'Content-Type':'application/json'}).end(JSON.stringify(result));
  }catch{res.writeHead(400,{'Content-Type':'application/json'}).end(JSON.stringify({error:'invalid_contract_request'}));}
 });server.requestTimeout=10000;server.listen(8876,'127.0.0.1');
}else if(process.argv[2]==='--manifest')console.log(JSON.stringify(await manifest(),null,2));
else if(process.argv[2]==='--stdin'){let body='';for await(const chunk of process.stdin){body+=chunk;if(Buffer.byteLength(body)>262144)throw Error('request too large');}console.log(JSON.stringify(await evaluate(JSON.parse(body))));}
