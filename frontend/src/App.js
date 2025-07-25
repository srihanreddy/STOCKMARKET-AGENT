import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';
import { TrendingUp, TrendingDown, Brain, Search, BarChart3, AlertCircle, DollarSign, Activity, Zap } from 'lucide-react';
import toast, { Toaster } from 'react-hot-toast';
import './App.css';

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [selectedStock, setSelectedStock] = useState('RELIANCE.NS');
  const [customStock, setCustomStock] = useState('');
  const [stockData, setStockData] = useState([]);
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [chatQuery, setChatQuery] = useState('');
  const [chatResponse, setChatResponse] = useState(null);
  const [trendingStocks, setTrendingStocks] = useState([]);
  const [activeTab, setActiveTab] = useState('analysis');
  const [stockError, setStockError] = useState('');
  const [isCustomStock, setIsCustomStock] = useState(false);

  useEffect(() => {
    fetchTrendingStocks();
    fetchStockData();
  }, []);

  useEffect(() => {
    if (selectedStock) {
      fetchStockData();
    }
  }, [selectedStock]);

  const fetchTrendingStocks = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/market/trending`);
      setTrendingStocks(response.data.trending_stocks);
    } catch (error) {
      console.error('Error fetching trending stocks:', error);
      toast.error('Failed to fetch trending stocks');
    }
  };

  const fetchStockData = async (symbol = null) => {
    const stockSymbol = symbol || selectedStock;
    setLoading(true);
    setStockError('');
    try {
      const response = await axios.get(`${API_BASE_URL}/api/stock/${stockSymbol}/data`);
      setStockData(response.data.data);
    } catch (error) {
      console.error('Error fetching stock data:', error);
      setStockError(`Failed to fetch data for ${stockSymbol}. Please check if the symbol is valid.`);
      toast.error(`Failed to fetch stock data for ${stockSymbol}`);
    } finally {
      setLoading(false);
    }
  };

  const handleStockChange = (symbol) => {
    setSelectedStock(symbol);
    setIsCustomStock(false);
    setAnalysis(null);
    setChatResponse(null);
    setStockError('');
  };

  const handleCustomStockSubmit = () => {
    if (!customStock.trim()) {
      toast.error('Please enter a stock symbol');
      return;
    }
    
    let stockSymbol = customStock.trim().toUpperCase();
    
    // Add .NS suffix if not already present for NSE stocks
    if (!stockSymbol.includes('.NS') && !stockSymbol.includes('.')) {
      stockSymbol = `${stockSymbol}.NS`;
    }
    
    setSelectedStock(stockSymbol);
    setIsCustomStock(true);
    setAnalysis(null);
    setChatResponse(null);
    setStockError('');
    fetchStockData(stockSymbol);
  };

  const analyzeStock = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/analyze`, {
        symbol: selectedStock,
        timeframe: '1y'
      });
      setAnalysis(response.data);
      toast.success('Analysis complete!');
    } catch (error) {
      console.error('Error analyzing stock:', error);
      toast.error('Failed to analyze stock');
    } finally {
      setLoading(false);
    }
  };

  const handleChatQuery = async () => {
    if (!chatQuery.trim()) return;
    
    setLoading(true);
    try {
      const response = await axios.post(`${API_BASE_URL}/api/chat`, {
        symbol: selectedStock,
        query: chatQuery
      });
      setChatResponse(response.data);
      toast.success('AI response generated!');
    } catch (error) {
      console.error('Error in chat:', error);
      toast.error('Failed to get AI response');
    } finally {
      setLoading(false);
    }
  };

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2
    }).format(price);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  const getRiskColor = (risk) => {
    switch (risk?.toLowerCase()) {
      case 'low': return 'text-green-600 bg-green-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'high': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const currentPrice = stockData.length > 0 ? stockData[stockData.length - 1]?.close : 0;
  const priceChange = stockData.length > 1 ? currentPrice - stockData[stockData.length - 2]?.close : 0;
  const priceChangePercent = stockData.length > 1 ? (priceChange / stockData[stockData.length - 2]?.close) * 100 : 0;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <Toaster position="top-right" />
      
      {/* Header */}
      <header className="bg-black/20 backdrop-blur-sm border-b border-purple-500/20">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <Brain className="h-8 w-8 text-purple-400" />
                <Zap className="h-6 w-6 text-yellow-400" />
              </div>
              <h1 className="text-2xl font-bold text-white">
                AI Stock Market Agent
              </h1>
              <span className="text-sm text-purple-300 bg-purple-900/50 px-3 py-1 rounded-full">
                Powered by Groq
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <select
                  value={isCustomStock ? 'custom' : selectedStock}
                  onChange={(e) => {
                    if (e.target.value === 'custom') {
                      setIsCustomStock(true);
                    } else {
                      handleStockChange(e.target.value);
                    }
                  }}
                  className="bg-slate-800 text-white px-4 py-2 rounded-lg border border-purple-500/50 focus:border-purple-400 focus:outline-none"
                >
                  <option value="RELIANCE.NS">Reliance Industries</option>
                  <option value="TCS.NS">Tata Consultancy Services</option>
                  <option value="HDFCBANK.NS">HDFC Bank</option>
                  <option value="INFY.NS">Infosys</option>
                  <option value="ICICIBANK.NS">ICICI Bank</option>
                  <option value="HINDUNILVR.NS">Hindustan Unilever</option>
                  <option value="ITC.NS">ITC Limited</option>
                  <option value="SBIN.NS">State Bank of India</option>
                  <option value="BHARTIARTL.NS">Bharti Airtel</option>
                  <option value="KOTAKBANK.NS">Kotak Mahindra Bank</option>
                  <option value="custom">Enter Custom Symbol</option>
                </select>
                
                {isCustomStock && (
                  <div className="flex items-center space-x-2">
                    <input
                      type="text"
                      value={customStock}
                      onChange={(e) => setCustomStock(e.target.value)}
                      placeholder="Enter NSE symbol (e.g., WIPRO)"
                      className="bg-slate-800 text-white px-4 py-2 rounded-lg border border-purple-500/50 focus:border-purple-400 focus:outline-none w-48"
                      onKeyPress={(e) => e.key === 'Enter' && handleCustomStockSubmit()}
                    />
                    <button
                      onClick={handleCustomStockSubmit}
                      className="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                    >
                      <Search className="h-4 w-4" />
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* Stock Overview */}
        <div className="mb-8">
          <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-3xl font-bold text-white">{selectedStock}</h2>
                <p className="text-purple-300 text-sm mt-1">NSE: National Stock Exchange of India</p>
              </div>
              <div className="flex items-center space-x-4">
                <div className="text-right">
                  <div className="text-3xl font-bold text-white">
                    ₹{currentPrice.toFixed(2)}
                  </div>
                  <div className={`flex items-center space-x-1 ${priceChange >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                    {priceChange >= 0 ? <TrendingUp className="h-4 w-4" /> : <TrendingDown className="h-4 w-4" />}
                    <span>{priceChange >= 0 ? '+' : ''}₹{priceChange.toFixed(2)}</span>
                    <span>({priceChangePercent.toFixed(2)}%)</span>
                  </div>
                </div>
              </div>
            </div>
            
            {stockError && (
              <div className="mb-4 p-3 bg-red-900/30 border border-red-500/50 rounded-lg">
                <div className="flex items-center space-x-2">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <span className="text-red-300">{stockError}</span>
                </div>
              </div>
            )}
            
            {/* Chart */}
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={stockData}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.8}/>
                      <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0.1}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                  <XAxis 
                    dataKey="date" 
                    stroke="#9ca3af"
                    tickFormatter={formatDate}
                  />
                  <YAxis 
                    stroke="#9ca3af"
                    tickFormatter={(value) => `₹${value}`}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: 'rgba(0, 0, 0, 0.8)',
                      border: '1px solid #8b5cf6',
                      borderRadius: '8px',
                      color: 'white'
                    }}
                    formatter={(value) => [`₹${value.toFixed(2)}`, 'Price']}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="close" 
                    stroke="#8b5cf6" 
                    fillOpacity={1} 
                    fill="url(#colorPrice)"
                    strokeWidth={2}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma_20" 
                    stroke="#fbbf24" 
                    strokeWidth={1}
                    dot={false}
                  />
                  <Line 
                    type="monotone" 
                    dataKey="sma_50" 
                    stroke="#10b981" 
                    strokeWidth={1}
                    dot={false}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-6">
          <div className="flex space-x-1 bg-black/40 backdrop-blur-sm rounded-lg p-1">
            <button
              onClick={() => setActiveTab('analysis')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'analysis'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <BarChart3 className="h-4 w-4" />
              <span>AI Analysis</span>
            </button>
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'chat'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <Brain className="h-4 w-4" />
              <span>AI Chat</span>
            </button>
            <button
              onClick={() => setActiveTab('trending')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-colors ${
                activeTab === 'trending'
                  ? 'bg-purple-600 text-white'
                  : 'text-gray-300 hover:text-white'
              }`}
            >
              <TrendingUp className="h-4 w-4" />
              <span>Trending</span>
            </button>
          </div>
        </div>

        {/* Tab Content */}
        {activeTab === 'analysis' && (
          <div className="space-y-6">
            {/* Analysis Controls */}
            <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-white">AI-Powered Analysis</h3>
                <button
                  onClick={analyzeStock}
                  disabled={loading}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-6 py-2 rounded-lg font-medium flex items-center space-x-2 transition-colors"
                >
                  {loading ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <Brain className="h-4 w-4" />
                      <span>Analyze with AI</span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Analysis Results */}
            {analysis && (
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* Technical Indicators */}
                <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                  <h4 className="text-lg font-bold text-white mb-4 flex items-center">
                    <Activity className="h-5 w-5 mr-2 text-purple-400" />
                    Technical Indicators
                  </h4>
                  <div className="space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">Current Price</span>
                      <span className="text-white font-semibold">
                        ₹{analysis.technical_indicators.current_price.toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">RSI</span>
                      <span className="text-white font-semibold">
                        {analysis.technical_indicators.rsi?.toFixed(2) || 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">20-day SMA</span>
                      <span className="text-white font-semibold">
                        {analysis.technical_indicators.sma_20 ? `₹${analysis.technical_indicators.sma_20.toFixed(2)}` : 'N/A'}
                      </span>
                    </div>
                    <div className="flex justify-between items-center">
                      <span className="text-gray-300">Volume</span>
                      <span className="text-white font-semibold">
                        {analysis.technical_indicators.volume?.toLocaleString() || 'N/A'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Risk Assessment */}
                <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                  <h4 className="text-lg font-bold text-white mb-4 flex items-center">
                    <AlertCircle className="h-5 w-5 mr-2 text-yellow-400" />
                    Risk Assessment
                  </h4>
                  <div className="space-y-4">
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300">Risk Level</span>
                        <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(analysis.risk_level)}`}>
                          {analysis.risk_level}
                        </span>
                      </div>
                    </div>
                    <div>
                      <div className="flex justify-between items-center mb-2">
                        <span className="text-gray-300">Confidence Score</span>
                        <span className="text-white font-semibold">
                          {analysis.confidence_score.toFixed(1)}%
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-purple-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${analysis.confidence_score}%` }}
                        ></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Recommendations */}
                <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                  <h4 className="text-lg font-bold text-white mb-4 flex items-center">
                    <DollarSign className="h-5 w-5 mr-2 text-green-400" />
                    Recommendations
                  </h4>
                  <div className="space-y-2">
                    {analysis.recommendations.map((rec, index) => (
                      <div key={index} className="flex items-start space-x-2">
                        <div className="w-2 h-2 bg-purple-400 rounded-full mt-2 flex-shrink-0"></div>
                        <span className="text-gray-300 text-sm">{rec}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Detailed Analysis */}
            {analysis && (
              <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                <h4 className="text-lg font-bold text-white mb-4">Detailed Analysis</h4>
                <div className="prose prose-invert max-w-none">
                  <div className="text-gray-300 whitespace-pre-wrap">
                    {analysis.analysis}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <div className="space-y-6">
            {/* Chat Interface */}
            <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
              <h3 className="text-xl font-bold text-white mb-4">Chat with AI Agent</h3>
              <div className="flex space-x-4">
                <input
                  type="text"
                  value={chatQuery}
                  onChange={(e) => setChatQuery(e.target.value)}
                  placeholder={`Ask anything about ${selectedStock.replace('.NS', '')}...`}
                  className="flex-1 bg-slate-800 text-white px-4 py-2 rounded-lg border border-purple-500/50 focus:border-purple-400 focus:outline-none"
                  onKeyPress={(e) => e.key === 'Enter' && handleChatQuery()}
                />
                <button
                  onClick={handleChatQuery}
                  disabled={loading || !chatQuery.trim()}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-6 py-2 rounded-lg font-medium flex items-center space-x-2 transition-colors"
                >
                  <Search className="h-4 w-4" />
                  <span>Ask AI</span>
                </button>
              </div>
            </div>

            {/* Chat Response */}
            {chatResponse && (
              <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
                <h4 className="text-lg font-bold text-white mb-4">AI Response</h4>
                <div className="prose prose-invert max-w-none">
                  <div className="text-gray-300 whitespace-pre-wrap mb-4">
                    {chatResponse.analysis}
                  </div>
                  {chatResponse.recommendations.length > 0 && (
                    <div>
                      <h5 className="text-white font-semibold mb-2">Recommendations:</h5>
                      <ul className="space-y-1">
                        {chatResponse.recommendations.map((rec, index) => (
                          <li key={index} className="text-gray-300">• {rec}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'trending' && (
          <div className="bg-black/40 backdrop-blur-sm rounded-2xl p-6 border border-purple-500/20">
            <h3 className="text-xl font-bold text-white mb-6">Trending Stocks</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {trendingStocks.map((stock, index) => (
                <div
                  key={index}
                  className="bg-slate-800/50 rounded-lg p-4 border border-purple-500/30 hover:border-purple-400 transition-colors cursor-pointer"
                  onClick={() => handleStockChange(stock.symbol)}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div>
                      <div className="font-bold text-white">{stock.symbol}</div>
                      <div className="text-sm text-gray-400 truncate">{stock.name}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-semibold text-white">₹{stock.price.toFixed(2)}</div>
                      <div className={`text-sm flex items-center ${stock.change >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                        {stock.change >= 0 ? <TrendingUp className="h-3 w-3 mr-1" /> : <TrendingDown className="h-3 w-3 mr-1" />}
                        {stock.change_percent.toFixed(2)}%
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;