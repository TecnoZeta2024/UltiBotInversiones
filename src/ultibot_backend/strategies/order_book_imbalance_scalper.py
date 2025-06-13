"""
Order Book Imbalance Scalper Strategy

Esta estrategia detecta grandes desbalances entre órdenes de compra/venta en el libro 
de órdenes para predecir movimientos a corto plazo. Utiliza microestructura de mercado
para identificar presión institucional y flujos de órdenes.

Author: UltiBotInversiones
Version: 1.0
"""

import logging
from decimal import Decimal
from typing import Optional, Dict, Any, List, Tuple
import statistics

from .base_strategy import BaseStrategy, AnalysisResult, TradingSignal, SignalStrength
from src.ultibot_backend.core.domain_models.market import MarketData, KlineData

logger = logging.getLogger(__name__)

class OrderBookParameters:
    """Parámetros configurables para Order Book Imbalance Scalper."""
    
    def __init__(
        self,
        imbalance_threshold: float = 0.6,  # 60% mínimo de imbalance
        min_order_size_filter: float = 10000,  # Filtrar órdenes pequeñas (USDT)
        depth_levels: int = 10,  # Niveles del order book a analizar
        volume_confirmation_multiplier: float = 2.0,
        price_impact_threshold: float = 0.001,  # 0.1% mínimo de impacto
        holding_period_seconds: int = 30,  # Máximo 30 segundos
        position_size_pct: float = 0.005,  # 0.5% posición muy pequeña para scalping
        spread_threshold_bps: float = 5.0,  # Máximo 5 bps de spread
        liquidity_threshold: float = 50000  # Mínima liquidez total en book
    ):
        self.imbalance_threshold = imbalance_threshold
        self.min_order_size_filter = min_order_size_filter
        self.depth_levels = depth_levels
        self.volume_confirmation_multiplier = volume_confirmation_multiplier
        self.price_impact_threshold = price_impact_threshold
        self.holding_period_seconds = holding_period_seconds
        self.position_size_pct = position_size_pct
        self.spread_threshold_bps = spread_threshold_bps
        self.liquidity_threshold = liquidity_threshold

class OrderBookImbalanceScalper(BaseStrategy):
    """
    Estrategia de scalping basada en desbalances del order book.
    
    Identifica momentos donde hay significativo desequilibrio entre bid/ask volume
    y opera en la dirección del imbalance esperando corrección inmediata.
    """
    
    def __init__(self, parameters: OrderBookParameters):
        super().__init__("Order_Book_Imbalance_Scalper", parameters)
        self.imbalance_threshold = parameters.imbalance_threshold
        self.min_order_size_filter = parameters.min_order_size_filter
        self.depth_levels = parameters.depth_levels
        self.volume_confirmation_multiplier = parameters.volume_confirmation_multiplier
        self.price_impact_threshold = parameters.price_impact_threshold
        self.holding_period_seconds = parameters.holding_period_seconds
        self.position_size_pct = parameters.position_size_pct
        self.spread_threshold_bps = parameters.spread_threshold_bps
        self.liquidity_threshold = parameters.liquidity_threshold
        
        self._order_book_history = []
        self._imbalance_history = []

    async def setup(self, market_data: Any) -> None:
        """Configuración inicial de la estrategia."""
        logger.info(f"Configurando {self.name} con imbalance threshold={self.imbalance_threshold}")

    async def analyze(self, market_snapshot: MarketData) -> AnalysisResult:
        """
        Analiza el order book para detectar imbalances significativos.
        
        Args:
            market_snapshot: Datos actuales del mercado
            
        Returns:
            AnalysisResult con análisis de order book y oportunidades de scalping
        """
        try:
            if len(market_snapshot.klines) < 5:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Datos insuficientes para análisis"}
                )

            # Simular order book (en implementación real vendría de WebSocket)
            order_book = self._simulate_order_book(market_snapshot.klines[-1])
            
            # Verificar calidad del mercado
            market_quality = self._assess_market_quality(order_book, market_snapshot.klines[-1])
            
            if not market_quality["tradeable"]:
                return AnalysisResult(
                    confidence=0.0,
                    indicators={},
                    metadata={"error": "Condiciones de mercado no aptas para scalping"}
                )

            # Calcular imbalance del order book
            imbalance_data = self._calculate_order_book_imbalance(order_book)
            
            # Detectar órdenes grandes (icebergs/institucionales)
            large_orders = self._detect_large_orders(order_book)
            
            # Analizar flujo de órdenes reciente
            order_flow = self._analyze_order_flow(market_snapshot.klines[-5:])
            
            # Calcular presión de precio esperada
            price_pressure = self._calculate_price_pressure(order_book, imbalance_data)
            
            # Verificar momentum de volumen instantáneo
            volume_momentum = self._analyze_instantaneous_volume(market_snapshot.klines[-3:])
            
            # Detectar patrones de microestructura
            microstructure_patterns = self._detect_microstructure_patterns(order_book, order_flow)
            
            # Evaluar oportunidad de scalping
            scalping_opportunity = self._evaluate_scalping_opportunity(
                imbalance_data, large_orders, price_pressure, market_quality
            )
            
            # Calcular confianza
            confidence = self._calculate_confidence(
                imbalance_data, market_quality, scalping_opportunity, 
                volume_momentum, microstructure_patterns
            )
            
            current_price = float(market_snapshot.klines[-1].close)
            
            return AnalysisResult(
                confidence=confidence,
                indicators={
                    "current_price": current_price,
                    "order_book_imbalance": imbalance_data,
                    "large_orders": large_orders,
                    "price_pressure": price_pressure,
                    "market_quality": market_quality,
                    "volume_momentum": volume_momentum,
                    "microstructure_patterns": microstructure_patterns,
                    "scalping_opportunity": scalping_opportunity
                },
                metadata={
                    "order_book": order_book,
                    "imbalance_threshold": self.imbalance_threshold,
                    "holding_period": self.holding_period_seconds
                }
            )
            
        except Exception as e:
            logger.error(f"Error en análisis Order Book Imbalance: {e}")
            return AnalysisResult(
                confidence=0.0,
                indicators={},
                metadata={"error": str(e)}
            )

    async def generate_signal(self, analysis: AnalysisResult) -> Optional[TradingSignal]:
        """
        Genera señal de scalping basada en el análisis de order book.
        
        Args:
            analysis: Resultado del análisis
            
        Returns:
            TradingSignal si se detecta imbalance significativo, None en caso contrario
        """
        try:
            if analysis.confidence < 0.8:  # Umbral muy alto para scalping
                return None
                
            indicators = analysis.indicators
            scalping_opportunity = indicators.get("scalping_opportunity", {})
            market_quality = indicators.get("market_quality", {})
            
            if not scalping_opportunity.get("valid_opportunity", False):
                return None
                
            if not market_quality.get("tradeable", False):
                return None
                
            imbalance_data = indicators.get("order_book_imbalance", {})
            price_pressure = indicators.get("price_pressure", {})
            current_price = indicators.get("current_price", 0)
            
            imbalance_ratio = imbalance_data.get("imbalance_ratio", 0)
            imbalance_direction = imbalance_data.get("direction")
            
            # Señal de compra (bid imbalance significativo)
            if (imbalance_direction == "bid_heavy" and 
                abs(imbalance_ratio) >= self.imbalance_threshold):
                
                signal_strength = self._get_signal_strength(analysis.confidence, abs(imbalance_ratio))
                position_size = self._calculate_position_size(signal_strength, market_quality)
                
                # Calcular targets muy ajustados para scalping
                entry_price = current_price
                stop_loss = self._calculate_scalping_stop_loss(current_price, price_pressure, "BUY")
                take_profit = self._calculate_scalping_take_profit(current_price, price_pressure, "BUY")
                
                return TradingSignal(
                    signal_type="BUY",
                    strength=signal_strength,
                    entry_price=Decimal(str(entry_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Order book bid imbalance scalping. Imbalance: {imbalance_ratio:.1%}, Price pressure: {price_pressure.get('expected_move', 0):.4f}, Liquidity: {market_quality.get('total_liquidity', 0):,.0f}",
                    metadata={
                        "strategy_type": "scalping",
                        "max_holding_seconds": self.holding_period_seconds,
                        "order_book_imbalance": imbalance_ratio
                    }
                )
                
            # Señal de venta (ask imbalance significativo)
            elif (imbalance_direction == "ask_heavy" and 
                  abs(imbalance_ratio) >= self.imbalance_threshold):
                
                signal_strength = self._get_signal_strength(analysis.confidence, abs(imbalance_ratio))
                position_size = self._calculate_position_size(signal_strength, market_quality)
                
                # Calcular targets muy ajustados para scalping
                entry_price = current_price
                stop_loss = self._calculate_scalping_stop_loss(current_price, price_pressure, "SELL")
                take_profit = self._calculate_scalping_take_profit(current_price, price_pressure, "SELL")
                
                return TradingSignal(
                    signal_type="SELL",
                    strength=signal_strength,
                    entry_price=Decimal(str(entry_price)),
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    position_size=position_size,
                    reasoning=f"Order book ask imbalance scalping. Imbalance: {imbalance_ratio:.1%}, Price pressure: {price_pressure.get('expected_move', 0):.4f}, Liquidity: {market_quality.get('total_liquidity', 0):,.0f}",
                    metadata={
                        "strategy_type": "scalping",
                        "max_holding_seconds": self.holding_period_seconds,
                        "order_book_imbalance": imbalance_ratio
                    }
                )
                
            return None
            
        except Exception as e:
            logger.error(f"Error generando señal Order Book Imbalance: {e}")
            return None

    def _simulate_order_book(self, current_kline: KlineData) -> Dict[str, Any]:
        """
        Simula un order book realista para testing.
        En implementación real, estos datos vendrían de WebSocket de Binance.
        """
        current_price = float(current_kline.close)
        spread_pct = 0.0002  # 0.02% spread típico
        
        # Simular bid/ask prices
        mid_price = current_price
        spread = mid_price * spread_pct
        best_bid = mid_price - spread / 2
        best_ask = mid_price + spread / 2
        
        # Simular levels del order book
        bids = []
        asks = []
        
        # Generar niveles con volumen decreciente
        for i in range(self.depth_levels):
            # Bids (órdenes de compra)
            bid_price = best_bid - (i * spread * 0.1)  # Precios decrecientes
            bid_volume = max(1000, 10000 * (1 - i * 0.1)) * (1 + (hash(str(i)) % 50) / 100)  # Volumen con algo de aleatoriedad
            bids.append({"price": bid_price, "volume": bid_volume})
            
            # Asks (órdenes de venta)
            ask_price = best_ask + (i * spread * 0.1)  # Precios crecientes
            ask_volume = max(1000, 10000 * (1 - i * 0.1)) * (1 + (hash(str(i+100)) % 50) / 100)
            asks.append({"price": ask_price, "volume": ask_volume})
        
        # Simular algún imbalance ocasional
        imbalance_factor = (hash(str(current_price)) % 200 - 100) / 100  # -1 a 1
        
        if imbalance_factor > 0.3:  # Favor a bids
            for bid in bids[:3]:
                bid["volume"] *= (1 + imbalance_factor)
        elif imbalance_factor < -0.3:  # Favor a asks
            for ask in asks[:3]:
                ask["volume"] *= (1 + abs(imbalance_factor))
        
        return {
            "bids": bids,
            "asks": asks,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "spread": spread,
            "mid_price": mid_price
        }

    def _assess_market_quality(self, order_book: Dict[str, Any], current_kline: KlineData) -> Dict[str, Any]:
        """Evalúa la calidad del mercado para scalping."""
        spread = order_book["spread"]
        mid_price = order_book["mid_price"]
        
        # Calcular spread en basis points
        spread_bps = (spread / mid_price) * 10000
        
        # Calcular liquidez total
        total_bid_volume = sum(bid["volume"] for bid in order_book["bids"][:5])  # Top 5 levels
        total_ask_volume = sum(ask["volume"] for ask in order_book["asks"][:5])
        total_liquidity = (total_bid_volume + total_ask_volume) / 2
        
        # Evaluar condiciones
        spread_ok = spread_bps <= self.spread_threshold_bps
        liquidity_ok = total_liquidity >= self.liquidity_threshold
        
        # Verificar volumen reciente
        current_volume = float(current_kline.volume)
        volume_ok = current_volume > 1000000  # Mínimo volumen para scalping
        
        tradeable = spread_ok and liquidity_ok and volume_ok
        
        return {
            "tradeable": tradeable,
            "spread_bps": spread_bps,
            "total_liquidity": total_liquidity,
            "current_volume": current_volume,
            "spread_ok": spread_ok,
            "liquidity_ok": liquidity_ok,
            "volume_ok": volume_ok
        }

    def _calculate_order_book_imbalance(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula el imbalance del order book."""
        # Sumar volumen de top N levels
        bid_volume = sum(bid["volume"] for bid in order_book["bids"][:self.depth_levels])
        ask_volume = sum(ask["volume"] for ask in order_book["asks"][:self.depth_levels])
        
        total_volume = bid_volume + ask_volume
        
        if total_volume == 0:
            return {"imbalance_ratio": 0, "direction": "neutral"}
        
        # Calcular ratio de imbalance
        imbalance_ratio = (bid_volume - ask_volume) / total_volume
        
        # Determinar dirección
        if imbalance_ratio > self.imbalance_threshold:
            direction = "bid_heavy"  # Más órdenes de compra
        elif imbalance_ratio < -self.imbalance_threshold:
            direction = "ask_heavy"  # Más órdenes de venta
        else:
            direction = "balanced"
        
        return {
            "imbalance_ratio": imbalance_ratio,
            "direction": direction,
            "bid_volume": bid_volume,
            "ask_volume": ask_volume,
            "total_volume": total_volume
        }

    def _detect_large_orders(self, order_book: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta órdenes grandes que pueden mover el mercado."""
        large_bids = []
        large_asks = []
        
        # Filtrar órdenes grandes
        for bid in order_book["bids"]:
            order_value = bid["price"] * bid["volume"]
            if order_value >= self.min_order_size_filter:
                large_bids.append(bid)
        
        for ask in order_book["asks"]:
            order_value = ask["price"] * ask["volume"]
            if order_value >= self.min_order_size_filter:
                large_asks.append(ask)
        
        # Calcular impacto potencial
        total_large_bid_volume = sum(bid["volume"] for bid in large_bids)
        total_large_ask_volume = sum(ask["volume"] for ask in large_asks)
        
        return {
            "large_bids": large_bids,
            "large_asks": large_asks,
            "large_bid_count": len(large_bids),
            "large_ask_count": len(large_asks),
            "total_large_bid_volume": total_large_bid_volume,
            "total_large_ask_volume": total_large_ask_volume
        }

    def _analyze_order_flow(self, recent_klines: List[KlineData]) -> Dict[str, Any]:
        """Analiza el flujo de órdenes reciente."""
        if len(recent_klines) < 3:
            return {"flow_direction": "neutral"}
        
        # Usar precio y volumen para inferir flujo
        price_changes = []
        volume_changes = []
        
        for i in range(1, len(recent_klines)):
            price_change = float(recent_klines[i].close) - float(recent_klines[i-1].close)
            volume_change = (float(recent_klines[i].volume) - float(recent_klines[i-1].volume)) / float(recent_klines[i-1].volume)
            
            price_changes.append(price_change)
            volume_changes.append(volume_change)
        
        # Determinar flujo predominante
        positive_flows = sum(1 for p, v in zip(price_changes, volume_changes) if p > 0 and v > 0)
        negative_flows = sum(1 for p, v in zip(price_changes, volume_changes) if p < 0 and v > 0)
        
        if positive_flows > negative_flows:
            flow_direction = "buying_pressure"
        elif negative_flows > positive_flows:
            flow_direction = "selling_pressure"
        else:
            flow_direction = "neutral"
        
        return {
            "flow_direction": flow_direction,
            "positive_flows": positive_flows,
            "negative_flows": negative_flows,
            "price_changes": price_changes,
            "volume_changes": volume_changes
        }

    def _calculate_price_pressure(self, order_book: Dict[str, Any], imbalance_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calcula la presión de precio esperada."""
        imbalance_ratio = imbalance_data.get("imbalance_ratio", 0)
        mid_price = order_book["mid_price"]
        
        # Estimar movimiento de precio basado en imbalance
        # Imbalance fuerte puede mover el precio hasta el siguiente nivel significativo
        expected_move_pct = abs(imbalance_ratio) * 0.001  # Máximo 0.1% por imbalance completo
        
        if imbalance_ratio > 0:  # Bid heavy
            expected_direction = "up"
            expected_price = mid_price * (1 + expected_move_pct)
        else:  # Ask heavy
            expected_direction = "down"
            expected_price = mid_price * (1 - expected_move_pct)
        
        # Calcular resistencia/soporte en book
        resistance_level = self._find_resistance_level(order_book)
        support_level = self._find_support_level(order_book)
        
        return {
            "expected_direction": expected_direction,
            "expected_move": expected_price - mid_price,
            "expected_move_pct": expected_move_pct,
            "resistance_level": resistance_level,
            "support_level": support_level
        }

    def _find_resistance_level(self, order_book: Dict[str, Any]) -> float:
        """Encuentra el nivel de resistencia más cercano en el order book."""
        # Buscar nivel con volumen significativo en asks
        max_volume = 0
        resistance_price = order_book["best_ask"]
        
        for ask in order_book["asks"]:
            if ask["volume"] > max_volume:
                max_volume = ask["volume"]
                resistance_price = ask["price"]
        
        return resistance_price

    def _find_support_level(self, order_book: Dict[str, Any]) -> float:
        """Encuentra el nivel de soporte más cercano en el order book."""
        # Buscar nivel con volumen significativo en bids
        max_volume = 0
        support_price = order_book["best_bid"]
        
        for bid in order_book["bids"]:
            if bid["volume"] > max_volume:
                max_volume = bid["volume"]
                support_price = bid["price"]
        
        return support_price

    def _analyze_instantaneous_volume(self, recent_klines: List[KlineData]) -> Dict[str, Any]:
        """Analiza momentum de volumen instantáneo."""
        if len(recent_klines) < 2:
            return {"momentum": "neutral"}
        
        current_volume = float(recent_klines[-1].volume)
        prev_volume = float(recent_klines[-2].volume)
        
        volume_change = (current_volume - prev_volume) / prev_volume if prev_volume > 0 else 0
        
        if volume_change >= 0.5:  # 50% aumento
            momentum = "strong_increase"
        elif volume_change >= 0.2:  # 20% aumento
            momentum = "increase"
        elif volume_change <= -0.3:  # 30% disminución
            momentum = "decrease"
        else:
            momentum = "neutral"
        
        return {
            "momentum": momentum,
            "volume_change_pct": volume_change,
            "current_volume": current_volume,
            "previous_volume": prev_volume
        }

    def _detect_microstructure_patterns(self, order_book: Dict[str, Any], order_flow: Dict[str, Any]) -> Dict[str, Any]:
        """Detecta patrones de microestructura del mercado."""
        patterns = []
        
        # Patrón: Spread muy estrecho + volumen alto
        spread_bps = (order_book["spread"] / order_book["mid_price"]) * 10000
        if spread_bps < 2.0:  # Spread muy estrecho
            patterns.append("tight_spread")
        
        # Patrón: Concentración de liquidez
        top3_bid_volume = sum(bid["volume"] for bid in order_book["bids"][:3])
        total_bid_volume = sum(bid["volume"] for bid in order_book["bids"])
        bid_concentration = top3_bid_volume / total_bid_volume if total_bid_volume > 0 else 0
        
        if bid_concentration > 0.7:  # 70% en top 3 levels
            patterns.append("liquidity_concentration")
        
        # Patrón: Flujo direccional consistente
        flow_direction = order_flow.get("flow_direction", "neutral")
        if flow_direction in ["buying_pressure", "selling_pressure"]:
            patterns.append("directional_flow")
        
        return {
            "patterns": patterns,
            "spread_bps": spread_bps,
            "liquidity_concentration": bid_concentration,
            "flow_direction": flow_direction
        }

    def _evaluate_scalping_opportunity(
        self,
        imbalance_data: Dict[str, Any],
        large_orders: Dict[str, Any],
        price_pressure: Dict[str, Any],
        market_quality: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evalúa si existe una oportunidad válida de scalping."""
        opportunity = {
            "valid_opportunity": False,
            "reasons": []
        }
        
        # Verificar imbalance significativo
        imbalance_ratio = abs(imbalance_data.get("imbalance_ratio", 0))
        if imbalance_ratio >= self.imbalance_threshold:
            opportunity["reasons"].append("significant_imbalance")
        else:
            return opportunity
        
        # Verificar calidad del mercado
        if market_quality.get("tradeable", False):
            opportunity["reasons"].append("good_market_quality")
        else:
            return opportunity
        
        # Verificar presión de precio suficiente
        expected_move_pct = abs(price_pressure.get("expected_move_pct", 0))
        if expected_move_pct >= self.price_impact_threshold:
            opportunity["reasons"].append("sufficient_price_impact")
        
        # Verificar órdenes grandes
        if large_orders.get("large_bid_count", 0) > 0 or large_orders.get("large_ask_count", 0) > 0:
            opportunity["reasons"].append("large_orders_present")
        
        # Si llegamos aquí con razones suficientes, es válido
        if len(opportunity["reasons"]) >= 2:
            opportunity["valid_opportunity"] = True
        
        return opportunity

    def _calculate_confidence(
        self,
        imbalance_data: Dict[str, Any],
        market_quality: Dict[str, Any],
        scalping_opportunity: Dict[str, Any],
        volume_momentum: Dict[str, Any],
        microstructure_patterns: Dict[str, Any]
    ) -> float:
        """Calcula el nivel de confianza de la estrategia."""
        confidence = 0.0
        
        # Base: imbalance fuerte
        imbalance_ratio = abs(imbalance_data.get("imbalance_ratio", 0))
        if imbalance_ratio >= 0.8:
            confidence += 0.4
        elif imbalance_ratio >= self.imbalance_threshold:
            confidence += 0.3
        
        # Calidad del mercado
        if market_quality.get("tradeable", False):
            confidence += 0.25
        
        # Oportunidad válida
        if scalping_opportunity.get("valid_opportunity", False):
            confidence += 0.15
        
        # Momentum de volumen
        momentum = volume_momentum.get("momentum", "neutral")
        if momentum in ["strong_increase", "increase"]:
            confidence += 0.1
        
        # Patrones de microestructura
        patterns = microstructure_patterns.get("patterns", [])
        if "tight_spread" in patterns:
            confidence += 0.05
        if "directional_flow" in patterns:
            confidence += 0.05
        
        return min(1.0, confidence)

    def _get_signal_strength(self, confidence: float, imbalance_ratio: float) -> SignalStrength:
        """Convierte confianza e imbalance a fuerza de señal."""
        combined_score = confidence + (min(imbalance_ratio, 1.0) * 0.2)
        
        if combined_score >= 0.9:
            return SignalStrength.STRONG
        elif combined_score >= 0.8:
            return SignalStrength.MEDIUM
        else:
            return SignalStrength.WEAK

    def _calculate_position_size(self, signal_strength: SignalStrength, market_quality: Dict[str, Any]) -> Decimal:
        """Calcula tamaño de posición muy conservador para scalping."""
        base_size = self.position_size_pct
        
        # Scalping requiere posiciones pequeñas
        if signal_strength == SignalStrength.STRONG:
            multiplier = 1.2
        elif signal_strength == SignalStrength.MEDIUM:
            multiplier = 1.0
        else:
            multiplier = 0.8
        
        # Ajuste por liquidez
        liquidity = market_quality.get("total_liquidity", 0)
        if liquidity >= self.liquidity_threshold * 2:
            liquidity_multiplier = 1.1
        else:
            liquidity_multiplier = 1.0
        
        final_size = base_size * multiplier * liquidity_multiplier
        return Decimal(str(final_size))

    def _calculate_scalping_stop_loss(self, entry_price: float, price_pressure: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula stop loss muy ajustado para scalping."""
        # Stop loss muy cerca, típicamente 2-3 ticks
        stop_distance_pct = 0.0005  # 0.05% máximo
        
        if position_type == "BUY":
            stop_price = entry_price * (1 - stop_distance_pct)
        else:  # SELL
            stop_price = entry_price * (1 + stop_distance_pct)
        
        return Decimal(str(stop_price))

    def _calculate_scalping_take_profit(self, entry_price: float, price_pressure: Dict[str, Any], position_type: str) -> Decimal:
        """Calcula take profit ajustado para scalping."""
        # Take profit basado en movimiento esperado pero limitado
        expected_move_pct = abs(price_pressure.get("expected_move_pct", 0.0005))
        tp_distance_pct = min(expected_move_pct, 0.002)  # Máximo 0.2%
        
        if position_type == "BUY":
            tp_price = entry_price * (1 + tp_distance_pct)
        else:  # SELL
            tp_price = entry_price * (1 - tp_distance_pct)
        
        return Decimal(str(tp_price))
