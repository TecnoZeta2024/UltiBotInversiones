import express, { Request, Response } from 'express';
import { logger } from '../utils/logger';

export const signalRoutes = express.Router();

/**
 * @route   GET api/v1/signals
 * @desc    Get all available trading signals
 * @access  Public
 */
signalRoutes.get('/', async (req: Request, res: Response) => {
  try {
    // Mock response for now
    const signals = [
      {
        id: '1',
        coinPair: 'BTC/USDT',
        signalType: 'BUY',
        confidence: 0.85,
        source: 'mock-mcp',
        timestamp: new Date().toISOString(),
        price: 32500.45,
        targetPrice: 33000.00,
        stopLoss: 32000.00,
      },
      {
        id: '2',
        coinPair: 'ETH/USDT',
        signalType: 'SELL',
        confidence: 0.78,
        source: 'mock-mcp',
        timestamp: new Date().toISOString(),
        price: 1820.75,
        targetPrice: 1750.00,
        stopLoss: 1850.00,
      }
    ];
    
    res.json({ success: true, data: signals });
  } catch (error: any) {
    logger.error('Error fetching signals:', error);
    res.status(500).json({ success: false, error: 'Server error', message: error.message });
  }
});

/**
 * @route   POST api/v1/signals/generate
 * @desc    Generate a new signal based on market conditions
 * @access  Protected (should have auth in production)
 */
signalRoutes.post('/generate', async (req: Request, res: Response) => {
  try {
    const { coinPair, timeframe } = req.body;
    
    if (!coinPair) {
      return res.status(400).json({ 
        success: false, 
        error: 'Bad request', 
        message: 'coinPair is required' 
      });
    }
    
    // Mock signal generation
    const signal = {
      id: Date.now().toString(),
      coinPair,
      signalType: Math.random() > 0.5 ? 'BUY' : 'SELL',
      confidence: Math.random() * 0.5 + 0.5, // Between 0.5 and 1.0
      source: 'signal-generator',
      timestamp: new Date().toISOString(),
      timeframe: timeframe || '1h',
      analysis: {
        rsi: Math.floor(Math.random() * 100),
        macd: Math.random() > 0.5,
        movingAverages: {
          ma50: Math.random() * 1000 + 30000,
          ma200: Math.random() * 1000 + 29500,
        },
      }
    };
    
    logger.info(`Generated signal for ${coinPair}: ${signal.signalType}`);
    res.json({ success: true, data: signal });
  } catch (error: any) {
    logger.error('Error generating signal:', error);
    res.status(500).json({ success: false, error: 'Server error', message: error.message });
  }
});
