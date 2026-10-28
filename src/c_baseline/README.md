# MIN C baseline — CP1

此目錄提供 `MIN` 自訂指令的 C 語言參考實作。輸入 `rs1`、`rs2` 均為 32-bit 有號整數，函式回傳兩數中較小者：

```text
rd = min(rs1, rs2)
```

## 檔案與測試

- `min.h`：函式介面。
- `min.c`：`min_s32` 參考實作。
- [測試程式與 14 組測資](../tests/test_min.c)：涵蓋一般、相等、正負號及 32-bit 邊界值。
- `Makefile`：編譯、測試與清理指令。

## 執行

在專案根目錄執行：

```bash
make -C instructions/02_MIN/c_baseline test
make -C instructions/02_MIN/c_baseline clean
```

測試成功時程式回傳碼為 0；任一案例失敗時回傳非 0。
