# 本机版完成验收

2026-11-06，按用户最新选择：本机运行、暂不接组织SSO、暂不调用模型。当前本机实施范围已完成；真实论文事实判断仍是人工工作，不由测试替代。

## 已完成闭环

五组19项可执行合成用例 → 冻结版本 → 持久队列与单Worker → 实际模块/编排 → 确定性评分 → 人工复核 → 门禁 → 版本对比 → 失败回归集 → 持久报告产物 → 操作记录 → 整包备份恢复。
支持可选服务令牌项目/读写权限，SQLite有序迁移，运行中取消保护及中断恢复。没有自动批准内容，没有调用真实模型。

## 本机使用

1. `.venv/Scripts/python.exe scripts/doctor.py --report reports/doctor-latest.json`：只读自检，本次PASS。
2. 运行 `start.ps1`，打开 http://127.0.0.1:8765。
3. “写作验收”选择范围，准备并执行；19项结构检查零失败，内容保持NEEDS_REVIEW，作者按证据复核。
4. “导出证据报告”先归档到data/artifacts，随后校验下载；操作记录页显示发布、执行、取消、复核与报告归档。
5. `.venv/Scripts/python.exe scripts/run_offline.py --suite all --report reports/local-complete-offline.json`：五组均COMPLETED，8/4/2/2/3待复核，0失败，预期退出1，不是执行异常。

## 完整备份恢复

```powershell
.venv/Scripts/python.exe scripts/backup_local.py backup --destination backups/local-new
.venv/Scripts/python.exe scripts/backup_local.py restore --source backups/local-new --destination backups/recovered-new
```

目标目录必须不存在；包含evaluation.db、产物及其完整性密钥、逐文件SHA256清单。恢复核验清单，旧未完成任务标ERROR，不自动重放。
恢复运行时先停本项目服务，配对设置EVAL_DB指向recovered-new/evaluation.db、EVAL_ARTIFACT_ROOT指向recovered-new/data/artifacts，再运行start.ps1。不自动覆盖原库。备份包含密钥，请保护目录。
2026-11-06实际演练：backups/local-20261106-023832 → backups/local-restored-20261106-023832，3个文件恢复，已重新读取归档文件且完整性通过。数据库仍使用原运行库，没有切换恢复副本。

## 验收证据

全量72项pytest通过（仅有TestClient依赖弃用提示），前端生产构建通过；两个子会话交付完成。运行库已应用v2审计迁移，原数据保留。

报告 reports/doctor-latest.json、reports/local-complete-offline.json、reports/local-final-report.json。
浏览器 tests/browser_local_complete.py 验证评测、归档下载、审计链及移动端，未发现pageerror；截图docs/local-audit.png。
审计为本地事务记录和可检查哈希链，不是实名签名或独立不可篡改日志。产物为本地文件库与HMAC校验，不是远程对象存储。备份为本地副本，不是异地容灾。

## 非当前验收范围

组织SSO、真实模型/论文质量、真实PostgreSQL切换、Docker部署、多Worker租约、S3服务、外部提供方请求撤销等保留可选扩展，不再作为当前本机单用户版的阻塞项。已有PostgreSQL/容器制品仍仅完成离线准备和静态验证，不能据此宣称生产系统已上线。
