/**
 * Lightweight Charts integration for German30 Simulator
 * Manages three synchronized charts: 4H, 1H, and 3M
 */

class ChartManager {
    constructor() {
        this.charts = {};
        this.candleSeries = {};
        this.volumeSeries = {};
        this.priceLines = {};

        this.chartOptions = {
            layout: {
                background: { color: '#1E222D' },
                textColor: '#D1D4DC',
            },
            grid: {
                vertLines: { color: '#2A2E39' },
                horzLines: { color: '#2A2E39' },
            },
            crosshair: {
                mode: LightweightCharts.CrosshairMode.Normal,
            },
            rightPriceScale: {
                borderColor: '#2A2E39',
            },
            timeScale: {
                borderColor: '#2A2E39',
                timeVisible: true,
                secondsVisible: false,
            },
        };

        this.initializeCharts();
        this.syncCrosshairs();
    }

    initializeCharts() {
        // 4H Chart
        this.createChart('4h', 'chart4h', 250);

        // 1H Chart
        this.createChart('1h', 'chart1h', 250);

        // 3M Chart
        this.createChart('3m', 'chart3m', 400);

        console.log('Charts initialized');
    }

    createChart(timeframe, containerId, height) {
        const container = document.getElementById(containerId);
        if (!container) {
            console.error(`Container ${containerId} not found`);
            return;
        }

        const chart = LightweightCharts.createChart(container, {
            ...this.chartOptions,
            width: container.clientWidth,
            height: height,
        });

        // Create candlestick series
        const candleSeries = chart.addCandlestickSeries({
            upColor: '#26A69A',
            downColor: '#EF5350',
            borderUpColor: '#26A69A',
            borderDownColor: '#EF5350',
            wickUpColor: '#26A69A',
            wickDownColor: '#EF5350',
        });

        // Create volume series
        const volumeSeries = chart.addHistogramSeries({
            color: '#26a69a',
            priceFormat: {
                type: 'volume',
            },
            priceScaleId: '',
            scaleMargins: {
                top: 0.85,
                bottom: 0,
            },
        });

        this.charts[timeframe] = chart;
        this.candleSeries[timeframe] = candleSeries;
        this.volumeSeries[timeframe] = volumeSeries;
        this.priceLines[timeframe] = {};

        // Handle resize
        window.addEventListener('resize', () => {
            chart.applyOptions({
                width: container.clientWidth,
            });
        });
    }

    syncCrosshairs() {
        const chartKeys = Object.keys(this.charts);

        chartKeys.forEach((key) => {
            this.charts[key].subscribeCrosshairMove((param) => {
                if (!param || !param.time) {
                    return;
                }

                // Sync other charts
                chartKeys.forEach((otherKey) => {
                    if (otherKey !== key) {
                        this.charts[otherKey].setCrosshairPosition(
                            param.point ? param.point.y : null,
                            param.time,
                            this.candleSeries[otherKey]
                        );
                    }
                });
            });
        });

        console.log('Crosshairs synchronized');
    }

    setData(timeframe, candles) {
        if (!this.candleSeries[timeframe]) {
            console.error(`No series for timeframe ${timeframe}`);
            return;
        }

        const candleData = candles.map(c => ({
            time: c.time,
            open: c.open,
            high: c.high,
            low: c.low,
            close: c.close,
        }));

        const volumeData = candles.map(c => ({
            time: c.time,
            value: c.volume,
            color: c.close >= c.open ? '#26a69a40' : '#ef535040',
        }));

        this.candleSeries[timeframe].setData(candleData);
        this.volumeSeries[timeframe].setData(volumeData);

        console.log(`Set ${candles.length} candles for ${timeframe}`);
    }

    updateCandle(timeframe, candle) {
        if (!this.candleSeries[timeframe]) {
            return;
        }

        const candleData = {
            time: candle.time,
            open: candle.open,
            high: candle.high,
            low: candle.low,
            close: candle.close,
        };

        const volumeData = {
            time: candle.time,
            value: candle.volume,
            color: candle.close >= candle.open ? '#26a69a40' : '#ef535040',
        };

        this.candleSeries[timeframe].update(candleData);
        this.volumeSeries[timeframe].update(volumeData);
    }

    addPriceLine(timeframe, price, options = {}) {
        if (!this.candleSeries[timeframe]) {
            return null;
        }

        const defaultOptions = {
            price: price,
            color: '#787B86',
            lineWidth: 1,
            lineStyle: LightweightCharts.LineStyle.Dashed,
            axisLabelVisible: true,
            title: '',
        };

        const priceLine = this.candleSeries[timeframe].createPriceLine({
            ...defaultOptions,
            ...options,
        });

        return priceLine;
    }

    addTradeLine(timeframe, type, price) {
        const lineId = `${type}_${Date.now()}`;

        let color, title;
        switch (type) {
            case 'entry':
                color = '#2962FF';
                title = 'Entry';
                break;
            case 'sl':
                color = '#EF5350';
                title = 'SL';
                break;
            case 'tp':
                color = '#26A69A';
                title = 'TP';
                break;
            default:
                color = '#787B86';
                title = '';
        }

        const priceLine = this.addPriceLine(timeframe, price, {
            color: color,
            title: title,
            lineWidth: 2,
        });

        if (priceLine) {
            this.priceLines[timeframe][lineId] = priceLine;
        }

        return lineId;
    }

    removePriceLine(timeframe, lineId) {
        if (this.priceLines[timeframe] && this.priceLines[timeframe][lineId]) {
            this.candleSeries[timeframe].removePriceLine(this.priceLines[timeframe][lineId]);
            delete this.priceLines[timeframe][lineId];
        }
    }

    clearPriceLines(timeframe) {
        if (!this.priceLines[timeframe]) {
            return;
        }

        Object.keys(this.priceLines[timeframe]).forEach(lineId => {
            this.removePriceLine(timeframe, lineId);
        });
    }

    fitContent(timeframe) {
        if (this.charts[timeframe]) {
            this.charts[timeframe].timeScale().fitContent();
        }
    }

    fitAllContent() {
        Object.keys(this.charts).forEach(tf => {
            this.fitContent(tf);
        });
    }

    clearChart(timeframe) {
        if (this.candleSeries[timeframe]) {
            this.candleSeries[timeframe].setData([]);
            this.volumeSeries[timeframe].setData([]);
            this.clearPriceLines(timeframe);
        }
    }

    clearAllCharts() {
        Object.keys(this.charts).forEach(tf => {
            this.clearChart(tf);
        });
    }

    getVisibleRange(timeframe) {
        if (!this.charts[timeframe]) {
            return null;
        }

        const timeScale = this.charts[timeframe].timeScale();
        return timeScale.getVisibleRange();
    }

    setVisibleRange(timeframe, from, to) {
        if (!this.charts[timeframe]) {
            return;
        }

        this.charts[timeframe].timeScale().setVisibleRange({
            from: from,
            to: to,
        });
    }
}

// Global chart manager instance
let chartManager;

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('chart4h')) {
            chartManager = new ChartManager();
        }
    });
} else {
    if (document.getElementById('chart4h')) {
        chartManager = new ChartManager();
    }
}
