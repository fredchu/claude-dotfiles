# 經典範例庫 (Futu Indicator Examples)

## 1. 雙均線交叉 (Golden Cross)
```pascal
{ 參數: N1: 5, N2: 20 }
MA5 := MA(CLOSE, N1);
MA20 := MA(CLOSE, N2);

{ 繪圖 }
MA5_LINE: MA5, COLORWHITE;
MA20_LINE: MA20, COLORYELLOW;

{ 信號: 當 MA5 向上突破 MA20 時在最低價位置畫一個圖標 }
DRAWICON(CROSS(MA5, MA20), LOW, 1);
```

## 2. 布林帶突破 (Bollinger Breakout)
```pascal
{ 參數: N: 20, P: 2 }
MID := MA(CLOSE, N);
UPPER := MID + P * STD(CLOSE, N);
LOWER := MID - P * STD(CLOSE, N);

{ 顯示三條線 }
MID_LINE: MID, COLORWHITE;
UPPER_LINE: UPPER, COLORRED;
LOWER_LINE: LOWER, COLORGREEN;

{ 信號: 收盤價站上上軌 }
DRAWICON(CROSS(CLOSE, UPPER), LOW, 1);
```

## 3. 進階邏輯：狀態機模擬 (State Machine Simulation)
模擬 TradingView `var` 變數鎖定狀態的行為（例如：假跌破後進入等待區）。

**核心技巧：**
1.  使用 `BARSLAST` 找出事件發生點。
2.  使用 `REF(..., BARSLAST(...))` 回溯鎖定數值。
3.  使用 `COUNT(...) = 1` 確保連續訊號只觸發一次。

```pascal
{ 假摔偵測 (簡化版) }
MA30 := MA(CLOSE, 30);
SETUP := CLOSE > MA30;
FAKE_DOWN := REF(SETUP, 1) AND LOW < MA30; { 昨天在均線上，今天跌破 }

{ 1. 狀態追蹤：找出最近一次假摔距離幾天 }
BARS_FAKE := BARSLAST(FAKE_DOWN);

{ 2. 數值鎖定：鎖定假摔當天的高點作為壓力 }
LOCKED_HIGH := REF(HIGH, BARS_FAKE);

{ 3. 進場條件：假摔發生後，收盤站回均線且突破鎖定高點 }
RAW_ENTRY := (BARS_FAKE >= 0) AND CLOSE > MA30 AND CLOSE > LOCKED_HIGH;

{ 4. 訊號過濾：確保同一波假摔只觸發一次 }
{ 計算從上次假摔以來，進場條件成立過幾次 }
ENTRY := RAW_ENTRY AND COUNT(RAW_ENTRY, BARS_FAKE + 1) = 1;

DRAWICON(ENTRY, LOW, 1);
```