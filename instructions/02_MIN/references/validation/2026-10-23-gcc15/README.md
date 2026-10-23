# 2026-10-23 GCC15來源重建證據包

## 對象與版本

本包保存main@e084ba0既有C baseline、Branch及Branchless的驗證，不替換dev@07736e2的min_s32.S。新ELF的min_s32是C函式，與dev同名Assembly不是同一來源。核心快照未改，驗證器v1.2.1及相符回歸腳本保存原位元組。

- [新run狀態及六個來源SHA](gcc_run_fixed/run_status.json)
- [來源／產物／工具保存清單](provenance_manifest.json)
- [完整精選包SHA](package_sha256.json)
- [原main報告與歷史AI自述](historical_main_CP2.txt)

## 結果與可重現來源

| 類別 | 保存結果 | 界線 |
|---|---|---|
| 主機C原生重編執行 | 14/14 | GCC14.2.0 |
| 新RISC-V ELF直譯 | 三函式各5,199/5,199 | xPack GCC15.2.0／GNU2.45；非週期模擬 |
| 額外signed邊界 | 各49/49，共147次 | 另存JSON，非預設入口自動測項 |
| 原流程回歸 | 22/22 | 含mock／fixture／保存機器碼重播 |
| 反組譯比較 | 13組位址／機器碼一致 | 歷史ELF未提交，不能比整檔 |

[維護驗證器](source_snapshot/tests/check_cp2.py)、[回歸腳本](source_snapshot/tests/test_cp2_flow.py)、[原C](source_snapshot/c_baseline/min.c)、[Branch](source_snapshot/rv32im/min_branch.S)與[Branchless](source_snapshot/rv32im/min_branchless.S)保存實際來源。歷史[反組譯](source_snapshot/references/disassembly_gcc16.txt)、[測量JSON](source_snapshot/references/measurements.json)保持原位元組；不是重新產生的舊證據。

驗證腳本位於source_snapshot，依其相對路徑讀取對應來源。[完整指南](../../../report/CP2_MIN_執行指令與實驗紀錄.md)說明新run與工具前提。缺檔、缺工具、編譯或測試失敗不得算PASS；輸出不得寫入本包或覆寫舊檔。

## 精選與原始性

新ELF僅5,080 bytes，保留以支持機器碼核對。主機EXE、工具鏈、安裝包與重複ZIP未納入。原始artifacts_sha256.json覆蓋原run，包含未選入EXE；精選包以package_sha256.json為準，manifest本身不自我雜湊。原始log內的絕對路徑是當時紀錄，不是現在的導覽或重現前提。

首次CRLF假失敗、LLVM不支援目標與後續GNU成功紀錄分開保存；沒有將舊失敗改成成功。原始log／歷史報告含當時工具提醒與舊路徑，作證據保留，不作目前操作入口或更新後的分工敘述。

本包只包含組內MIN來源及驗證證據，工作分工見[CP2貢獻聲明](../../../report/CP2_CONTRIBUTIONS.md)；來源與原始測試歸屬保持獨立。沒有Ripes／Spike／QEMU／硬體、cycles或Speedup結果。全部導覽採專案內相對路徑，與對應來源及工具版本一同保存。

## 整合位置回歸檢查

路徑搬遷後另跑流程回歸22/22、退出碼0，見[新回歸log](integration_check/relocated_flow_raw.log)及[新執行狀態](integration_check/relocated_flow_status.json)。這是新位置的流程測試，不是重新跑RISC-V編譯或重算額外49組；原22項log保持不變。

historical_main_CP2.txt以原報告位元組保存，內文的舊相對路徑與待審查語句屬歷史原文，不作目前文件導覽。本包所有新導覽使用現在的相對路徑。
