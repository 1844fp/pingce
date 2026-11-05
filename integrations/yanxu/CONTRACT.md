# Stable Worker contract — offline-v1

Python entry: integrations.yanxu.adapter.execute(case, spec). spec={} or {"version":"offline-v1"}. Returns output/actions/trace/usage. Raises ValueError for invalid contract; subprocess timeout is a target error. Do not convert exceptions to PASS. Worker calls this directly; HTTP bridge is optional.

case.input must be an object {operation,payload}. Whitelist: audit and repair only. Module is fixed to E:/AI/codex/writing-site/src/writing-evidence.mjs. No caller-controlled executable, module, filesystem path, model or URL. Node is invoked with an argument list, shell=False, timeout=15 seconds. context is not interpreted. No regression injection implemented.

Baseline case: {"input":{"operation":"audit","payload":{"bundle":{"claims":[]},"currentSources":[]}}}. Expected output {"status":"awaiting_author","issues":[],"affectedLocations":[]}. Real-module offline execution, zero model calls; empty baseline only proves wiring. Negative evidence baseline: claims=[{id:"c1",kind:"plan",locations:["p1"],evidence:[]}] produces missing_evidence.

repair payload: {paragraphs,sourceVersion,review,edits,round?}; review requires matching sourceVersion and issues with id,acceptance,basis,location,quote. This returns revised in-memory paragraphs only. No business state is saved.

## Frozen target manifest API

Python `get_manifest()` returns JSON-safe {schema,version,mode,files}, hashing fixed source files plus both adapters. At Target creation persist this value in `spec.manifest`; use `spec.version="offline-v1"`. `execute(case,spec)` compares the complete manifest before execution and checks again after execution. Drift raises ValueError (target error); do not silently refresh a frozen Target. Create a new Target version instead. For legacy direct callers spec={} is accepted, but only specs with manifest are frozen targets. This is detection around execution, not an immutable filesystem snapshot.

Quality scorer receives the complete response; business result is response.output. Actions are ["execute_offline_contract"]. trace mode is real_module_offline; appended manifest trace records the executed source set. audit output status needs_review is a business finding, not transport failure. awaiting_author does not mean academic truth verified. Missing/malformed fields may raise target errors.

## Final Worker specification (supersedes earlier spec-only examples)
execute(case, runtime_spec) accepts the full Worker spec. runtime_spec.target contains only version (default offline-v1), manifest (get_manifest result), mode (correct or regression). Other outer Worker keys are ignored. runtime_spec.timeout_seconds defaults to 15 and must be numeric >0 and <=120. Legacy flat specs remain supported.

correct executes the actual offline function. regression executes it first, then deliberately clears output.issues (or replaces non-audit output with {injected_error:true}); sets injected_regression=true and appends trace {name:regression_injection,status:INJECTED,mode:simulation}. This is explicit synthetic regression injection, never evidence of genuine module regression. No source edits or automatic repair. Eight tests passed including full Worker spec, frozen manifest, and explicit regression injection. Parent persists get_manifest() at Target creation under spec.target.manifest; adapter rejects drift before invocation and detected changes afterward. Latest callable Python manifest is authoritative; static manifest.json is the earlier inspection snapshot.

Final compatibility correction: target accepts standard name/adapter/revision/url metadata in addition to version/mode/manifest. adapter, when provided, must equal yanxu-local; URL is ignored and never fetched. Unknown target keys (including command) are rejected. Complete real Target structure, wrong adapter and arbitrary command rejection tested: 9 tests passed. manifest.json refreshed using Python get_manifest() after this code change; it now uses the same schema as the Worker freeze API. Existing frozen targets must be recreated because adapter source hash changed.
