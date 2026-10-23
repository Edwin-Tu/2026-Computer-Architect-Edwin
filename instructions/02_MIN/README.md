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

## 小組資訊

- 組名：待全組確認（題目目錄：`02_MIN`）
- 組長及組員：請見 [個人貢獻聲明](CONTRIBUTIONS.md)
- 分支：依課程規定使用 `dev/<學號>`

## 成果索引

| 項目 | 內容 |
|---|---|
| CP1 C baseline | [C 參考實作](c_baseline/README.md)、[測試與測資](tests/README.md)、[CP1 報告](report/CP1.md) |
| CP2 RV32IM | [目錄說明](rv32im/README.md)、[CP2 報告](report/CP2.md) |
| CP3 指令規格與編碼 | [目錄說明](spec/README.md) |
| 參考資料 | [目錄說明](references/README.md) |
