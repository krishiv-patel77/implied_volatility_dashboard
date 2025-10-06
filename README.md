# Implied Volatility Dashboard

A **Tkinter-based GUI** application for visualizing and analyzing **implied volatility (IV)** dynamics for any given equity ticker using **real market data from Interactive Brokers (IB TWS API)**.

![App Screenshot](./app_screenshot.png)

---

## Overview

The **Implied Volatility Trading Dashboard** enables traders to analyze how implied volatility behaves across time and regimes, uncovering opportunities for **mean-reversion**, **momentum**, and **volatility-based trading strategies**.

By integrating real-time market data from **Interactive Brokers**, the dashboard allows users to visualize **historical IV**, **forward IV relationships**, and **regime-dependent patterns**, giving a quantitative foundation for strategic decision-making in options trading.

---

## What is Implied Volatility?

Within the **Black-Scholes Option Pricing Model**, the fair price of an option depends on five key inputs:

| Parameter          | Symbol | Description                                     |
| ------------------ | ------ | ----------------------------------------------- |
| Strike Price       | K      | Exercise price of the option                    |
| Spot Price         | S      | Current price of the underlying asset           |
| Time to Expiration | T      | Remaining time until option maturity (in years) |
| Volatility         | σ      | Annualized standard deviation of returns        |
| Risk-Free Rate     | r      | Interest rate of a risk-free investment         |

In practice, an option’s **market price** is known. All key inputs except volatility are also observable. Therefore, traders **invert the Black-Scholes equation** to solve for the unknown volatility — the **implied volatility (IV)**.

Implied Volatility represents the market’s **expectation of future volatility**. It encapsulates market sentiment, uncertainty, and anticipated magnitude of price movement — without directional bias.

For instance, if **NVDA** is approaching earnings, option premiums may rise as traders expect increased volatility. Solving for IV using these market prices reveals how much volatility the market is “pricing in” ahead of the event.

---

## Why Analyze Implied Volatility?

1. **Mean Reversion:**
   IV tends to revert to its long-term mean. Extreme IV levels often signal potential trading opportunities.

2. **Regime Dependence:**
   Volatility behaves differently across high and low IV regimes, requiring adaptive analysis.

3. **Predictive Insights:**
   Today’s IV levels contain valuable information about the market's expectations for future volatility and sentiment towards the underlying, especially fear and uncertainty. 

4. **Risk Management:**
   Understanding IV dynamics helps traders hedge vega exposure and optimize position sizing.

---

## Key Features

### 1. Direct IB API Integration

* Connects to the **Interactive Brokers TWS/Gateway API**.
* Retrieves **historical volatility** and **real-time implied volatility**.
* Uses TCP socket connection (`127.0.0.1`) with configurable port (`7497` paper / `7496` live).

### 2. Automated Historical Data Processing

* Fetches **daily implied volatility bars**.
* Automatically **annualizes volatility values** for consistency.
* Supports forward-looking IV computation and regime classification.

### 3. Mean-Reversion Signal Generator

* Generates **non-trading advisory insights** based on percentile thresholds:

  * IV > 80th percentile → *Volatility-selling conditions*
  * IV < 20th percentile → *Volatility-buying conditions*

---

## Core Analyses

### 1. Forward IV vs. Current IV (Unconditional Regression)

**Purpose:** Explore how current IV predicts future IV (30-day average).

**Method:**

* Compute a 30-day rolling mean of IV (`forward_30d_IV`).
* Shift the window backward by 30 days to align each day with its future average.
* Perform regression: *Forward IV vs Current IV*.

**Interpretation:**

| Observation | Meaning                                               |
| ----------- | ----------------------------------------------------- |
| Slope < 1   | Mean reversion — high IV today implies lower IV ahead |
| Slope = 1   | Neutral — IV remains constant                         |
| Slope > 1   | Momentum — IV tends to continue rising/falling        |
| R² value    | Indicates strength of predictive relationship         |

---

### 2. Vol Difference vs. Current IV (Regime Analysis)

**Purpose:** Examine regime-specific IV dynamics.

**Process:**

* Define regimes by the **intersection point** of the regression line and the y=x line from the previous analysis.
* Split data into **high-volatility** and **low-volatility** regimes based on this intersection x-value.
* Calculate **Vol Difference** = Forward IV − Current IV.

**Insights:**

| Regime                                 | Interpretation                                          |
| -------------------------------------- | ------------------------------------------------------- |
| High-Volatility (Right of x-intercept) | Negative slope → IV likely to decrease (mean reversion) |
| Low-Volatility (Left of x-intercept)   | Positive slope → IV likely to increase                  |
| y=0 Line                               | No change — Forward IV = Current IV                     |

> Note: The high-volatility (right of x-intercept) and low-volatility (left of x-intercept) are referring to the current IV values (x-values). If these x-values are to the right of the x-intercept, they represent higher current IV values and vice versa for the x-values to the left of the intercept. 

---

### 3. Implied Volatility Time Series

**Purpose:** Visualize long-term IV evolution with percentile bands (25th, 50th, 75th).

**Use Cases:**

* Identify volatility extremes.
* Track shifts between volatility regimes.
* See historical trends

---

## Practical Trading Applications

### 1. Option Selling Scenarios

* Time-series IV above 75th percentile
* High-vol regime shows strong negative slope (R² > 0.5)
* Current IV regime classified as *High IV*
  → *Potential setup for short vega positions.*

### 2. Option Buying Scenarios

* Time-series IV below 25th percentile
* Low-vol regime shows strong positive slope (R² > 0.5)
* Current IV Regime classified as *LOW IV*
  → *Potential setup for long vega positions.*

> ⚠️ These are analytical insights, **not trading recommendations**.

---

## Installation

### Prerequisites

```
Interactive Brokers TWS or Gateway Installed
Valid Paper or Live IB Account
```

### Dependencies

* `tkinter` — GUI framework
* `pandas`, `numpy`, `scipy` — data and math libraries
* `ibapi` — Interactive Brokers Python API

---

## IB TWS Configuration

1. Open **TWS/Gateway** → *File → Global Configuration → API → Settings*
2. Enable “ActiveX and Socket Clients”
3. Set Socket Port: `7497` (paper) or `7496` (live)
4. Add `127.0.0.1` to trusted IPs
5. Disable “Read-Only API”
6. Under *Volatility & Analytics*, ensure **Daily Volatility Units** are selected

---

## Usage

1. **Launch Application**

   ```bash
   # Requires uv package manager installed globally
   uv run main.py
   ```

2. **Connect to IB**

   * Host: `127.0.0.1`
   * Port: `7497` (paper)
   * Confirm green “Connected” status in GUI.

3. **Enter Ticker**

   * e.g. `AAPL`, `TSLA`, `NVDA`
   * Fetches IV data automatically.

4. **Analyze**

   * View regression plots, volatility regimes, and time-series IV.
   * Interpret slopes and percentiles for potential mean-reversion setups.

---

## References

* [Interactive Brokers API Documentation](https://interactivebrokers.github.io/tws-api/)

---

## Disclaimer

This application is for educational and analytical purposes only. Options trading involves substantial risk and may not be suitable for all investors. Theoretical models do not guarantee real-world performance. Always consult a qualified financial advisor before trading options. The author assumes no liability for any losses incurred.

---

**Built with:** Python, Tkinter, Interactive Brokers API
**Version:** 1.0.0
