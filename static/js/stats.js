/**
 * Statistics Display for German30 Simulator
 * Handles data visualization and analysis
 */

class StatsManager {
    constructor() {
        this.initializeControls();
        this.loadStats();
    }

    initializeControls() {
        // Add any interactive controls here
        // e.g., date filters, export buttons
    }

    async loadStats() {
        // Could fetch additional computed stats from API
        // For now, stats are rendered server-side
        console.log('Stats page loaded');
    }

    exportToCSV() {
        // Export trade journal to CSV
        const table = document.querySelector('.table');
        if (!table) {
            return;
        }

        let csv = [];
        const rows = table.querySelectorAll('tr');

        rows.forEach(row => {
            const cols = row.querySelectorAll('td, th');
            const csvRow = [];

            cols.forEach(col => {
                csvRow.push(col.textContent.trim());
            });

            csv.push(csvRow.join(','));
        });

        const csvContent = csv.join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `german30-trades-${new Date().toISOString().split('T')[0]}.csv`;
        a.click();

        URL.revokeObjectURL(url);
        showToast('Exported to CSV', 'success');
    }

    calculateStreaks(trades) {
        let currentStreak = 0;
        let longestWinStreak = 0;
        let longestLossStreak = 0;
        let lastOutcome = null;

        trades.forEach(trade => {
            if (trade.outcome === 'win') {
                if (lastOutcome === 'win') {
                    currentStreak++;
                } else {
                    currentStreak = 1;
                }
                longestWinStreak = Math.max(longestWinStreak, currentStreak);
            } else if (trade.outcome === 'loss') {
                if (lastOutcome === 'loss') {
                    currentStreak++;
                } else {
                    currentStreak = 1;
                }
                longestLossStreak = Math.max(longestLossStreak, currentStreak);
            }
            lastOutcome = trade.outcome;
        });

        return {
            longestWinStreak,
            longestLossStreak
        };
    }

    generatePnLCurve(trades) {
        // Generate cumulative P&L data for charting
        let cumulative = 0;
        const data = [];

        trades.forEach(trade => {
            cumulative += trade.pnl_points;
            data.push({
                date: trade.entry_timestamp,
                pnl: cumulative
            });
        });

        return data;
    }
}

// Global stats manager instance
let statsManager;

// Initialize on DOM load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        if (document.querySelector('.stats-container')) {
            statsManager = new StatsManager();
        }
    });
} else {
    if (document.querySelector('.stats-container')) {
        statsManager = new StatsManager();
    }
}
