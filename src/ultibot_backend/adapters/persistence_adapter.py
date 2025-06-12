"""
Adaptador para la persistencia de datos, utilizando Supabase como backend.
Implementa la interfaz IPersistencePort, traduciendo las operaciones de dominio
a interacciones con la base de datos de Supabase.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from uuid import UUID

from supabase import create_client, Client

from src.ultibot_backend.core.ports import IPersistencePort, ICredentialProvider
from src.ultibot_backend.core.domain_models.trading import Trade, TradeId
from src.ultibot_backend.core.domain_models.portfolio import Portfolio, UserId, Asset
from src.ultibot_backend.core.domain_models.prompt_models import PromptTemplate, PromptVersion
from src.ultibot_backend.core.domain_models.scan_presets import ScanPreset, ScanResult
from src.ultibot_backend.core.exceptions import PersistenceError, CredentialError

class SupabasePersistenceAdapter(IPersistencePort):
    """
    Adaptador de persistencia que utiliza Supabase para almacenar y recuperar datos.
    """
    def __init__(self, credential_provider: ICredentialProvider):
        """
        Inicializa el SupabasePersistenceAdapter.

        Args:
            credential_provider (ICredentialProvider): Proveedor de credenciales para acceder a la URL y clave de Supabase.
        """
        self._credential_provider = credential_provider
        self._supabase_client: Optional[Client] = None

    async def _initialize_client(self):
        """Inicializa el cliente de Supabase y carga las credenciales."""
        if self._supabase_client is None:
            try:
                supabase_url = await self._credential_provider.get_credential("SUPABASE_URL")
                supabase_key = await self._credential_provider.get_credential("SUPABASE_ANON_KEY")
                self._supabase_client = create_client(supabase_url, supabase_key)
            except Exception as e:
                raise CredentialError(f"Fallo al cargar credenciales de Supabase: {e}")

    async def save_trade(self, trade: Trade) -> TradeId:
        """
        Guarda un registro de trade en la tabla 'trades' de Supabase.

        Args:
            trade (Trade): Objeto Trade a guardar.

        Returns:
            TradeId: ID del trade guardado.

        Raises:
            PersistenceError: Si ocurre un error al guardar el trade.
        """
        await self._initialize_client()
        try:
            data_to_insert = {
                "id": str(trade.id.value),
                "symbol": trade.symbol,
                "side": trade.side.value,
                "quantity": float(trade.quantity),
                "price": float(trade.price),
                "timestamp": trade.timestamp.isoformat(),
                "strategy_id": trade.strategy_id,
                "order_type": trade.order_type.value,
                "fee": float(trade.fee) if trade.fee is not None else None,
                "fee_asset": trade.fee_asset
            }
            response = self._supabase_client.table("trades").insert(data_to_insert).execute()
            if response.data:
                return TradeId(value=UUID(response.data[0]["id"]))
            raise PersistenceError("No se pudo guardar el trade, respuesta vacía.")
        except Exception as e:
            raise PersistenceError(f"Error al guardar trade en Supabase: {e}") from e

    async def get_portfolio(self, user_id: UserId) -> Portfolio:
        """
        Obtiene el portfolio de un usuario específico de la tabla 'portfolios' de Supabase.
        Si no existe, devuelve un portfolio vacío.

        Args:
            user_id (UserId): ID del usuario.

        Returns:
            Portfolio: Objeto Portfolio del usuario.

        Raises:
            PersistenceError: Si ocurre un error al obtener el portfolio.
        """
        await self._initialize_client()
        try:
            response = self._supabase_client.table("portfolios").select("*").eq("user_id", str(user_id.value)).limit(1).execute()
            if response.data:
                portfolio_data = response.data[0]
                assets_data = portfolio_data.get("assets", {})
                assets = {
                    sym: Asset(
                        symbol=sym,
                        quantity=Decimal(str(data["quantity"])),
                        average_buy_price=Decimal(str(data["average_buy_price"])),
                        current_price=Decimal(str(data["current_price"])),
                        last_updated=datetime.fromisoformat(data["last_updated"])
                    ) for sym, data in assets_data.items()
                }
                return Portfolio(
                    user_id=UserId(value=UUID(portfolio_data["user_id"])),
                    assets=assets,
                    total_value_usd=Decimal(str(portfolio_data["total_value_usd"])),
                    available_balance_usd=Decimal(str(portfolio_data["available_balance_usd"])),
                    last_updated=datetime.fromisoformat(portfolio_data["last_updated"])
                )
            # Si no se encuentra, devolver un portfolio vacío
            return Portfolio(user_id=user_id)
        except Exception as e:
            raise PersistenceError(f"Error al obtener portfolio de Supabase para {user_id.value}: {e}") from e

    async def save_portfolio(self, portfolio: Portfolio) -> None:
        """
        Guarda el estado actual de un portfolio en la tabla 'portfolios' de Supabase.
        Si el portfolio ya existe, lo actualiza; de lo contrario, lo inserta.

        Args:
            portfolio (Portfolio): El objeto Portfolio a guardar.

        Raises:
            PersistenceError: Si ocurre un error al guardar el portfolio.
        """
        await self._initialize_client()
        try:
            data_to_upsert = {
                "user_id": str(portfolio.user_id.value),
                "assets": {sym: asset.model_dump() for sym, asset in portfolio.assets.items()},
                "total_value_usd": float(portfolio.total_value_usd),
                "available_balance_usd": float(portfolio.available_balance_usd),
                "last_updated": portfolio.last_updated.isoformat()
            }
            # Usar upsert para insertar o actualizar
            response = self._supabase_client.table("portfolios").upsert(data_to_upsert, on_conflict="user_id").execute()
            if not response.data:
                raise PersistenceError(f"No se pudo guardar el portfolio para el usuario {portfolio.user_id.value}.")
        except Exception as e:
            raise PersistenceError(f"Error al guardar portfolio en Supabase para {portfolio.user_id.value}: {e}") from e

    async def get_trade_history(self, user_id: UserId, symbol: Optional[str] = None) -> List[Trade]:
        """
        Obtiene el historial de trades para un usuario de la tabla 'trades' de Supabase,
        opcionalmente filtrado por símbolo.

        Args:
            user_id (UserId): ID del usuario.
            symbol (Optional[str]): Símbolo para filtrar (opcional).

        Returns:
            List[Trade]: Lista de objetos Trade.

        Raises:
            PersistenceError: Si ocurre un error al obtener el historial de trades.
        """
        await self._initialize_client()
        try:
            query = self._supabase_client.table("trades").select("*").eq("user_id", str(user_id.value))
            if symbol:
                query = query.eq("symbol", symbol)
            response = query.order("timestamp", desc=True).execute()
            
            trades = []
            for trade_data in response.data:
                trades.append(Trade(
                    id=TradeId(value=UUID(trade_data["id"])),
                    symbol=trade_data["symbol"],
                    side=trade_data["side"],
                    quantity=Decimal(str(trade_data["quantity"])),
                    price=Decimal(str(trade_data["price"])),
                    timestamp=datetime.fromisoformat(trade_data["timestamp"]),
                    strategy_id=trade_data.get("strategy_id"),
                    order_type=trade_data["order_type"],
                    fee=Decimal(str(trade_data["fee"])) if trade_data.get("fee") else None,
                    fee_asset=trade_data.get("fee_asset")
                ))
            return trades
        except Exception as e:
            raise PersistenceError(f"Error al obtener historial de trades de Supabase para {user_id.value}: {e}") from e

    async def create_prompt_version(self, name: str, new_template: str, variables: Optional[dict] = None, description: Optional[str] = None) -> PromptVersion:
        """
        Crea una nueva versión de un prompt en la tabla 'ai_prompts' de Supabase.
        Si el prompt ya existe, incrementa la versión.

        Args:
            name (str): Nombre del prompt.
            new_template (str): Nuevo contenido de la plantilla.
            variables (Optional[dict]): Variables asociadas al prompt.
            description (Optional[str]): Descripción del prompt.

        Returns:
            PromptVersion: Objeto PromptVersion creado.

        Raises:
            PersistenceError: Si ocurre un error al crear la versión del prompt.
        """
        await self._initialize_client()
        try:
            # Obtener la versión actual del prompt
            response = self._supabase_client.table("ai_prompts").select("id, version").eq("name", name).limit(1).execute()
            
            prompt_id: UUID
            current_version: int = 0

            if response.data:
                prompt_id = UUID(response.data[0]["id"])
                current_version = response.data[0]["version"]
                # Actualizar el prompt existente para incrementar la versión
                self._supabase_client.table("ai_prompts").update({"version": current_version + 1, "template": new_template, "variables": variables, "description": description, "updated_at": datetime.utcnow().isoformat()}).eq("id", str(prompt_id)).execute()
            else:
                # Crear un nuevo prompt
                new_prompt_data = {
                    "name": name,
                    "template": new_template,
                    "variables": variables,
                    "description": description,
                    "is_active": True
                }
                insert_response = self._supabase_client.table("ai_prompts").insert(new_prompt_data).execute()
                if insert_response.data:
                    prompt_id = UUID(insert_response.data[0]["id"])
                else:
                    raise PersistenceError("No se pudo crear el nuevo prompt.")
            
            return PromptVersion(
                prompt_id=prompt_id,
                version_number=current_version + 1,
                template=new_template,
                variables=variables or {}
            )
        except Exception as e:
            raise PersistenceError(f"Error al crear versión de prompt en Supabase: {e}") from e

    async def get_prompt_template(self, name: str) -> Optional[PromptTemplate]:
        """
        Obtiene la plantilla de prompt más reciente por nombre de la tabla 'ai_prompts' de Supabase.

        Args:
            name (str): Nombre del prompt.

        Returns:
            Optional[PromptTemplate]: Objeto PromptTemplate si se encuentra, None en caso contrario.

        Raises:
            PersistenceError: Si ocurre un error al obtener la plantilla del prompt.
        """
        await self._initialize_client()
        try:
            response = self._supabase_client.table("ai_prompts").select("*").eq("name", name).limit(1).execute()
            if response.data:
                prompt_data = response.data[0]
                return PromptTemplate(
                    id=UUID(prompt_data["id"]),
                    name=prompt_data["name"],
                    template=prompt_data["template"],
                    variables=prompt_data.get("variables", {}),
                    description=prompt_data.get("description"),
                    is_active=prompt_data["is_active"],
                    created_at=datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.fromisoformat(prompt_data["updated_at"])
                )
            return None
        except Exception as e:
            raise PersistenceError(f"Error al obtener plantilla de prompt de Supabase: {e}") from e

    async def list_prompts(self) -> List[PromptTemplate]:
        """
        Lista todas las plantillas de prompts activas de la tabla 'ai_prompts' de Supabase.

        Returns:
            List[PromptTemplate]: Lista de objetos PromptTemplate.

        Raises:
            PersistenceError: Si ocurre un error al listar las plantillas de prompts.
        """
        await self._initialize_client()
        try:
            response = self._supabase_client.table("ai_prompts").select("*").eq("is_active", True).execute()
            prompts = []
            for prompt_data in response.data:
                prompts.append(PromptTemplate(
                    id=UUID(prompt_data["id"]),
                    name=prompt_data["name"],
                    template=prompt_data["template"],
                    variables=prompt_data.get("variables", {}),
                    description=prompt_data.get("description"),
                    is_active=prompt_data["is_active"],
                    created_at=datetime.fromisoformat(prompt_data["created_at"]),
                    updated_at=datetime.fromisoformat(prompt_data["updated_at"])
                ))
            return prompts
        except Exception as e:
            raise PersistenceError(f"Error al listar plantillas de prompts de Supabase: {e}") from e

    async def save_scan_result(self, scan_result: ScanResult) -> None:
        """
        Guarda un resultado de escaneo de mercado en la tabla 'scan_results' de Supabase.

        Args:
            scan_result (ScanResult): El resultado del escaneo a guardar.

        Raises:
            PersistenceError: Si ocurre un error al guardar el resultado del escaneo.
        """
        await self._initialize_client()
        try:
            data_to_insert = {
                "id": str(scan_result.result_id),
                "preset_name": scan_result.preset_name,
                "symbol": scan_result.symbol,
                "score": float(scan_result.score),
                "matched_criteria": scan_result.matched_criteria,
                "timestamp": scan_result.timestamp.isoformat()
            }
            self._supabase_client.table("scan_results").insert(data_to_insert).execute()
        except Exception as e:
            raise PersistenceError(f"Error al guardar resultado de escaneo en Supabase: {e}") from e

    async def get_scan_presets(self) -> List[ScanPreset]:
        """
        Obtiene todos los presets de escaneo de mercado de la tabla 'scan_presets' de Supabase.

        Returns:
            List[ScanPreset]: Lista de objetos ScanPreset.

        Raises:
            PersistenceError: Si ocurre un error al obtener los presets de escaneo.
        """
        await self._initialize_client()
        try:
            response = self._supabase_client.table("scan_presets").select("*").eq("is_active", True).execute()
            presets = []
            for preset_data in response.data:
                presets.append(ScanPreset(
                    id=UUID(preset_data["id"]),
                    name=preset_data["name"],
                    description=preset_data.get("description"),
                    criteria=preset_data["criteria"],
                    is_active=preset_data["is_active"],
                    created_at=datetime.fromisoformat(preset_data["created_at"]),
                    updated_at=datetime.fromisoformat(preset_data["updated_at"])
                ))
            return presets
        except Exception as e:
            raise PersistenceError(f"Error al obtener presets de escaneo de Supabase: {e}") from e

class PostgresPersistenceAdapter(IPersistencePort):
    """
    Adaptador de persistencia que utiliza PostgreSQL directamente.
    (Implementación esqueleto para resolver dependencias)
    """
    def __init__(self, credential_provider: ICredentialProvider):
        self._credential_provider = credential_provider
        # La inicialización de la conexión se manejará aquí

    async def save_trade(self, trade: Trade) -> TradeId:
        raise NotImplementedError

    async def get_portfolio(self, user_id: UserId) -> Portfolio:
        raise NotImplementedError

    async def save_portfolio(self, portfolio: Portfolio) -> None:
        raise NotImplementedError

    async def get_trade_history(self, user_id: UserId, symbol: Optional[str] = None) -> List[Trade]:
        raise NotImplementedError

    async def create_prompt_version(self, name: str, new_template: str, variables: Optional[dict] = None, description: Optional[str] = None) -> PromptVersion:
        raise NotImplementedError

    async def get_prompt_template(self, name: str) -> Optional[PromptTemplate]:
        raise NotImplementedError

    async def list_prompts(self) -> List[PromptTemplate]:
        raise NotImplementedError

    async def save_scan_result(self, scan_result: ScanResult) -> None:
        raise NotImplementedError

    async def get_scan_presets(self) -> List[ScanPreset]:
        raise NotImplementedError
