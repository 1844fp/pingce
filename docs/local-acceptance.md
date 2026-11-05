# 本机验收

仅本机单用户MVP，不接组织SSO，不调用模型。Docker/PostgreSQL/SSO不是本机阻塞项。先在唯一项目根E:/Codex/评测中台运行：

```powershell
.venv/Scripts/python.exe scripts/doctor.py --report reports/doctor-latest.json
.venv/Scripts/python.exe -m pytest tests/test_doctor.py -q --basetemp=work/doctor-tests
```

doctor默认只读：检查当前Python及requirements锁定发行版版本、Node命令存在、前端dist/index和JS资源、五个固定适配器及业务源码依赖文件存在。固定业务根E:/AI/codex/writing-site，图谱源码根E:/AI/codex/agent-team。读取源码存在性，不导入API/适配器、不读取凭证或数据库、不运行模型/搜索、不启动服务。报告仅允许项目根内（解析符号链接后校验）；stdout为JSON，PASS退出0，必要项FAIL退出1，非法参数退出2。检查不证明文件完整性、Node版本兼容、服务健康或业务验收通过。api_health明确NOT_CHECKED；本版不发HTTP请求。

需要平台闭环时由操作者另行启动现有本机服务，然后：

```powershell
.venv/Scripts/python.exe scripts/run_offline.py --suite all --report reports/offline-latest.json
```

现有run_offline共19例，默认NEEDS_REVIEW属于预期的非零退出，不等于运行错误，也不能自动批准。逐项区分目标执行失败、评分失败和待人工复核，保留原始API报告。doctor通过不代替这19例验收，不代替人工事实和写作质量审核。服务不自动启动，运行中已有网站不要重启。

专属实现偏离：API健康为可选，本版明确不检查；不引入网络探测和凭证。隔离测试用临时根与假文件/注入版本探针，不依赖实际业务源码。
验证记录（2026-11-06）：专属tests/test_doctor.py两项pytest通过；使用项目venv实际调用inspect，status=PASS、failed=[]、api_health=NOT_CHECKED。该结果仅为当前本机前置检查，不代表19例或人工复核通过。
