# MIN RV32IM — CP2

本目錄放置 MIN 的 RV32IM 組合語言實作與可重現的建置設定。

| 檔案 | 用途 |
|---|---|
| [`min_s32.S`](min_s32.S) | `min_s32` 函式，遵守 RISC-V ILP32 呼叫慣例 |
| [`min_branch.S`](min_branch.S) | main有號分支MIN，原實作保持不變 |
| [`min_branchless.S`](min_branchless.S) | main遮罩選值MIN，原實作保持不變 |
| [`Makefile`](Makefile) | 以 `riscv64-elf-gcc` 組譯並產生 ELF 物件檔與反組譯 |
| [`../report/CP2.md`](../../report/CP2.md) | 設計說明、測資對照與指令統計 |

既有Makefile描述原建置方式，會更新本目錄的物件與反組譯。重新驗證時使用[全新輸出目錄流程](../../report/CP2_MIN_執行指令與實驗紀錄.md#10-dev來源的獨立組譯與反組譯)，保留歷史產物。

預設工具鏈為 `riscv64-elf-gcc` / `riscv64-elf-objdump`。若使用其他前綴，
可執行 `make -C instructions/02_MIN/rv32im TOOLCHAIN_PREFIX=<prefix>`。

## 路徑說明

課程規範 [HOMEWORK.md §5.4](../../HOMEWORK.md) 寫的是 `src/rv32im/`；
本倉庫目前採用 `src/rv32im/`，並與 MIN 的 CP1、CP3 目錄
放在同一題目目錄中。CP2 報告明列此實際路徑，避免量測說明指向不存在的檔案。

## 補充驗證資料的來源界線

本目錄提供dev來源的min_s32.S、Makefile及既有物件／反組譯。[證據索引](../references/README.md)另保存main既有C、Branch與Branchless的來源快照及新ELF，其main原始核心亦已由3e169d5保存在本目錄。新ELF中min_s32為C編譯結果，不能將其5,199／49筆驗證視為本目錄同名Assembly已接受相同測試。功能驗證與指令計數不等於週期或時間加速。

來源、計數方法及驗證限制另見[CP2報告](../../report/CP2.md)；重新建置步驟見[實驗指南](../../report/CP2_MIN_執行指令與實驗紀錄.md)。
