# MIN RV32IM — CP2

本目錄放置 MIN 的 RV32IM 組合語言實作與可重現的建置設定。

| 檔案 | 用途 |
|---|---|
| [`min_s32.S`](min_s32.S) | `min_s32` 函式，遵守 RISC-V ILP32 呼叫慣例 |
| [`min_branch.S`](min_branch.S) | main有號分支MIN，原實作保持不變 |
| [`min_branchless.S`](min_branchless.S) | main遮罩選值MIN，原實作保持不變 |
| [`Makefile`](Makefile) | 以 `riscv64-elf-gcc` 組譯並產生 ELF 物件檔與反組譯 |
| [CP2 報告](../../report/CP2.md) | 設計說明、測資對照與指令統計 |

既有Makefile描述原建置方式，會更新本目錄的物件與反組譯。重新驗證時使用[全新輸出目錄流程](../../report/CP2_MIN_執行指令與實驗紀錄.md#10-dev來源的獨立組譯與反組譯)，保留歷史產物。

預設工具鏈為 `riscv64-elf-gcc` / `riscv64-elf-objdump`。Makefile 的現行路徑是 `src/rv32im/`。例如在 Linux/macOS 的全新暫存專案副本根目錄中，使用下列命令（前綴依已安裝工具替換）：

```bash
make -C src/rv32im TOOLCHAIN_PREFIX=riscv64-unknown-elf-
```

此命令會寫入副本的 `min_s32.o` 與反組譯，不能在保存歷史產物的正式工作樹直接重跑。Windows GNU make 對應為 `mingw32-make`；含空白工具路徑時可用加引號的 `AS` 與 `OBJDUMP` 變數。跨平台、不依賴 Makefile 的全新輸出目錄流程見 [CP2 實驗指南第 10 節](../../report/CP2_MIN_執行指令與實驗紀錄.md#10-dev來源的獨立組譯與反組譯)。組譯成功只證明物件可建立，不能冒稱已執行 dev 函式測試。

## 路徑說明

課程規範 [HOMEWORK.md §5.4](../../HOMEWORK.md) 寫的是 `src/rv32im/`；
目前 MIN 的 C 與 Assembly 分別在 `src/c_baseline/`、`src/rv32im/`，測試在 `src/tests/`；CP1／CP2／CP3 報告集中於根目錄 `report/`，唯一完整語意規格在 `instructions/MIN/README.md`。舊 `instructions/02_MIN/` 不再作為現行操作路徑。

## 補充驗證資料的來源界線

本目錄提供dev來源的min_s32.S、Makefile及既有物件／反組譯。[證據索引](../references/README.md)另保存main既有C、Branch與Branchless的來源快照及新ELF，其main原始核心亦已由3e169d5保存在本目錄。新ELF中min_s32為C編譯結果，不能將其5,199／49筆驗證視為本目錄同名Assembly已接受相同測試。功能驗證與指令計數不等於週期或時間加速。

來源、計數方法及驗證限制另見[CP2報告](../../report/CP2.md)；重新建置步驟見[實驗指南](../../report/CP2_MIN_執行指令與實驗紀錄.md)。
