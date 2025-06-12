import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from uuid import UUID

from shared.data_types import Trade, PerformanceMetrics
from ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from ultibot_backend.core.exceptions import UltiBotError, ReportError

logger = logging.getLogger(__name__)

class TradingReportService:
    """
    Servicio para generar informes y métricas de rendimiento de trading.
    """
    def __init__(self, persistence_service: SupabasePersistenceService):
        self.persistence_service = persistence_service

    async def get_closed_trades(
        self, 
        user_id: UUID, 
        mode: str = 'paper', 
        symbol: Optional[str] = None, 
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Trade]:
        """
        Obtiene una lista de trades cerrados con capacidad de filtrado.
        
        Args:
            user_id: ID del usuario
            mode: Modo de trading ('paper' o 'real')
            symbol: Filtrar por par de trading (opcional)
            start_date: Fecha de inicio para filtrar (opcional)
            end_date: Fecha de fin para filtrar (opcional)
            limit: Número máximo de trades a devolver
            offset: Número de trades a saltar (para paginación)
            
        Returns:
            Lista de objetos Trade cerrados que cumplen con los filtros
        """
        try:
            # Construir los filtros para la consulta
            filters = {
                "user_id": str(user_id),
                "mode": mode,
                "positionStatus": "closed"
            }
            
            # Añadir filtros opcionales si están presentes
            if symbol:
                filters["symbol"] = symbol
            
            # Las fechas se filtrarán directamente en la consulta SQL 
            # (ver persistence_service.get_closed_trades)
            
            # Realizar la consulta a la base de datos
            trade_records = await self.persistence_service.get_closed_trades(
                filters, start_date, end_date, limit, offset
            )
            
            # Convertir los registros a objetos Trade
            trades = [Trade(**record) for record in trade_records]
            
            logger.info(f"Obtenidos {len(trades)} trades cerrados para usuario {user_id} en modo {mode}")
            return trades
            
        except Exception as e:
            logger.error(f"Error al obtener trades cerrados para usuario {user_id}: {e}", exc_info=True)
            raise ReportError(f"Error al obtener historial de trades: {str(e)}")
    
    async def calculate_performance_metrics(
        self, 
        user_id: UUID, 
        mode: str = 'paper',
        symbol: Optional[str] = None,
        start_date: Optional[datetime] = None, 
        end_date: Optional[datetime] = None
    ) -> PerformanceMetrics:
        """
        Calcula métricas de rendimiento consolidadas para un conjunto de trades.
        
        Args:
            user_id: ID del usuario
            mode: Modo de trading ('paper' o 'real')
            symbol: Filtrar por par de trading (opcional)
            start_date: Fecha de inicio para filtrar (opcional)
            end_date: Fecha de fin para filtrar (opcional)
            
        Returns:
            Objeto PerformanceMetrics con las métricas calculadas
        """
        try:
            # Obtener todos los trades cerrados para los filtros (sin límite para cálculos precisos)
            trades = await self.get_closed_trades(
                user_id, mode, symbol, start_date, end_date, limit=1000, offset=0
            )
            
            # Si no hay trades, devolver métricas con valores por defecto
            if not trades:
                return PerformanceMetrics(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_pnl=0.0,
                    avg_pnl_per_trade=0.0,
                    best_trade_pnl=0.0,
                    worst_trade_pnl=0.0,
                    best_trade_symbol=None,
                    worst_trade_symbol=None,
                    period_start=start_date,
                    period_end=end_date,
                    total_volume_traded=0.0
                )
                
            # Calcular métricas
            total_trades = len(trades)
            winning_trades = sum(1 for trade in trades if trade.pnl_usd is not None and trade.pnl_usd > 0)
            losing_trades = sum(1 for trade in trades if trade.pnl_usd is not None and trade.pnl_usd < 0)
            
            # Win rate (excluye trades con PnL = 0)
            non_zero_trades = sum(1 for trade in trades if trade.pnl_usd is not None and trade.pnl_usd != 0)
            win_rate = (winning_trades / non_zero_trades) * 100 if non_zero_trades > 0 else 0.0
            
            # PnL total
            total_pnl = sum(trade.pnl_usd for trade in trades if trade.pnl_usd is not None)
            
            # PnL promedio por operación
            avg_pnl_per_trade = total_pnl / total_trades if total_trades > 0 else 0.0
            
            # Mejor y peor trade
            trades_with_pnl = [(trade.pnl_usd, trade.symbol) for trade in trades if trade.pnl_usd is not None]
            
            best_trade_pnl = 0.0
            worst_trade_pnl = 0.0
            best_trade_symbol = None
            worst_trade_symbol = None
            
            if trades_with_pnl:
                best_trade = max(trades_with_pnl, key=lambda x: x[0])
                worst_trade = min(trades_with_pnl, key=lambda x: x[0])
                
                best_trade_pnl = best_trade[0]
                worst_trade_pnl = worst_trade[0]
                best_trade_symbol = best_trade[1]
                worst_trade_symbol = worst_trade[1]
            
            # Calcular volumen total operado (suma de todas las operaciones)
            total_volume_traded = sum(
                trade.entryOrder.executedQuantity * trade.entryOrder.executedPrice 
                for trade in trades 
                if trade.entryOrder and trade.entryOrder.executedQuantity and trade.entryOrder.executedPrice
            )
            
            # Determinar fechas de inicio y fin del periodo si no se proporcionaron
            if not start_date and trades:
                start_date = min(trade.opened_at for trade in trades if trade.opened_at)
            if not end_date and trades:
                end_date = max(trade.closed_at for trade in trades if trade.closed_at)
            
            # Crear y devolver el objeto de métricas
            return PerformanceMetrics(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=losing_trades,
                win_rate=win_rate,
                total_pnl=total_pnl,
                avg_pnl_per_trade=avg_pnl_per_trade,
                best_trade_pnl=best_trade_pnl,
                worst_trade_pnl=worst_trade_pnl,
                best_trade_symbol=best_trade_symbol,
                worst_trade_symbol=worst_trade_symbol,
                period_start=start_date,
                period_end=end_date,
                total_volume_traded=total_volume_traded
            )
            
        except Exception as e:
            logger.error(f"Error al calcular métricas de rendimiento para usuario {user_id}: {e}", exc_info=True)
            raise ReportError(f"Error al calcular métricas de rendimiento: {str(e)}")
