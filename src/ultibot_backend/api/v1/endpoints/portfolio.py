from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from typing import Annotated, Optional, Literal
from uuid import UUID

from shared.data_types import PortfolioSnapshot, PortfolioSummary
from ultibot_backend.services.portfolio_service import PortfolioService
from ultibot_backend import dependencies as deps
from ultibot_backend.app_config import settings

router = APIRouter()

# Trading mode type alias for consistent validation
TradingMode = Literal["paper", "real", "both"]

@router.get("/snapshot", response_model=PortfolioSnapshot, status_code=status.HTTP_200_OK)
async def get_portfolio_snapshot(
    request: Request,
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode filter: 'paper', 'real', or 'both'")] = "both"
):
    """
    Get portfolio snapshot for the fixed user and trading mode.
    
    Args:
        trading_mode: Filter by trading mode ('paper', 'real', 'both')
        
    Returns:
        PortfolioSnapshot with data filtered by trading mode
    """
    user_id = settings.FIXED_USER_ID
    try:
        if trading_mode == "both":
            snapshot = await portfolio_service.get_portfolio_snapshot(user_id)
            return snapshot
        elif trading_mode == "paper":
            await portfolio_service.initialize_portfolio(user_id)
            paper_summary = await portfolio_service._get_paper_trading_summary()
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
            real_summary = await portfolio_service._get_real_trading_summary(user_id)
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
    request: Request,
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode: 'paper' or 'real'")] = "paper"
):
    """
    Get portfolio summary for a specific trading mode for the fixed user.
    
    Args:
        trading_mode: Trading mode ('paper' or 'real')
        
    Returns:
        PortfolioSummary for the specified mode
    """
    user_id = settings.FIXED_USER_ID
    try:
        if trading_mode == "paper":
            await portfolio_service.initialize_portfolio(user_id)
            return await portfolio_service._get_paper_trading_summary()
        elif trading_mode == "real":
            return await portfolio_service._get_real_trading_summary(user_id)
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
    request: Request,
    portfolio_service: Annotated[PortfolioService, Depends(deps.get_portfolio_service)],
    trading_mode: Annotated[TradingMode, Query(description="Trading mode: 'paper', 'real', or 'both'")] = "paper"
):
    """
    Get available balance for trading in the specified mode for the fixed user.
    
    Args:
        trading_mode: Trading mode ('paper', 'real', or 'both')
        
    Returns:
        Available balance in USDT
    """
    user_id = settings.FIXED_USER_ID
    try:
        if trading_mode == "paper":
            await portfolio_service.initialize_portfolio(user_id)
            return {
                "trading_mode": "paper",
                "available_balance_usdt": portfolio_service.paper_trading_balance,
                "currency": "USDT"
            }
        elif trading_mode == "real":
            real_usdt_balance = await portfolio_service.get_real_usdt_balance(user_id)
            return {
                "trading_mode": "real",
                "available_balance_usdt": real_usdt_balance,
                "currency": "USDT"
            }
        elif trading_mode == "both":
            await portfolio_service.initialize_portfolio(user_id)
            real_usdt_balance = await portfolio_service.get_real_usdt_balance(user_id)
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

