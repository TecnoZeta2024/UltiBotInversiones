from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, Optional, Literal
from uuid import UUID

from src.shared.data_types import PortfolioSnapshot, PortfolioSummary
from src.ultibot_backend.services.portfolio_service import PortfolioService
from src.ultibot_backend.security import core as security_core # Importar security_core
from src.ultibot_backend.security import schemas as security_schemas # Importar security_schemas
# MarketDataService y SupabasePersistenceService no se usan directamente aquí como Depends,
# pero son dependencias de PortfolioService, que se resolverá a través de deps.
# from src.ultibot_backend.services.market_data_service import MarketDataService
# from src.ultibot_backend.adapters.persistence_service import SupabasePersistenceService
from src.ultibot_backend import dependencies as deps

router = APIRouter()

# Trading mode type alias for consistent validation
TradingMode = Literal["paper", "real", "both"]

@router.get("/snapshot", response_model=PortfolioSnapshot, status_code=status.HTTP_200_OK)
async def get_portfolio_snapshot(
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both"
):
    """
    Get portfolio snapshot for the authenticated user and trading mode.
    
    Args:
        current_user: Authenticated user object
        trading_mode: Filter by trading mode ('paper', 'real', 'both')
        
    Returns:
        PortfolioSnapshot with data filtered by trading mode
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

        if trading_mode == "both":
            # Return full snapshot as before
            snapshot = await portfolio_service.get_portfolio_snapshot(current_user.id)
            return snapshot
        elif trading_mode == "paper":
            # Return snapshot with only paper trading data
            # _get_paper_trading_summary might need user_id if it becomes user-specific
            # For now, assuming it's global or uses a fixed/default user for paper.
            # If PortfolioService's paper_trading_balance is user-specific, initialize_portfolio might be needed.
            await portfolio_service.initialize_portfolio(current_user.id) # Ensure context for paper if needed
            paper_summary = await portfolio_service._get_paper_trading_summary()
            # Create empty real trading summary
            empty_real = PortfolioSummary(
                available_balance_usdt=0.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=0.0,
                assets=[],
                error_message="Real trading data not requested"
            )
            return PortfolioSnapshot(
                paper_trading=paper_summary,
                real_trading=empty_real
            )
        elif trading_mode == "real":
            # Return snapshot with only real trading data
            real_summary = await portfolio_service._get_real_trading_summary(current_user.id)
            # Create empty paper trading summary
            empty_paper = PortfolioSummary(
                available_balance_usdt=0.0,
                total_assets_value_usd=0.0,
                total_portfolio_value_usd=0.0,
                assets=[],
                error_message="Paper trading data not requested"
            )
            return PortfolioSnapshot(
                paper_trading=empty_paper,
                real_trading=real_summary
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading_mode: {trading_mode}. Must be 'paper', 'real', or 'both'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio snapshot: {str(e)}"
        )

@router.get("/summary", response_model=PortfolioSummary, status_code=status.HTTP_200_OK)
async def get_portfolio_summary(
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    trading_mode: Annotated[TradingMode, Query(description="Trading mode: 'paper' or 'real'")] = "paper"
):
    """
    Get portfolio summary for a specific trading mode for the authenticated user.
    
    Args:
        current_user: Authenticated user object
        trading_mode: Trading mode ('paper' or 'real')
        
    Returns:
        PortfolioSummary for the specified mode
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

        if trading_mode == "paper":
            # Initialize portfolio if needed
            # The initialize_portfolio method in PortfolioService should handle user context.
            await portfolio_service.initialize_portfolio(current_user.id)
            return await portfolio_service._get_paper_trading_summary() # This might need user_id if paper becomes user-specific
        elif trading_mode == "real":
            return await portfolio_service._get_real_trading_summary(current_user.id)
        elif trading_mode == "both":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Use /snapshot endpoint for 'both' mode"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading_mode: {trading_mode}. Must be 'paper' or 'real'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio summary: {str(e)}"
        )

@router.get("/balance", status_code=status.HTTP_200_OK)
async def get_available_balance(
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    current_user: security_schemas.User = Depends(security_core.get_current_active_user),
    trading_mode: Annotated[TradingMode, Query(description="Trading mode: 'paper', 'real', or 'both'")] = "paper"
):
    """
    Get available balance for trading in the specified mode for the authenticated user.
    
    Args:
        current_user: Authenticated user object
        trading_mode: Trading mode ('paper', 'real', or 'both')
        
    Returns:
        Available balance in USDT
    """
    try:
        if not isinstance(current_user.id, UUID):
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="User ID is not a valid UUID.")

        if trading_mode == "paper":
            # Initialize portfolio if needed
            await portfolio_service.initialize_portfolio(current_user.id)
            return {
                "trading_mode": "paper",
                "available_balance_usdt": portfolio_service.paper_trading_balance, # Assumes paper_trading_balance is correctly set after initialize_portfolio
                "currency": "USDT"
            }
        elif trading_mode == "real":
            real_usdt_balance = await portfolio_service.get_real_usdt_balance(current_user.id)
            return {
                "trading_mode": "real",
                "available_balance_usdt": real_usdt_balance,
                "currency": "USDT"
            }
        elif trading_mode == "both":
            # Return both balances
            await portfolio_service.initialize_portfolio(current_user.id) # For paper balance
            real_usdt_balance = await portfolio_service.get_real_usdt_balance(current_user.id)
            return {
                "trading_mode": "both",
                "paper_balance_usdt": portfolio_service.paper_trading_balance,
                "real_balance_usdt": real_usdt_balance,
                "currency": "USDT"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid trading_mode: {trading_mode}. Must be 'paper', 'real', or 'both'"
            )
            
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve available balance: {str(e)}"
        )
