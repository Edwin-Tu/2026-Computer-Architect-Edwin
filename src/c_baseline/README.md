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

Linux/macOS 或已安裝 GNU make 與 C 編譯器的環境，在專案根目錄執行：

```bash
make -C src/c_baseline test
make -C src/c_baseline clean
```

測試成功時程式回傳碼為 0；任一案例失敗時回傳非 0。`test` 會建立本目錄的測試執行檔；`clean` 只清除該建置目標，不可套用到保存證據目錄。Windows MinGW 應明確使用 `TARGET=test_min.exe` 執行 test 與 clean，讓清理目標與實際執行檔一致；工具寫法見 [CP1 報告](../../report/CP1.md#3-結果與分析)。

若要完全不在工作樹產生產物，先將 `min.c`、`min.h`、`Makefile` 及 `../tests/test_min.c` 複製至全新的暫存副本，保留 `src/c_baseline/` 與 `src/tests/` 相對結構，再對該副本執行相同的 `test`／`clean`。本次驗收採此方式；不把測試執行檔提交。
