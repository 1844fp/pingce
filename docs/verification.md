# 验收记录

日期：2026-11-04（Asia/Shanghai）。本机 Windows、Python 3.13、Node.js；仅验证本地单用户版。

## 已通过

- `python -m pytest -q`：6 passed。测试库在 conftest 导入前设置独立临时 DB。
- 覆盖：完整执行与退化对比、幂等重放和冲突、项目归属筛选、调用预算、排队取消、模拟超时、Worker 中断恢复、重复样本拒绝、目标白名单、真实 HTTP 收发及不泄露参考答案、禁止动作评分。
- `npm run build`：TypeScript 编译和 Vite 生产构建通过。
- `tests/browser_acceptance.py`：无界面 Edge 在运行中的 API + 独立 Worker 上完成发布数据集、注册目标、基线 3/3、退化 2/3、逐样本对比下降 33.3 个百分点。
- 390px 移动视口无整页横向溢出；浏览器没有 pageerror。
- 已查看工作台截图，主要控件与结果显示正常。截图见 workbench.png、mobile.png。

## 限制与未验证

- 6 项测试是组合场景，不等于生产全面覆盖；运行中远程请求强制撤销、多 Worker、网络分区和大数据量未验证。
- HTTP 测试是真实本地服务；浏览器目标明确使用 fixture，不代表真实 Agent 的质量。
- 禁止动作只检查目标声明，不能证明实际工具执行合规。
- 测试依赖存在 Starlette 对 httpx TestClient 的弃用提示，不影响本次通过；后续升级时适配。
- 未接真实数据中台、业务 Agent、SSO、模型评分和生产流水线。
- 本地数据库保留浏览器验收及早期测试记录；源码压缩包不含数据库，解压启动为空白实例。

## 重现

按 README 启动，在项目虚拟环境安装 `playwright==1.64.1`，确保本机已安装 Edge，然后运行 `python tests/browser_acceptance.py`。
该脚本显式创建带“浏览器验收”名称的模拟资源和实验，可反复执行。
