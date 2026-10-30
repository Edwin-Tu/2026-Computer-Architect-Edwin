# MIN — 兩數取小

| 項目 | 內容 |
|---|---|
| 指令名稱 | `MIN` |
| 題目類別 | 基礎運算類 |
| 運算元類型 | 二元 |
| 輸入定義 | `rs1`、`rs2` 為 32-bit 有號整數 |
| 語意公式 | `rd = min(rs1, rs2)` |

正式語意與測試向量見 [HOMEWORK.md 第六節](../../HOMEWORK.md#六題目語意規格)。

本組選題為 `MIN`。此指令只比較兩個有號整數並回傳較小值；相等時回傳該共同值。CP1 C baseline、測試與報告請見下方連結。

## 專題與分工

- 題目目錄：`02_MIN`。
- [CP2分工與貢獻比例](./report/CP2_CONTRIBUTIONS.md)。
- 整合基底：`3e169d5`（包含main `e084ba0`與dev既有成果）。
- dev原min_s32來源：`07736e2`；main驗證來源：`e084ba0`。

## 成果索引

| 項目 | 內容 |
|---|---|
| CP1 C baseline | [C 參考實作](c_baseline/README.md)、[測試與測資](tests/README.md)、[CP1 報告](report/CP1.md) |
| CP2 RV32IM | [目錄說明](rv32im/README.md)、[CP2 報告](report/CP2.md) |
| CP3 指令規格與編碼（後續階段，非已完成聲明） | [目錄說明](spec/README.md) |
| 參考資料 | [目錄說明](references/README.md) |

## CP2驗證與文件

保留本分支的[min_s32.S導覽](rv32im/README.md)。main既有C／Branch／Branchless的新來源建置證據另有[索引](references/README.md)，不取代本分支核心，也不把其5,199／49筆結果套用到dev min_s32.S。流程回歸保存22/22；目前沒有週期或實測Speedup。

- [測試分類與結果](tests/README.md)
- [實驗指南](report/CP2_MIN_執行指令與實驗紀錄.md)
- [文件維護與證據說明](report/CP2_MAINTENANCE.md)

CP2分工與25%比例列於貢獻聲明；文件整理、MIN核心實作及重新建置的工作範圍分別記錄，不以工具或commit數重新分配成果。
