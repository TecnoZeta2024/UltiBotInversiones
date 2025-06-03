import express, { Request, Response } from 'express';
import { logger } from '../utils/logger';

export const marketDataRoutes = express.Router();

/**
 * @route   GET api/v1/market-data/ticker/:symbol
 * @desc    Get ticker info for a specific trading pair
 * @access  Public
 */
marketDataRoutes.get('/ticker/:symbol', async (req: Request, res: Response) => {
  try {
    const { symbol } = req.params;
    const { exchange = 'binance' } = req.query;
    
    if (!symbol) {
      return res.status(400).json({
        success: false, 
        error: 'Bad request', 
        message: 'Symbol is required'
      });
    }
    
    // Mock ticker data
    const ticker = {
      symbol,
      exchange,
      last: Math.random() * 1000 + 30000, // Mock price value
      bid: Math.random() * 1000 + 29950,
      ask: Math.random() * 1000 + 30050,
      volume: Math.random() * 5000 + 10000,
      timestamp: Date.now(),
      change24h: (Math.random() * 10 - 5).toFixed(2), // -5% to +5%
      high24h: Math.random() * 1000 + 30500,
      low24h: Math.random() * 1000 + 29500,
    };
    
    logger.info(`Fetched ticker for ${symbol} on ${exchange}`);
    res.json({ success: true, data: ticker });
  } catch (error: any) {
    logger.error('Error fetching ticker:', error);
    res.status(500).json({ success: false, error: 'Server error', message: error.message });
  }
});

/**
 * @route   GET api/v1/market-data/orderbook/:symbol
 * @desc    Get orderbook for a specific trading pair
 * @access  Public
 */
marketDataRoutes.get('/orderbook/:symbol', async (req: Request, res: Response) => {
  try {
    const { symbol } = req.params;
    const { exchange = 'binance', limit = 10 } = req.query;
    
    if (!symbol) {
      return res.status(400).json({
        success: false, 
        error: 'Bad request', 
        message: 'Symbol is required'
      });
    }
    
    const limitNum = Math.min(Number(limit), 100); // Cap at 100 entries
    
    // Generate mock orderbook
    const basePrice = 30000 + Math.random() * 2000;
    
    // Generate asks (sell orders) above base price
    const asks = Array.from({ length: limitNum }, (_, i) => {
      const price = basePrice + (i + 1) * (Math.random() * 10 + 5);
      const amount = Math.random() * 2 + 0.1;
      return [price.toFixed(2), amount.toFixed(8)];
    });
    
    // Generate bids (buy orders) below base price
    const bids = Array.from({ length: limitNum }, (_, i) => {
      const price = basePrice - (i + 1) * (Math.random() * 10 + 5);
      const amount = Math.random() * 2 + 0.1;
      return [price.toFixed(2), amount.toFixed(8)];
    });
    
    const orderbook = {
      symbol,
      exchange,
      timestamp: Date.now(),
      bids,
      asks,
    };
    
    logger.info(`Fetched orderbook for ${symbol} on ${exchange}`);
    res.json({ success: true, data: orderbook });
  } catch (error: any) {
    logger.error('Error fetching orderbook:', error);
    res.status(500).json({ success: false, error: 'Server error', message: error.message });
  }
});
