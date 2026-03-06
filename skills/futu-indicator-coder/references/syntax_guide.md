# 富途牛牛指標語法指南 (Futu Syntax Guide)

富途牛牛使用類通達信 (TDX) 的腳本語言。以下是編寫自定義指標的核心規則。

## 1. 賦值符號 (Assignment)
- `:=` : **隱含賦值**。計算結果不會顯示在圖表上。用於中間變數。
- `:` : **顯示賦值**。計算結果會直接在圖表（主圖或副圖）上畫線。

## 2. 常用核心函數
- `MA(X, N)`: X 的 N 日簡單移動平均。
- `EMA(X, N)`: X 的 N 日指數移動平均。
- `REF(X, N)`: 引用 X 在 N 個週期前的值。
- `HHV(X, N)` / `LLV(X, N)`: X 在 N 個週期內的最高值 / 最低值。
- `CROSS(A, B)`: A 向上突破 B。
- `IF(COND, A, B)`: 如果 COND 為真則返回 A，否則返回 B。
- `ABS(X)`: X 的絕對值。
- `STD(X, N)`: X 的 N 日估計標準差。
- `BARSLAST(COND)`: 上一次條件成立到現在的週期數。
- `COUNT(COND, N)`: 統計 N 週期內條件成立的次數。

## 3. 繪圖與圖標
- `DRAWICON(COND, PRICE, TYPE)`: 當 COND 成立時，在 PRICE 位置繪製圖標。
- `STICKLINE(COND, PRICE1, PRICE2, WIDTH, EMPTY)`: 繪製柱狀線。
- `DRAWTEXT(COND, PRICE, TEXT)`: 在指定位置顯示文字。

## 4. 顏色函數
可以用在賦值語句末尾，如 `MA5: MA(C, 5), COLORRED;`。
- COLORRED, COLORGREEN, COLORBLUE, COLORYELLOW, COLORWHITE, COLORCYAN, COLORMAGENTA。

## 5. 限制與雷區 (Pitfalls)
- **不支援複雜迴圈**: 儘量使用向量化函數。
- **NOT 運算元歧義**: 在布林判斷中避免直接使用 `NOT COND`，某些編譯器會報錯。
    - ❌ `NOT ENTRY_SIGNAL`
    - ✅ `ENTRY_SIGNAL = 0` 或 `ENTRY_SIGNAL < 1`
- **狀態變數**: 不支援類似 Pine Script `var` 的狀態鎖定變數，需用 `BARSLAST` + `REF` 組合來回溯歷史狀態。
- **參數設定**: 建議在代碼中以註釋說明，提醒使用者在 UI 介面填入。