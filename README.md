# 衡尺 · AI写作评测中台

本机单用户评测平台：数据集版本、异步执行、规则评分、人工复核、门禁、版本对比、失败回归集、产物归档与审计。

## 版本

- `versions/v1.0.0-local`：当前已验收的本机源码快照。
- `versions/v1.0.1-local`：同一业务实现，加GitHub使用说明、便携CI与版本清单。
- `main`：最新仓库版本。历史阶段并非独立可还原源码，详见CHANGELOG.md。

## 安装与运行

需要Python 3.11+、Node.js 20.19+。

```powershell
python -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements-dev.txt
Set-Location apps/web
npm.cmd ci
npm.cmd run build
Set-Location ../..
.venv/Scripts/python.exe run.py
```

打开 http://127.0.0.1:8765 。默认本地无认证；可选作用域服务令牌见docs/runtime-preparation.md。不要直接作为公网生产服务部署。

通用fixture/HTTP评测可以独立使用。完整五组写作适配器依赖作者本机 `E:/AI/codex/writing-site` 和图谱模块；这些是独立项目，未打包进本仓库。缺少它们时，不应宣称完整写作端到端可运行。脚本 `scripts/doctor.py` 会检查依赖。

## 验证

原作者本机全量72项pytest和浏览器验收通过；五组19个合成用例结构零失败，内容均保留NEEDS_REVIEW，并非真实模型质量通过。GitHub CI只运行可移植平台测试与前端构建，不调用模型，也不冒充本地写作适配器验收。

完整操作见docs/local-completion.md；当前实现边界见docs/current-status.md。数据库、产物密钥、令牌、运行报告、截图和备份不入库；文档中的本机报告路径是验收记录，需在自己的环境重新生成。

未执行真实模型评测、组织SSO、真实PostgreSQL切换或容器运行验收。容器与PostgreSQL文件是准备制品，不代表生产上线。
