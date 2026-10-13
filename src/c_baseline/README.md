# CP1 C baseline — MIN

此目錄提供 `MIN` 自訂指令的 C 語言黃金參考模型與自動化測試。

## 語意

輸入 `rs1`、`rs2` 均視為 32-bit 有號整數：

```text
rd = min(rs1, rs2)
```

實作使用固定寬度型別 `int32_t`，確保語意與 RV32 暫存器的 32-bit 有號比較一致。

## 檔案

- `min.h`：函式介面。
- `min.c`：`min_s32` 參考實作。
- `test_min.c`：14 組正常、相等、正負號與邊界測資。
- `Makefile`：編譯、測試與清理指令。

## 執行

```bash
cd src/c_baseline
make test
make clean
```

預期結果為 `14/14 tests passed.`，程式成功時回傳碼為 0；任一案例失敗時回傳非 0。
