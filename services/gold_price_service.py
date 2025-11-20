import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.config import settings
import logging

from app.config import settings

logger = logging.getLogger(__name__)

class GoldPriceService:
    def __init__(self):
        self.finnhub_api_key = settings.FINNHUB_API_KEY
        self.alpha_api_key = settings.ALPHA_VANTAGE_API_KEY
        
    def get_live_price(self) -> Optional[Dict[str, float]]:
        """Fetch live XAUUSD price from Finnhub"""
        try:
            url = f"https://finnhub.io/api/v1/quote?symbol=XAUUSD&token={self.finnhub_api_key}"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            return {
                "timestamp": datetime.fromtimestamp(data["t"]),
                "current": data["c"],
                "open": data["o"],
                "high": data["h"],
                "low": data["l"],
                "previous_close": data["pc"]
            }
        except Exception as e:
            logger.error(f"Error fetching live price: {e}")
            return None
    
    def get_historical_prices(self, start_date: datetime, 
                            end_date: datetime) -> List[Dict]:
        """Fetch historical XAUUSD prices"""
        try:
            # Using Alpha Vantage for historical data
            url = (f"https://www.alphavantage.co/query?function=FX_DAILY"
                   f"&from_symbol=XAU&to_symbol=USD&apikey={self.alpha_api_key}")
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if "Time Series FX (Daily)" not in data:
                logger.error("No historical data available")
                return []
            
            prices = []
            for date_str, price_data in data["Time Series FX (Daily)"].items():
                date = datetime.strptime(date_str, "%Y-%m-%d")
                if start_date <= date <= end_date:
                    prices.append({
                        "timestamp": date,
                        "open": float(price_data["1. open"]),
                        "high": float(price_data["2. high"]),
                        "low": float(price_data["3. low"]),
                        "close": float(price_data["4. close"])
                    })
            return sorted(prices, key=lambda x: x["timestamp"])
        except Exception as e:
            logger.error(f"Error fetching historical prices: {e}")
            return []