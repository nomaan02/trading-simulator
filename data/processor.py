"""
Data processor module - handles strategy-specific data filtering
"""
import pandas as pd
import pytz
from datetime import datetime, time, timedelta
from config import Config


class DataProcessor:
    """Processes and filters data according to trading strategy rules"""

    def __init__(self):
        self.valid_days = Config.VALID_DAYS
        self.time_windows = Config.TIME_WINDOWS
        self.bst_tz = pytz.timezone(Config.DISPLAY_TIMEZONE)
        self.utc_tz = pytz.timezone(Config.DATA_TIMEZONE)

    def filter_valid_trading_days(self, df):
        """
        Filter DataFrame to only include valid trading days

        Valid days: Monday, Thursday, Friday

        Args:
            df: DataFrame with datetime index

        Returns:
            Filtered DataFrame
        """
        if df is None or df.empty:
            return df

        # Get day names
        df_copy = df.copy()
        day_names = df_copy.index.day_name()

        # Filter to valid days
        mask = day_names.isin(self.valid_days)
        filtered = df_copy[mask]

        print(f"Filtered to valid trading days: {len(filtered)} candles from {len(df)} total")
        return filtered

    def convert_to_bst(self, dt):
        """Convert UTC datetime to BST"""
        if dt.tzinfo is None:
            dt = self.utc_tz.localize(dt)
        return dt.astimezone(self.bst_tz)

    def convert_to_utc(self, dt):
        """Convert BST datetime to UTC"""
        if dt.tzinfo is None:
            dt = self.bst_tz.localize(dt)
        return dt.astimezone(self.utc_tz)

    def filter_time_window(self, df, window_key):
        """
        Filter DataFrame to specific time window

        Args:
            df: DataFrame with datetime index (in UTC)
            window_key: Time window key ('morning_1', 'morning_2', etc.)

        Returns:
            Filtered DataFrame
        """
        if df is None or df.empty:
            return df

        if window_key not in self.time_windows:
            print(f"Invalid time window: {window_key}")
            return df

        window = self.time_windows[window_key]
        start_time = window['start']
        end_time = window['end']

        # Convert index to BST for filtering
        df_copy = df.copy()
        df_copy['bst_time'] = df_copy.index.map(lambda x: self.convert_to_bst(x).time())

        # Filter by time range
        mask = (df_copy['bst_time'] >= start_time) & (df_copy['bst_time'] <= end_time)
        filtered = df_copy[mask].drop(columns=['bst_time'])

        print(f"Filtered to {window['label']}: {len(filtered)} candles")
        return filtered

    def get_available_dates(self, start_date, end_date):
        """
        Get list of valid trading dates in range

        Args:
            start_date: Start date (datetime or string)
            end_date: End date (datetime or string)

        Returns:
            List of date objects (valid trading days only)
        """
        # Convert to datetime if string
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        elif isinstance(end_date, datetime):
            end_date = end_date.date()

        # Generate all dates in range
        dates = []
        current = start_date
        while current <= end_date:
            # Check if valid trading day
            day_name = current.strftime('%A')
            if day_name in self.valid_days:
                dates.append(current)

            current += timedelta(days=1)

        print(f"Found {len(dates)} valid trading dates between {start_date} and {end_date}")
        return dates

    def get_available_sessions(self, start_date, end_date, time_window):
        """
        Get list of available practice sessions (date + time window combinations)

        Args:
            start_date: Start date
            end_date: End date
            time_window: Time window key

        Returns:
            List of dictionaries with session info
        """
        valid_dates = self.get_available_dates(start_date, end_date)

        if time_window not in self.time_windows:
            print(f"Invalid time window: {time_window}")
            return []

        window_info = self.time_windows[time_window]

        sessions = []
        for date in valid_dates:
            sessions.append({
                'date': date.isoformat(),
                'date_formatted': date.strftime('%A, %B %d, %Y'),
                'time_window': time_window,
                'time_window_label': window_info['label'],
                'day_name': date.strftime('%A')
            })

        return sessions

    def prepare_replay_data(self, date, time_window, timeframes=['4h', '1h', '3m']):
        """
        Prepare multi-timeframe data for a specific date and time window

        Args:
            date: Date to prepare (datetime.date or string)
            time_window: Time window key
            timeframes: List of timeframes to prepare

        Returns:
            Dictionary with data for each timeframe
        """
        from data.fetcher import DataFetcher

        # Convert date if needed
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()

        # Calculate date range for context
        # For higher timeframes, we need data from before the specific date
        context_start = date - timedelta(days=10)  # Get 10 days of context
        context_end = date + timedelta(days=1)

        fetcher = DataFetcher()
        result = {}

        for tf in timeframes:
            # Fetch data for timeframe
            df = fetcher.fetch_and_cache(context_start, context_end, timeframe=tf)

            if df is not None and not df.empty:
                # For 3-minute data, filter to specific date and time window
                if tf == '3m':
                    # Filter to specific date
                    df_date = df[df.index.date == date]

                    # Filter to time window
                    df_filtered = self.filter_time_window(df_date, time_window)

                    result[tf] = df_filtered
                else:
                    # For higher timeframes (4h, 1h), include context up to the date
                    df_filtered = df[df.index.date <= date]
                    result[tf] = df_filtered

        return result

    def get_candles_for_date(self, date, time_window, timeframe='3m'):
        """
        Get candles for a specific date and time window

        Args:
            date: Date (datetime.date or string)
            time_window: Time window key
            timeframe: Timeframe string

        Returns:
            pandas DataFrame with filtered candles
        """
        data = self.prepare_replay_data(date, time_window, timeframes=[timeframe])
        return data.get(timeframe)

    def get_time_window_info(self, window_key):
        """Get time window configuration"""
        return self.time_windows.get(window_key)

    def is_valid_trading_day(self, date):
        """Check if a date is a valid trading day"""
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()
        elif isinstance(date, datetime):
            date = date.date()

        day_name = date.strftime('%A')
        return day_name in self.valid_days

    def get_scenario_metadata(self, date, time_window):
        """
        Get metadata for a scenario (date + time window)

        Args:
            date: Date (datetime.date or string)
            time_window: Time window key

        Returns:
            Dictionary with metadata
        """
        if isinstance(date, str):
            date = datetime.strptime(date, '%Y-%m-%d').date()

        if not self.is_valid_trading_day(date):
            return None

        window_info = self.time_windows.get(time_window)
        if not window_info:
            return None

        return {
            'date': date.isoformat(),
            'date_formatted': date.strftime('%A, %B %d, %Y'),
            'day_name': date.strftime('%A'),
            'time_window': time_window,
            'time_window_label': window_info['label'],
            'start_time': window_info['start'].strftime('%H:%M'),
            'end_time': window_info['end'].strftime('%H:%M')
        }


# Convenience function
def get_data_processor():
    """Get a DataProcessor instance"""
    return DataProcessor()
