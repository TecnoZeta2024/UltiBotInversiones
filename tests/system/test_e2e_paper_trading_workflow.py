# tests/system/test_e2e_paper_trading_workflow.py

import pytest
import asyncio
from uuid import UUID

from ultibot_ui.services.api_client import UltiBotAPIClient

@pytest.mark.asyncio
async def test_e2e_paper_trading_workflow():
    """
    Test E2E para el flujo de paper trading.
    """
    api_client = UltiBotAPIClient(base_url="http://localhost:8000")
    await api_client.initialize_client()

    for i in range(5):
        print(f"Iteración {i+1}/5")

        # 1. Obtener oportunidades de IA
        opportunities = await api_client.get_ai_opportunities()
        assert isinstance(opportunities, list)

        # 2. Filtrar oportunidades con confianza > 0.5
        valid_opportunities = [opp for opp in opportunities if opp.get("ai_confidence", 0) > 0.5]
        assert len(valid_opportunities) > 0, "No se encontraron oportunidades válidas"

        # 3. Tomar la primera oportunidad válida
        opportunity = valid_opportunities[0]
        symbol = opportunity.get("symbol")
        side = opportunity.get("side")
        amount = 0.001 # Cantidad de prueba

        # 4. Ejecutar una orden de mercado
        order_data = {
            "symbol": symbol,
            "type": "market",
            "side": side,
            "amount": amount,
            "trading_mode": "paper",
        }
        order_result = await api_client.execute_market_order(order_data)

        # 5. Verificar que la respuesta de la orden es exitosa
        assert isinstance(order_result, dict)
        assert "id" in order_result

    await api_client.close()
