# 架构与契约

浏览器 → FastAPI（API 与静态站点） → SQLite（不可变资源、运行队列、结果） ← 单 Worker → fixture / 允许的 HTTP 目标。

## 数据与版本

resources 保存 dataset、target，不提供更新和删除接口。每次 POST 生成新版本 ID。
dataset 必须声明 snapshot，样本 ID 不重复。run.spec 冻结数据集、目标、评分器 rules-v1 与执行参数。
results 以 run_id + case_id + repetition 唯一，保留执行耗时、评分、证据和响应。
SQLite DDL 初始化采用 IF NOT EXISTS；后续改表必须引入有序迁移，不可直接改已有表含义。

## 状态机

QUEUED → RUNNING → COMPLETED；QUEUED/RUNNING → CANCELLED；RUNNING → ERROR。
COMPLETED 表示样本均已尝试，不等于质量通过。样本可为 PASS、FAIL、ERROR。
ERROR 的 error_type 为 TARGET_ERROR 或 EVALUATOR_ERROR。
门禁仅在 COMPLETED 且所有预期样本 PASS 时通过；取消、中断、排队均为 INCOMPLETE。
进程重启将 RUNNING 标记 ERROR，不重放不确定副作用。QUEUED 继续等待。

## 幂等与派发

BEGIN IMMEDIATE 事务内按项目和幂等键检查，比较规范化请求摘要，再写 QUEUED。
运行表即队列，不存在事务提交后向 Redis 派发失败的间隙。相同键不同内容返回 409。
Worker 事务领取单个任务，逐样本提交。取消在调用间以及结果提交前检查，不保留取消后的迟到结果。
HTTP timeout 为连接/读写超时，不是跨服务硬截止时间。当前无法强杀已发送请求。

## 资源限制与信任

单数据集至多 500 样本，最多重复 5 次；资源 JSON 上限约 2MB；HTTP 响应读取后检查 2MB。
响应目前先缓冲再检查大小，生产需流式字节上限、入口请求体上限、出口代理和地址解析约束。
白名单是操作员配置的主机信任范围，不能替代网络沙箱；不允许不可信用户管理目标主机。
没有任意代码评分器执行接口，避免将用户代码运行在 API 进程。
当前不提供认证；X-Project 是本地开发组织维度，客户端可自行填写。

## 核心 API

POST /api/v1/datasets；POST /api/v1/targets；GET /api/v1/resources/{dataset|target}。
POST /api/v1/runs（必填 Idempotency-Key）；GET /api/v1/runs；GET /api/v1/runs/{id}。
POST /api/v1/runs/{id}/cancel；GET /api/v1/comparisons?baseline=...&candidate=...。
完整字段、校验和 OpenAPI 可在运行时 /docs 与 /openapi.json 获取。
