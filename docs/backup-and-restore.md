# 本地备份与恢复

工具使用 SQLite 在线 backup API，包含 WAL 中已经提交的内容；不直接复制正在写入的主文件。目标必须是项目内的新文件，已存在则拒绝，不覆盖当前业务库。

```powershell
.venv/Scripts/python.exe scripts/backup_database.py backup --source evaluation.db --destination backups/manual-001.db
.venv/Scripts/python.exe scripts/backup_database.py restore --source backups/manual-001.db --destination backups/recovered-001.db
```

输出包含SHA256、四张表的行数和恢复时中断的任务数。恢复副本中的QUEUED/RUNNING改为ERROR，避免自动重复调用；备份文件本身不修改。COMPLETED、结果、复核依据保持原值。

需要实际启用恢复副本时，先停止本项目API与Worker，在启动终端设置EVAL_DB指向恢复副本，再运行start.ps1；该操作不会自动执行，亦不替换原库。重开终端时需重新确认EVAL_DB。

2026-11-05 实际演练：源库32条资源、18次实验、73条结果、3条复核，备份和新文件恢复的计数一致；两文件SHA256均为2a2b17310f6c3df15a323490997b9098c06d645a48ac33c32d1ba449cb47f949。文件位于backups/evaluation-20261105-133001.db和backups/restored-20261105-133001.db；未替换运行中的evaluation.db。

另有自动测试覆盖WAL、复核保留、未完成任务转ERROR、拒绝覆盖和错误来源清理。开发时发现SQLite连接上下文不会自动close，已显式关闭，防止Windows文件锁阻止清理。

本地副本位于同一磁盘，不属于异地容灾；未提供备份加密或保留期策略。
