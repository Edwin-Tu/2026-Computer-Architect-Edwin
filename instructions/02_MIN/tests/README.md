# MIN 測試與測資

此目錄包含 CP1 C baseline 測試程式 [test_min.c](test_min.c)，以表格逐筆列出輸入與預期結果，共 14 組，符合至少 10 組測資的要求，並涵蓋 `INT32_MIN`、`INT32_MAX` 邊界值。

從專案根目錄執行 `make -C instructions/02_MIN/c_baseline test`，即可逐筆比對實際結果與預期值。測試結果與分析見 [CP1 報告](../report/CP1.md)。
