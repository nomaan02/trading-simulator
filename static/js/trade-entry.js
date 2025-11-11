/**
 * Trade Entry Management for German30 Simulator
 * Handles trade creation and outcome determination
 */

class TradeManager {
    constructor() {
        this.currentTrade = null;
        this.initializeControls();
    }

    initializeControls() {
        document.getElementById('enterLong')?.addEventListener('click', () => {
            this.enterTrade('long');
        });

        document.getElementById('enterShort')?.addEventListener('click', () => {
            this.enterTrade('short');
        });
    }

    async enterTrade(direction) {
        if (!replayEngine || !replayEngine.currentSession) {
            showToast('No active session', 'error');
            return;
        }

        if (!replayEngine.currentScenario) {
            showToast('No scenario loaded', 'error');
            return;
        }

        // Pause replay
        if (replayEngine.isPlaying) {
            replayEngine.pause();
        }

        // Get current price (last candle close)
        const candles3m = replayEngine.allCandles['3m'];
        if (replayEngine.currentIndex === 0 || replayEngine.currentIndex > candles3m.length) {
            showToast('Invalid entry point', 'error');
            return;
        }

        const lastCandle = candles3m[replayEngine.currentIndex - 1];
        const entryPrice = lastCandle.close;

        // Get timestamp
        const timestamp = new Date(lastCandle.time * 1000).toISOString();

        // Calculate SL and TP
        let sl, tp;
        if (direction === 'long') {
            sl = entryPrice - CONFIG.stopLossPoints;
            tp = entryPrice + CONFIG.takeProfitPoints;
        } else {
            sl = entryPrice + CONFIG.stopLossPoints;
            tp = entryPrice - CONFIG.takeProfitPoints;
        }

        // Update UI
        document.getElementById('entryPrice').textContent = entryPrice.toFixed(2);
        document.getElementById('slPrice').textContent = sl.toFixed(2);
        document.getElementById('tpPrice').textContent = tp.toFixed(2);

        // Get notes and A-grade status
        const notes = document.getElementById('tradeNotes')?.value || '';
        const isAGrade = this.checkAGrade();

        // Create trade
        try {
            const response = await fetch(`${CONFIG.apiUrl}/trade/enter`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: replayEngine.currentSession.id,
                    timestamp: timestamp,
                    direction: direction,
                    entry_price: entryPrice,
                    notes: notes,
                    is_a_grade: isAGrade
                })
            });

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to create trade');
            }

            this.currentTrade = data.trade;

            // Draw entry, SL, TP lines on chart
            chartManager.addTradeLine('3m', 'entry', entryPrice);
            chartManager.addTradeLine('3m', 'sl', this.currentTrade.stop_loss);
            chartManager.addTradeLine('3m', 'tp', this.currentTrade.take_profit);

            showToast(`${direction.toUpperCase()} trade entered at ${entryPrice.toFixed(2)}`, 'success');

            // Auto-determine outcome
            setTimeout(() => {
                this.determineOutcome();
            }, 1000);

        } catch (error) {
            console.error('Error entering trade:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    async determineOutcome() {
        if (!this.currentTrade) {
            return;
        }

        try {
            const response = await fetch(
                `${CONFIG.apiUrl}/trade/${this.currentTrade.id}/outcome?` +
                `date=${replayEngine.currentScenario.date}&` +
                `time_window=${replayEngine.currentScenario.timeWindow}`
            );

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to determine outcome');
            }

            this.currentTrade = data.trade;

            // Show outcome
            this.showOutcomeModal();

            // Update session stats
            await this.refreshSessionStats();

        } catch (error) {
            console.error('Error determining outcome:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    showOutcomeModal() {
        if (!this.currentTrade || !this.currentTrade.outcome) {
            return;
        }

        const outcome = this.currentTrade.outcome.toUpperCase();
        const pnl = this.currentTrade.pnl_points.toFixed(2);
        const isWin = this.currentTrade.outcome === 'win';

        const message = `
            <div style="text-align: center; padding: 20px;">
                <h2 style="margin-bottom: 16px; color: ${isWin ? 'var(--bullish-green)' : 'var(--bearish-red)'}">
                    ${isWin ? '✅' : '❌'} ${outcome}
                </h2>
                <p style="font-size: 24px; font-family: var(--font-mono); margin-bottom: 16px;">
                    ${isWin ? '+' : ''}${pnl} pts
                </p>
                <p style="color: var(--text-secondary);">
                    Exit: ${this.currentTrade.exit_price.toFixed(2)}
                </p>
            </div>
        `;

        showToast(message, isWin ? 'success' : 'error');

        // Clear form
        this.resetTradeForm();

        // Offer to move to next scenario
        setTimeout(() => {
            if (confirm('Move to next scenario?')) {
                replayEngine.nextScenario();
            }
        }, 2000);
    }

    async refreshSessionStats() {
        if (!replayEngine || !replayEngine.currentSession) {
            return;
        }

        try {
            const response = await fetch(
                `${CONFIG.apiUrl}/session/${replayEngine.currentSession.id}`
            );

            const data = await response.json();

            if (data.success) {
                replayEngine.currentSession = data.session;
                replayEngine.updateSessionStats();
            }

        } catch (error) {
            console.error('Error refreshing stats:', error);
        }
    }

    checkAGrade() {
        const check4h = document.getElementById('check4h')?.checked || false;
        const check1h = document.getElementById('check1h')?.checked || false;
        const check3m = document.getElementById('check3m')?.checked || false;
        const checkWindow = document.getElementById('checkWindow')?.checked || false;

        return check4h && check1h && check3m && checkWindow;
    }

    resetTradeForm() {
        document.getElementById('tradeNotes').value = '';
        document.getElementById('check4h').checked = false;
        document.getElementById('check1h').checked = false;
        document.getElementById('check3m').checked = false;
        document.getElementById('checkWindow').checked = false;

        document.getElementById('entryPrice').textContent = '-';
        document.getElementById('slPrice').textContent = '-18 pts';
        document.getElementById('tpPrice').textContent = '+54 pts';

        this.currentTrade = null;
    }
}

// Global trade manager instance
let tradeManager;

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('enterLong')) {
            tradeManager = new TradeManager();
        }
    });
} else {
    if (document.getElementById('enterLong')) {
        tradeManager = new TradeManager();
    }
}
