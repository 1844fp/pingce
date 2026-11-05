# 覆盖说明

## 8个可执行用例
均为合成输入，实际执行 writing-evidence 的本地纯函数；不是生成论文或核验真实文献。

- real-normal：正常来源版本/hash/定位，issues 为空，仍等待作者审核。
- real-missing-evidence：缺证据，检查 missing_evidence 与受影响位置。
- real-stale-hash：旧来源 hash，检查 stale_source 与受影响位置。
- real-missing-locator：缺定位，检查 missing_locator。
- real-unconfirmed：作者结果未经确认，检查 unconfirmed_result。
- real-number-conflict：同口径数字冲突，检查 number_conflict 与两个位置。
- real-target-edit：只更新指定段落，背景段保持原样。
- real-keep-marker：定点修改保留数据待核验标记。

前6例断言 status/issues/affectedLocations；后2例断言 status/paragraphs。全部保留 NEEDS_REVIEW。它们不能证明文献真实、引用语义支持、无新编数值、语言自然或整站工作流可靠。

## 14个待实现业务契约
cases.v1.json 为完整契约与风险/来源信息，import.v1.json 为带 checks/evaluation 的平台格式。评分器测试仅用合成结构输出验证规则，不代表实际业务执行。

- no-reference / no-number：不编造题录和数值。
- preserve-number：保留3组、2025年、12%等已确认数字。
- insufficient-source：仅题录不能充当全文支持。
- target-edit：定点修改与方法保护。
- topic-discipline / topic-empty：选题硬约束及无可选候选。
- graph-unverified：未审核图谱关系不能提升为因果证据。
- retrieval-empty：零命中不能推断不存在或伪造。
- quote-gap / citation-lock：连续摘录与引用保护。
- cancel / resume / resume-ambiguous：取消、恢复与章节歧义。

需分别接入对应实际模块并取得可信字段和轨迹后才可升级为可执行验收；不得将 instruction 直接发送给当前 audit/repair 适配器。实际生成写作质量仍需人工复核。取消恢复、选题、图谱及知识检索端到端目前不在8例已执行覆盖范围。
