# PostgreSQL离线准备
当前API/Worker仍为SQLite；未连接、运行或切换PostgreSQL。
infra/postgres/001_initial.sql为v1空目标初始DDL：四表TEXT主键、项目幂等键UNIQUE(project,idem)、样本UNIQUE(run_id,case_id,repetition)、results/reviews引用runs，无级联删除。reviews允许重复样本复核以保留历史，不新增结果外键。
JSON文本映射JSONB；epoch秒保留DOUBLE PRECISION；整数映射BIGINT。JSONB规范化对象键顺序，因此原始JSON字节不保留，digest字段原样复制，不重新签算。导出器拒绝无效/重复键JSON、非有限值、NUL、无效Unicode、NULL主键、孤儿记录及重复业务键。
运行 python infra/postgres/export_sqlite.py work/synthetic.sqlite work/postgres-export-v1。源需明确指定备份/合成SQLite，mode=ro单读事务；产生snapshot.json/data.sql，仅输出行数，无凭证或网络。已有输出拒绝覆盖。不自动读取默认业务库。SQL需在空隔离目标按001 DDL后人工导入，当前不执行它。
测试 python -m pytest tests/test_postgres_contract.py -q：合成SQLite验证行数/JSON/转义/唯一键/FK/追加复核历史。SQLite执行等价DDL不代表PostgreSQL真实语法和JSONB/并发验收。
源仅导出四业务表；父会话管理schema_migrations等SQLite元数据。四表列变化拒绝，需要新版本DDL/导出规则。未来仍需隔离PostgreSQL实测、锁和队列认领语义、驱动/占位符适配、停写备份、切换回滚；本阶段均未完成。
偏离说明：仅标准库离线转换，无新增驱动、服务、模型或网络；未改main.py。此文件记录本专属任务偏离，避免写公共implementation-notes产生冲突。
实际验证（2026-11-05）：.venv/Scripts/python.exe -m pytest tests/test_postgres_contract.py -q --basetemp=work/postgres-test-temp，3 passed。系统python缺pytest，系统临时目录存在访问拒绝，因此使用项目venv和项目内临时目录。没有对真实服务执行DDL/导入。
