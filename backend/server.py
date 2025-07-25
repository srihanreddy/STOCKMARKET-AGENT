from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from groq import Groq
import yfinance as yf
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.fundamentaldata import FundamentalData
from alpha_vantage.techindicators import TechIndicators
import asyncio
import json
import uuid
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import requests
from concurrent.futures import ThreadPoolExecutor
import aiofiles

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="AI Stock Market Agent", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize clients
mongo_client = AsyncIOMotorClient(os.getenv("MONGO_URL"))
db = mongo_client[os.getenv("DB_NAME")]
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "demo")

# Initialize Alpha Vantage
ts = TimeSeries(key=alpha_vantage_key, output_format='pandas')
fd = FundamentalData(key=alpha_vantage_key, output_format='pandas')
ti = TechIndicators(key=alpha_vantage_key, output_format='pandas')

# Thread pool for synchronous operations
executor = ThreadPoolExecutor(max_workers=4)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

# Pydantic models
class StockQuery(BaseModel):
    symbol: str
    query: str

class StockAnalysisRequest(BaseModel):
    symbol: str
    timeframe: str = "1y"

class AIAgentResponse(BaseModel):
    analysis: str
    recommendations: List[str]
    risk_level: str
    confidence_score: float
    technical_indicators: Dict

class MarketAlert(BaseModel):
    symbol: str
    alert_type: str
    message: str
    timestamp: datetime

# Advanced Technical Analysis Functions
async def get_stock_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    """Get comprehensive stock data from multiple sources"""
    try:
        # Primary source: yfinance
        stock = yf.Ticker(symbol)
        data = stock.history(period=period)
        
        if data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for symbol {symbol}")
        
        # Add additional technical indicators
        data['SMA_20'] = data['Close'].rolling(window=20).mean()
        data['SMA_50'] = data['Close'].rolling(window=50).mean()
        data['RSI'] = calculate_rsi(data['Close'])
        data['MACD'], data['MACD_Signal'] = calculate_macd(data['Close'])
        data['BB_Upper'], data['BB_Lower'] = calculate_bollinger_bands(data['Close'])
        
        return data
    except Exception as e:
        logger.error(f"Error getting stock data for {symbol}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving data: {str(e)}")

def calculate_rsi(prices: pd.Series, window: int = 14) -> pd.Series:
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """Calculate MACD"""
    ema_fast = prices.ewm(span=fast).mean()
    ema_slow = prices.ewm(span=slow).mean()
    macd = ema_fast - ema_slow
    macd_signal = macd.ewm(span=signal).mean()
    return macd, macd_signal

def calculate_bollinger_bands(prices: pd.Series, window: int = 20, num_std: int = 2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * num_std)
    lower_band = sma - (std * num_std)
    return upper_band, lower_band

async def get_stock_news(symbol: str) -> List[Dict]:
    """Get latest news for a stock"""
    try:
        stock = yf.Ticker(symbol)
        news = stock.news[:5]  # Get latest 5 news items
        return [{"title": item.get("title", ""), "summary": item.get("summary", ""), "link": item.get("link", "")} for item in news]
    except Exception as e:
        logger.error(f"Error getting news for {symbol}: {str(e)}")
        return []

async def analyze_with_groq(symbol: str, data: pd.DataFrame, news: List[Dict], query: str) -> AIAgentResponse:
    """Advanced AI analysis using Groq"""
    try:
        # Prepare comprehensive data for analysis
        latest_data = data.tail(1).iloc[0]
        recent_data = data.tail(20)
        
        # Technical indicators summary
        tech_indicators = {
            "current_price": float(latest_data['Close']),
            "sma_20": float(latest_data['SMA_20']) if not pd.isna(latest_data['SMA_20']) else None,
            "sma_50": float(latest_data['SMA_50']) if not pd.isna(latest_data['SMA_50']) else None,
            "rsi": float(latest_data['RSI']) if not pd.isna(latest_data['RSI']) else None,
            "macd": float(latest_data['MACD']) if not pd.isna(latest_data['MACD']) else None,
            "volume": int(latest_data['Volume']),
            "price_change_pct": float(((latest_data['Close'] - recent_data['Close'].iloc[0]) / recent_data['Close'].iloc[0]) * 100)
        }
        
        # Create news summary
        news_summary = "\n".join([f"- {item['title']}: {item['summary'][:100]}..." for item in news[:3]])
        
        # Advanced prompt for Groq
        sma_20_str = f"${tech_indicators['sma_20']:.2f}" if tech_indicators['sma_20'] else "N/A"
        sma_50_str = f"${tech_indicators['sma_50']:.2f}" if tech_indicators['sma_50'] else "N/A"
        rsi_str = f"{tech_indicators['rsi']:.2f}" if tech_indicators['rsi'] else "N/A"
        macd_str = f"{tech_indicators['macd']:.4f}" if tech_indicators['macd'] else "N/A"
        
        prompt = f"""
        You are an expert financial analyst and portfolio manager. Analyze the following stock data for {symbol} and provide comprehensive insights.

        CURRENT MARKET DATA:
        - Current Price: ${tech_indicators['current_price']:.2f}
        - 20-day SMA: {sma_20_str}
        - 50-day SMA: {sma_50_str}
        - RSI: {rsi_str}
        - MACD: {macd_str}
        - Volume: {tech_indicators['volume']:,}
        - Price Change (20 days): {tech_indicators['price_change_pct']:.2f}%

        RECENT NEWS:
        {news_summary}

        USER QUERY: {query}

        Please provide:
        1. Comprehensive technical analysis
        2. Fundamental outlook based on news
        3. Risk assessment (Low/Medium/High)
        4. Specific actionable recommendations
        5. Confidence score (0-100)
        6. Market timing considerations

        Format your response as a detailed analysis followed by clear recommendations.
        """
        
        # Generate analysis with Groq
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a world-class financial analyst with 20+ years of experience. Provide detailed, actionable investment advice based on technical and fundamental analysis."},
                {"role": "user", "content": prompt}
            ],
            model="llama3-70b-8192",
            temperature=0.3,
            max_tokens=2000
        )
        
        analysis_text = response.choices[0].message.content
        
        # Extract recommendations (simplified for demo)
        recommendations = []
        if tech_indicators['rsi'] and tech_indicators['rsi'] < 30:
            recommendations.append("Consider buying - RSI indicates oversold conditions")
        elif tech_indicators['rsi'] and tech_indicators['rsi'] > 70:
            recommendations.append("Consider selling - RSI indicates overbought conditions")
        
        if tech_indicators['sma_20'] and tech_indicators['sma_50'] and tech_indicators['sma_20'] > tech_indicators['sma_50']:
            recommendations.append("Bullish signal - 20-day SMA above 50-day SMA")
        
        # Determine risk level
        risk_level = "Medium"
        if tech_indicators['rsi']:
            if tech_indicators['rsi'] > 80 or tech_indicators['rsi'] < 20:
                risk_level = "High"
            elif 40 <= tech_indicators['rsi'] <= 60:
                risk_level = "Low"
        
        # Calculate confidence score
        confidence_score = 85.0  # Simplified calculation
        
        return AIAgentResponse(
            analysis=analysis_text,
            recommendations=recommendations,
            risk_level=risk_level,
            confidence_score=confidence_score,
            technical_indicators=tech_indicators
        )
        
    except Exception as e:
        logger.error(f"Error in Groq analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

# API Routes
@app.get("/")
async def root():
    return {"message": "AI Stock Market Agent API is running"}

@app.post("/api/analyze")
async def analyze_stock(request: StockAnalysisRequest):
    """Comprehensive stock analysis endpoint"""
    try:
        # Get stock data
        data = await get_stock_data(request.symbol, request.timeframe)
        
        # Get news
        news = await get_stock_news(request.symbol)
        
        # Analyze with AI
        analysis = await analyze_with_groq(
            request.symbol, 
            data, 
            news, 
            f"Provide comprehensive analysis for {request.symbol}"
        )
        
        # Store analysis in database
        analysis_doc = {
            "symbol": request.symbol,
            "timestamp": datetime.utcnow(),
            "analysis": analysis.dict(),
            "timeframe": request.timeframe
        }
        await db.stock_analyses.insert_one(analysis_doc)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in stock analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chat")
async def chat_with_agent(request: StockQuery):
    """Chat with AI agent about specific stock"""
    try:
        # Get stock data
        data = await get_stock_data(request.symbol)
        
        # Get news
        news = await get_stock_news(request.symbol)
        
        # Analyze with AI
        analysis = await analyze_with_groq(request.symbol, data, news, request.query)
        
        return analysis
        
    except Exception as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stock/{symbol}/data")
async def get_stock_chart_data(symbol: str, period: str = "1y"):
    """Get stock chart data"""
    try:
        data = await get_stock_data(symbol, period)
        
        # Convert to JSON-serializable format
        chart_data = []
        for index, row in data.iterrows():
            chart_data.append({
                "date": index.strftime("%Y-%m-%d"),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume']),
                "sma_20": float(row['SMA_20']) if not pd.isna(row['SMA_20']) else None,
                "sma_50": float(row['SMA_50']) if not pd.isna(row['SMA_50']) else None,
                "rsi": float(row['RSI']) if not pd.isna(row['RSI']) else None
            })
        
        return {"symbol": symbol, "data": chart_data}
        
    except Exception as e:
        logger.error(f"Error getting chart data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/market/trending")
async def get_trending_stocks():
    """Get trending stocks"""
    try:
        # Popular stocks for demo
        trending_symbols = ["AAPL", "GOOGL", "MSFT", "TSLA", "AMZN", "NVDA"]
        trending_data = []
        
        for symbol in trending_symbols:
            try:
                stock = yf.Ticker(symbol)
                info = stock.info
                hist = stock.history(period="1d")
                if not hist.empty:
                    latest = hist.iloc[-1]
                    trending_data.append({
                        "symbol": symbol,
                        "name": info.get("longName", symbol),
                        "price": float(latest['Close']),
                        "change": float(latest['Close'] - latest['Open']),
                        "change_percent": float(((latest['Close'] - latest['Open']) / latest['Open']) * 100)
                    })
            except Exception as e:
                logger.error(f"Error getting data for {symbol}: {str(e)}")
                continue
        
        return {"trending_stocks": trending_data}
        
    except Exception as e:
        logger.error(f"Error getting trending stocks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message["type"] == "stock_subscribe":
                # Send real-time stock updates
                symbol = message["symbol"]
                stock_data = await get_stock_data(symbol, "1d")
                latest = stock_data.tail(1).iloc[0]
                
                response = {
                    "type": "stock_update",
                    "symbol": symbol,
                    "price": float(latest['Close']),
                    "volume": int(latest['Volume']),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await manager.send_personal_message(json.dumps(response), websocket)
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)