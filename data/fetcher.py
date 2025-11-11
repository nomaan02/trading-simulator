"""
Data fetcher module - handles data acquisition from yfinance
"""
import yfinance as yf
import pandas as pd
import pytz
from datetime import datetime, timedelta
from config import Config
from models import db
from models.candle import Candle


class DataFetcher:
    """Fetches and caches German30 historical data"""

    def __init__(self):
        self.symbol = Config.GERMAN30_SYMBOL
        self.data_timezone = pytz.timezone(Config.DATA_TIMEZONE)

    def fetch_german30_data(self, start_date, end_date, interval='1m'):
        """
        Fetch German30 data from yfinance

        Args:
            start_date: Start date (datetime or string)
            end_date: End date (datetime or string)
            interval: Data interval ('1m', '5m', '1h', etc.)

        Returns:
            pandas DataFrame with OHLCV data or None on error
        """
        try:
            print(f"Fetching {self.symbol} data from {start_date} to {end_date} ({interval})...")

            # Convert dates to string format if needed
            if isinstance(start_date, datetime):
                start_str = start_date.strftime('%Y-%m-%d')
            else:
                start_str = start_date

            if isinstance(end_date, datetime):
                end_str = end_date.strftime('%Y-%m-%d')
            else:
                end_str = end_date

            # Fetch data from yfinance
            ticker = yf.Ticker(self.symbol)
            df = ticker.history(
                start=start_str,
                end=end_str,
                interval=interval,
                auto_adjust=True,
                actions=False
            )

            if df.empty:
                print(f"No data returned for {start_str} to {end_str}")
                return None

            # Ensure timezone is UTC
            if df.index.tz is None:
                df.index = df.index.tz_localize('UTC')
            else:
                df.index = df.index.tz_convert('UTC')

            print(f"Successfully fetched {len(df)} candles")
            return df

        except Exception as e:
            print(f"Error fetching data: {e}")
            return None

    def resample_to_3min(self, df):
        """
        Resample 1-minute data to 3-minute candles

        Args:
            df: DataFrame with 1-minute OHLCV data

        Returns:
            DataFrame with 3-minute candles
        """
        if df is None or df.empty:
            return None

        try:
            # Resample to 3-minute intervals
            resampled = df.resample('3T').agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })

            # Drop rows with NaN (incomplete candles)
            resampled = resampled.dropna()

            print(f"Resampled to {len(resampled)} 3-minute candles")
            return resampled

        except Exception as e:
            print(f"Error resampling data: {e}")
            return None

    def resample_to_timeframe(self, df, timeframe):
        """
        Resample data to specified timeframe

        Args:
            df: DataFrame with OHLCV data
            timeframe: Target timeframe ('3m', '1h', '4h', '1d')

        Returns:
            DataFrame with resampled candles
        """
        if df is None or df.empty:
            return None

        # Map timeframe strings to pandas resample rules
        timeframe_map = {
            '1m': '1T',
            '3m': '3T',
            '5m': '5T',
            '15m': '15T',
            '1h': '1H',
            '4h': '4H',
            '1d': '1D'
        }

        resample_rule = timeframe_map.get(timeframe)
        if not resample_rule:
            print(f"Unknown timeframe: {timeframe}")
            return None

        try:
            resampled = df.resample(resample_rule).agg({
                'Open': 'first',
                'High': 'max',
                'Low': 'min',
                'Close': 'last',
                'Volume': 'sum'
            })

            resampled = resampled.dropna()
            return resampled

        except Exception as e:
            print(f"Error resampling to {timeframe}: {e}")
            return None

    def cache_data(self, df, timeframe):
        """
        Cache DataFrame to database

        Args:
            df: DataFrame with OHLCV data
            timeframe: Timeframe string

        Returns:
            Number of candles cached
        """
        if df is None or df.empty:
            return 0

        try:
            cached_count = 0
            candles_to_insert = []

            for timestamp, row in df.iterrows():
                # Check if candle already exists
                if not Candle.exists(timestamp.to_pydatetime(), timeframe):
                    candle = Candle.from_series(row, timeframe)
                    candles_to_insert.append(candle)

            # Bulk insert new candles
            if candles_to_insert:
                Candle.bulk_insert(candles_to_insert)
                cached_count = len(candles_to_insert)
                print(f"Cached {cached_count} new {timeframe} candles")

            return cached_count

        except Exception as e:
            print(f"Error caching data: {e}")
            return 0

    def get_cached_data(self, start_date, end_date, timeframe):
        """
        Retrieve cached data from database

        Args:
            start_date: Start datetime
            end_date: End datetime
            timeframe: Timeframe string

        Returns:
            pandas DataFrame with cached data or None
        """
        try:
            candles = Candle.get_range(start_date, end_date, timeframe)

            if not candles:
                return None

            # Convert to DataFrame
            data = {
                'Open': [c.open for c in candles],
                'High': [c.high for c in candles],
                'Low': [c.low for c in candles],
                'Close': [c.close for c in candles],
                'Volume': [c.volume for c in candles]
            }

            df = pd.DataFrame(data, index=[c.timestamp for c in candles])
            df.index = df.index.tz_localize('UTC') if df.index.tz is None else df.index

            print(f"Retrieved {len(df)} cached {timeframe} candles")
            return df

        except Exception as e:
            print(f"Error retrieving cached data: {e}")
            return None

    def fetch_and_cache(self, start_date, end_date, timeframe='3m', force_refresh=False):
        """
        Fetch data and cache it, or retrieve from cache

        Args:
            start_date: Start date
            end_date: End date
            timeframe: Target timeframe
            force_refresh: Force re-fetch even if cached

        Returns:
            pandas DataFrame with OHLCV data
        """
        # Convert string dates to datetime
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Make timezone-aware
        if start_date.tzinfo is None:
            start_date = pytz.UTC.localize(start_date)
        if end_date.tzinfo is None:
            end_date = pytz.UTC.localize(end_date)

        # Try to get cached data first
        if not force_refresh:
            cached_df = self.get_cached_data(start_date, end_date, timeframe)
            if cached_df is not None and not cached_df.empty:
                print(f"Using cached data for {timeframe}")
                return cached_df

        # Fetch fresh data
        print(f"Fetching fresh data for {timeframe}...")

        # Determine best interval based on date range
        # Yahoo Finance limitations:
        # - 1m data: last 7 days only
        # - 5m data: last 60 days
        # - 15m/30m/60m/90m: last 60 days
        # - 1h: last 730 days

        from datetime import timedelta
        days_ago = (datetime.now(pytz.UTC) - start_date).days

        # Choose appropriate base interval
        if days_ago <= 7:
            base_interval = '1m'
        elif days_ago <= 60:
            base_interval = '5m'
        else:
            # For older data, use hourly and downsample
            base_interval = '1h'

        print(f"Using {base_interval} interval (data from {days_ago} days ago)")

        # Fetch base data
        df_base = self.fetch_german30_data(start_date, end_date, interval=base_interval)

        if df_base is None or df_base.empty:
            print(f"Failed to fetch {base_interval} data")
            print(f"Yahoo Finance may not have data for {start_date.date()} to {end_date.date()}")
            print(f"Try using dates within the last 7 days for best results")
            return None

        # Cache base data
        self.cache_data(df_base, base_interval)

        # Resample to target timeframe if needed
        if timeframe == base_interval:
            return df_base

        # Special handling for 3m timeframe
        if timeframe == '3m' and base_interval == '5m':
            # Can't accurately downsample from 5m to 3m, use 5m as substitute
            print("Note: Using 5m data as substitute for 3m (historical data limitation)")
            self.cache_data(df_base, '3m')  # Cache as 3m for consistency
            return df_base

        # For other conversions, try resampling
        df_resampled = self.resample_to_timeframe(df_base, timeframe)
        if df_resampled is not None:
            self.cache_data(df_resampled, timeframe)
        return df_resampled

    def fetch_multiframe_data(self, start_date, end_date, timeframes=['4h', '1h', '3m']):
        """
        Fetch data for multiple timeframes

        Args:
            start_date: Start date
            end_date: End date
            timeframes: List of timeframe strings

        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        result = {}

        for tf in timeframes:
            df = self.fetch_and_cache(start_date, end_date, timeframe=tf)
            if df is not None:
                result[tf] = df

        return result


# Convenience function
def get_data_fetcher():
    """Get a DataFetcher instance"""
    return DataFetcher()
