/**
 * Replay Engine for German30 Simulator
 * Handles progressive reveal of candles and session management
 */

class ReplayEngine {
    constructor() {
        this.currentSession = null;
        this.currentScenario = null;
        this.allCandles = {
            '4h': [],
            '1h': [],
            '3m': []
        };
        this.currentIndex = 0;
        this.isPlaying = false;
        this.speed = 1;
        this.intervalId = null;

        this.initializeControls();
    }

    initializeControls() {
        // Playlist generation
        document.getElementById('generatePlaylist')?.addEventListener('click', () => {
            this.generatePlaylist();
        });

        // Replay controls
        document.getElementById('playBtn')?.addEventListener('click', () => {
            this.play();
        });

        document.getElementById('pauseBtn')?.addEventListener('click', () => {
            this.pause();
        });

        document.getElementById('nextBtn')?.addEventListener('click', () => {
            this.nextCandle();
        });

        // Speed selector
        document.querySelectorAll('.speed-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.setSpeed(parseInt(e.target.dataset.speed));
                document.querySelectorAll('.speed-btn').forEach(b => b.classList.remove('active'));
                e.target.classList.add('active');
            });
        });
    }

    async generatePlaylist() {
        const startDate = document.getElementById('startDate').value;
        const endDate = document.getElementById('endDate').value;
        const timeWindow = document.getElementById('timeWindow').value;

        if (!startDate || !endDate) {
            showToast('Please select date range', 'error');
            return;
        }

        try {
            // Get available dates
            const response = await fetch(
                `${CONFIG.apiUrl}/available-dates?start_date=${startDate}&end_date=${endDate}&time_window=${timeWindow}`
            );

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to get available dates');
            }

            if (data.sessions.length === 0) {
                showToast('No valid trading dates found in range', 'warning');
                return;
            }

            // Create session
            const dates = data.sessions.map(s => s.date);
            const createResponse = await fetch(`${CONFIG.apiUrl}/session/start`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dates: dates,
                    time_window: timeWindow,
                })
            });

            const sessionData = await createResponse.json();

            if (!sessionData.success) {
                throw new Error(sessionData.error || 'Failed to create session');
            }

            this.currentSession = sessionData.session;
            this.displayPlaylist();
            this.loadCurrentScenario();

            showToast(`Session created with ${dates.length} dates`, 'success');

        } catch (error) {
            console.error('Error generating playlist:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    displayPlaylist() {
        if (!this.currentSession) {
            return;
        }

        const playlist = this.currentSession.playlist;
        const playlistEl = document.getElementById('playlist');
        const playlistCount = document.getElementById('playlistCount');

        playlistCount.textContent = playlist.length;

        playlistEl.innerHTML = playlist.map((date, index) => {
            const isActive = index === this.currentSession.current_date_index;
            const isCompleted = index < this.currentSession.current_date_index;

            return `
                <div class="playlist-item ${isActive ? 'active' : ''} ${isCompleted ? 'completed' : ''}"
                     data-index="${index}">
                    ${formatDate(date)}
                </div>
            `;
        }).join('');
    }

    async loadCurrentScenario() {
        if (!this.currentSession || !this.currentSession.current_date) {
            return;
        }

        const date = this.currentSession.current_date;
        const timeWindow = this.currentSession.time_window;

        this.currentScenario = { date, timeWindow };
        this.currentIndex = 0;

        // Update UI
        document.getElementById('currentScenario').textContent =
            `${formatDate(date)} • ${CONFIG.timeWindows[timeWindow].label}`;
        document.getElementById('sessionProgress').textContent =
            `${this.currentSession.current_date_index + 1}/${this.currentSession.playlist.length}`;

        // Load candles for all timeframes
        try {
            await this.loadCandles('4h');
            await this.loadCandles('1h');
            await this.loadCandles('3m');

            // Show first few candles
            this.revealInitialCandles();

            showToast('Scenario loaded', 'success');

        } catch (error) {
            console.error('Error loading scenario:', error);
            showToast(`Error loading data: ${error.message}`, 'error');
        }
    }

    async loadCandles(timeframe) {
        if (!this.currentScenario) {
            return;
        }

        const response = await fetch(
            `${CONFIG.apiUrl}/candles?` +
            `session_id=${this.currentSession.id}&` +
            `date=${this.currentScenario.date}&` +
            `time_window=${this.currentScenario.timeWindow}&` +
            `timeframe=${timeframe}`
        );

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || `Failed to load ${timeframe} candles`);
        }

        this.allCandles[timeframe] = data.candles;

        console.log(`Loaded ${data.candles.length} ${timeframe} candles`);
    }

    revealInitialCandles() {
        // Show all 4H and 1H candles (context)
        if (this.allCandles['4h'].length > 0) {
            chartManager.setData('4h', this.allCandles['4h']);
            chartManager.fitContent('4h');
            this.updateChartInfo('4h');
        }

        if (this.allCandles['1h'].length > 0) {
            chartManager.setData('1h', this.allCandles['1h']);
            chartManager.fitContent('1h');
            this.updateChartInfo('1h');
        }

        // Show first 3 candles of 3m (or all if less than 3)
        const numInitial = Math.min(3, this.allCandles['3m'].length);
        const initialCandles = this.allCandles['3m'].slice(0, numInitial);

        if (initialCandles.length > 0) {
            chartManager.setData('3m', initialCandles);
            this.currentIndex = initialCandles.length;
            this.updateCandleCounter();
            chartManager.fitContent('3m');
            this.updateChartInfo('3m');

            console.log(`Revealed ${numInitial} initial candles. Total available: ${this.allCandles['3m'].length}`);
        } else {
            showToast('No 3-minute candles available for this time window', 'warning');
        }
    }

    play() {
        if (this.isPlaying) {
            return;
        }

        if (!this.currentScenario) {
            showToast('No scenario loaded', 'warning');
            return;
        }

        if (this.currentIndex >= this.allCandles['3m'].length) {
            showToast('End of data', 'info');
            return;
        }

        this.isPlaying = true;
        document.getElementById('playBtn').disabled = true;
        document.getElementById('pauseBtn').disabled = false;

        const interval = 1000 / this.speed;
        this.intervalId = setInterval(() => {
            this.nextCandle();
        }, interval);
    }

    pause() {
        this.isPlaying = false;
        document.getElementById('playBtn').disabled = false;
        document.getElementById('pauseBtn').disabled = true;

        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    nextCandle() {
        if (!this.currentScenario || this.currentIndex >= this.allCandles['3m'].length) {
            this.pause();
            showToast('End of time window', 'info');
            return;
        }

        const candle = this.allCandles['3m'][this.currentIndex];
        chartManager.updateCandle('3m', candle);

        this.currentIndex++;
        this.updateCandleCounter();

        // Update chart info with latest candle
        if (this.currentIndex > 0) {
            const displayCandle = this.allCandles['3m'][this.currentIndex - 1];
            const infoEl = document.getElementById('chart3mInfo');
            if (infoEl && displayCandle) {
                const time = new Date(displayCandle.time * 1000);
                const timeStr = time.toLocaleTimeString('en-GB', {
                    hour: '2-digit',
                    minute: '2-digit',
                    timeZone: 'Europe/London'
                });
                infoEl.textContent = `${timeStr} | O:${displayCandle.open.toFixed(2)} H:${displayCandle.high.toFixed(2)} L:${displayCandle.low.toFixed(2)} C:${displayCandle.close.toFixed(2)}`;
            }
        }

        // Auto-fit
        chartManager.fitContent('3m');
    }

    setSpeed(speed) {
        this.speed = speed;

        if (this.isPlaying) {
            this.pause();
            this.play();
        }
    }

    updateCandleCounter() {
        document.getElementById('candleCount').textContent = this.currentIndex;
        document.getElementById('totalCandles').textContent = this.allCandles['3m'].length;
    }

    updateChartInfo(timeframe) {
        const candles = this.allCandles[timeframe];
        if (!candles || candles.length === 0) {
            return;
        }

        // Get last candle for display
        const lastCandle = candles[candles.length - 1];
        const infoEl = document.getElementById(`chart${timeframe}Info`);

        if (infoEl) {
            const time = new Date(lastCandle.time * 1000);
            const timeStr = time.toLocaleTimeString('en-GB', {
                hour: '2-digit',
                minute: '2-digit',
                timeZone: 'Europe/London'
            });
            const dateStr = time.toLocaleDateString('en-GB', { timeZone: 'Europe/London' });

            infoEl.textContent = `${dateStr} ${timeStr} | O:${lastCandle.open.toFixed(2)} H:${lastCandle.high.toFixed(2)} L:${lastCandle.low.toFixed(2)} C:${lastCandle.close.toFixed(2)}`;
        }
    }

    async nextScenario() {
        if (!this.currentSession) {
            return;
        }

        try {
            const response = await fetch(
                `${CONFIG.apiUrl}/session/${this.currentSession.id}/next`,
                { method: 'POST' }
            );

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Failed to advance session');
            }

            if (data.completed) {
                showToast('Session completed!', 'success');
                this.sessionCompleted();
                return;
            }

            this.currentSession = data.session;
            this.displayPlaylist();
            this.loadCurrentScenario();

        } catch (error) {
            console.error('Error advancing session:', error);
            showToast(`Error: ${error.message}`, 'error');
        }
    }

    sessionCompleted() {
        showToast('Congratulations! Session completed. Check your statistics.', 'success');
        // Could redirect to stats page or show summary modal
    }

    updateSessionStats() {
        if (!this.currentSession) {
            return;
        }

        document.getElementById('sessionTrades').textContent = this.currentSession.total_trades;
        document.getElementById('sessionWinRate').textContent =
            `${this.currentSession.win_rate.toFixed(1)}%`;

        const pnlEl = document.getElementById('sessionPnl');
        pnlEl.textContent = `${this.currentSession.total_pnl >= 0 ? '+' : ''}${this.currentSession.total_pnl.toFixed(2)} pts`;
        pnlEl.className = `font-mono ${this.currentSession.total_pnl >= 0 ? 'text-success' : 'text-danger'}`;
    }
}

// Global replay engine instance
let replayEngine;

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.getElementById('generatePlaylist')) {
            replayEngine = new ReplayEngine();
        }
    });
} else {
    if (document.getElementById('generatePlaylist')) {
        replayEngine = new ReplayEngine();
    }
}

// Helper function to load session
function loadSession(session) {
    if (replayEngine) {
        replayEngine.currentSession = session;
        replayEngine.displayPlaylist();
        replayEngine.loadCurrentScenario();
    }
}
