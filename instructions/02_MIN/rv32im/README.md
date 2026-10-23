# MIN RV32IM — CP2

本目錄放置 MIN 的 RV32IM 組合語言實作與可重現的建置設定。

| 檔案 | 用途 |
|---|---|
| [`min_s32.S`](min_s32.S) | `min_s32` 函式，遵守 RISC-V ILP32 呼叫慣例 |
| [`Makefile`](Makefile) | 以 `riscv64-elf-gcc` 組譯並產生 ELF 物件檔與反組譯 |
| [`../report/CP2.md`](../report/CP2.md) | 設計說明、測資對照與指令統計 |

從專案根目錄建置：

```sh
make -C instructions/02_MIN/rv32im
```

預設工具鏈為 `riscv64-elf-gcc` / `riscv64-elf-objdump`。若使用其他前綴，
可執行 `make -C instructions/02_MIN/rv32im TOOLCHAIN_PREFIX=<prefix>`。

## 路徑說明

課程規範 [HOMEWORK.md §5.4](../../../HOMEWORK.md) 寫的是 `src/rv32im/`；
本倉庫目前採用 `instructions/02_MIN/rv32im/`，並與 MIN 的 CP1、CP3 目錄
放在同一題目目錄中。CP2 報告明列此實際路徑，避免量測說明指向不存在的檔案。
