import {useState} from 'react';
export function AccessSettings(){
 const [project,setProject]=useState(sessionStorage.getItem('eval-project')||'default');
 const [token,setToken]=useState(sessionStorage.getItem('eval-token')||'');
 return <section className="panel prose"><h2>连接工作空间</h2><p>服务启用访问令牌时，在此填写管理员分配的令牌与项目。未启用时令牌可留空。令牌仅保存在当前标签页会话中，不写入项目源码。</p><div className="stack"><label>项目<input value={project} onChange={e=>setProject(e.target.value)}/></label><label>服务访问令牌<input type="password" autoComplete="off" value={token} onChange={e=>setToken(e.target.value)}/></label><div className="button-row"><button className="primary" disabled={!project.trim()} onClick={()=>{sessionStorage.setItem('eval-project',project.trim());sessionStorage.setItem('eval-token',token);location.reload()}}>应用连接</button><button onClick={()=>{sessionStorage.removeItem('eval-token');sessionStorage.removeItem('eval-project');location.reload()}}>清除连接</button></div></div><p>这是本地服务令牌权限控制，尚未接入组织登录或 SSO；复核记录不代表已认证个人签名。</p></section>
}
