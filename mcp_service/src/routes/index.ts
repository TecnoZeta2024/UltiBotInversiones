import { Express, Request, Response } from 'express';
import { signalRoutes } from './signal-routes';
import { marketDataRoutes } from './market-data-routes';
import { logger } from '../utils/logger';

/**
 * Setup all routes for the MCP server
 */
export function setupRoutes(app: Express): void {
  // API version prefix
  const apiPrefix = '/api/v1';
  
  // Basic info endpoint
  app.get('/', (req: Request, res: Response) => {
    res.json({
      name: 'UltiBot MCP Server',
      version: '1.0.0',
      description: 'Model Context Protocol server for UltiBotInversiones',
    });
  });

  // Mount specific route groups
  app.use(`${apiPrefix}/signals`, signalRoutes);
  app.use(`${apiPrefix}/market-data`, marketDataRoutes);

  // 404 handler
  app.use((req: Request, res: Response) => {
    logger.warn(`404 - Route not found: ${req.originalUrl}`);
    res.status(404).json({
      error: 'Not Found',
      message: `The requested resource could not be found: ${req.originalUrl}`,
    });
  });
}
