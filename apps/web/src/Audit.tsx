import {useEffect,useState} from 'react';
export function Audit({api}:{api:(path:string,body?:any)=>Promise<any>}){
 const [data,setData]=useState<any>(null),[error,setError]=useState('');
 async function refresh(){try{setData(await api('audit'));setError('')}catch(e){setError((e as Error).message)}}
 useEffect(()=>{refresh()},[]);
 return <section className="panel"><h2>操作记录</h2><p className="muted">记录资源发布、实验创建、取消、复核和报告归档。这里只记录动作与资源标识，不记录令牌或稿件正文；本地哈希链不等于实名签名。</p><button onClick={refresh}>刷新记录</button>{error&&<p className="error" role="alert">{error}</p>}{data&&<><p>记录 {data.total} 条 · 链校验 {data.chain_valid?'通过':'失败，请检查数据库'}</p>{data.events.slice().reverse().map((e:any)=><details key={e.event_id}><summary><span>{e.action}</span><small>{new Date(e.created*1000).toLocaleString('zh-CN')}</small></summary><p>资源 {e.resource_id}</p><pre>{e.metadata}</pre><small>SHA256 {e.sha256}</small></details>)}</>}</section>
}
