# MIN 測試與測資

## CP3 工作二：語意與文件一致性檢查

從專案根目錄執行 `python -B instructions/02_MIN/tests/check_cp3_semantics.py`。此檢查核對原 14 筆測資、規格與報告範例，執行保存的 Branch ELF，並測試語意模型的邊界及暫存器寫回；不重新編譯、不執行自訂 opcode，也不量測 cycles。來源、工具版本與結果見[工作二紀錄](../../../report/CP3_WORK2_RECORD.md)。

此目錄包含 CP1 C baseline 測試程式 [test_min.c](test_min.c)，以表格逐筆列出輸入與預期結果，共 14 組，符合至少 10 組測資的要求，並涵蓋 `INT32_MIN`、`INT32_MAX` 邊界值。

從專案根目錄執行 `make -C instructions/02_MIN/c_baseline test`，即可逐筆比對實際結果與預期值。測試結果與分析見 [CP1 報告](../report/CP1.md)。


## CP2已保存的來源重建驗證

以下結果對應[證據目錄](../references/validation/2026-10-23-gcc15/README.md)內main@e084ba0來源快照，不取代或改寫原14筆測資，也不套用至dev min_s32.S：

| 對象 | 新ELF直譯器結果 | 額外signed邊界 |
|---|---:|---:|
| C baseline min_s32 | 5,199/5,199 PASS | 49/49 PASS |
| Branch min_branch | 5,199/5,199 PASS | 49/49 PASS |
| Branchless min_branchless | 5,199/5,199 PASS | 49/49 PASS |

主機C由GCC14.2.0真正編譯執行14/14。RISC-V三函式由xPack GCC15.2.0重建ELF，再由Python RV32I子集合直譯器v1.2.1執行；不是Ripes／Spike／QEMU或真實硬體。5,199包含原14筆，額外49組另存且可能重複；不宣稱全輸入窮舉。原始保存流程回歸22/22，包含mock、fixture及歷史機器碼重播，不能當作22次真正編譯。

來源與驗證器都以相同位元組保存在source_snapshot內。快照腳本依相對路徑使用source_snapshot內的C／Branch／Branchless來源，執行入口位於該來源快照；目前rv32im目錄亦有main原始核心，但重現既有證據仍使用相同SHA的來源快照。完整重建、額外49組核對、錯誤停止及輸出保存方法見[實驗指南](../report/CP2_MIN_執行指令與實驗紀錄.md)。

直譯器不支援load/store、M擴充或pipeline／cycles；100條上限是工具預算，有限保存暫存器／返回檢查不是完整ABI認證。沒有CPU cycles、CPI或實測Speedup。已保存成功與首次CRLF假失敗run均保留原狀。

來源與原始log的直接入口見[證據索引](../references/README.md)。歷史回歸與搬遷後回歸分別保存，兩者均為22/22，不當作44次獨立來源建置。

## 原驗證工具的版本界線

本目錄的[check_cp2.py](check_cp2.py)為基底保存的v1.0原工具，沿用舊src路徑及固定build輸出，不能直接當作本次v1.2.1驗證入口。該歷史工具保留原文；目前可重現入口為證據包source_snapshot/tests/check_cp2.py及相符回歸腳本，操作方法見實驗指南。
