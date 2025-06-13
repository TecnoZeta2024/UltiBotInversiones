import asyncio
import sys
import psycopg
from psycopg_pool import AsyncConnectionPool
import logging
import os
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from uuid import UUID, uuid4
from datetime import datetime, timezone
from psycopg.rows import dict_row
from psycopg.sql import SQL, Identifier, Composed, Composable
from psycopg.types.json import Jsonb
import json
from sqlalchemy.ext.asyncio import AsyncSession

# Solución para Windows ProactorEventLoop con psycopg
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from ..app_config import AppSettings
from src.ultibot_backend.core.domain_models.opportunity_models import Opportunity, OpportunityStatus
from src.ultibot_backend.core.domain_models.trade import Trade
from src.ultibot_backend.core.domain_models.trading_strategy_models import TradingStrategyConfig
from src.ultibot_backend.core.domain_models.user_configuration_models import ScanPreset, MarketScanConfiguration
from src.shared.data_types import APICredential, ServiceName, Notification, MarketData

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass

# Definir type hints para uso en el módulo
OpportunityTypeHint = Opportunity
OpportunityStatusTypeHint = OpportunityStatus


class SupabasePersistenceService:
    def __init__(self, db_session: Optional[AsyncSession] = None, app_settings: Optional[AppSettings] = None):
        self.pool: Optional[AsyncConnectionPool] = None
        self.session: Optional[AsyncSession] = db_session
        
        if app_settings:
            self.db_url: Optional[str] = app_settings.database_url
            self.fixed_user_id = UUID(app_settings.fixed_user_id)
        else:
            self.db_url = os.getenv("DATABASE_URL")
            self.fixed_user_id = UUID(os.getenv("FIXED_USER_ID", "00000000-0000-0000-0000-000000000001"))

        if not self.db_url and not self.session:
            logger.error("DATABASE_URL no se encontró y no se proporcionó ninguna sesión de BD.")
        

    async def connect(self):
        if self.session:
            logger.info("Utilizando sesión de base de datos inyectada. No se creará un nuevo pool.")
            return
            
        if self.pool and not self.pool.closed:
            logger.info("El pool de conexiones ya está activo.")
            return

        if not self.db_url:
            logger.error("DATABASE_URL no está configurada. No se puede inicializar el pool de conexiones.")
            raise ValueError("DATABASE_URL no está configurada en las variables de entorno.")

        try:
            min_size = int(os.getenv("DB_POOL_MIN_SIZE", "2"))
            max_size = int(os.getenv("DB_POOL_MAX_SIZE", "10"))
            
            conn_str = f"{self.db_url}?sslmode=verify-full&sslrootcert=supabase/prod-ca-2021.crt"
            
            self.pool = AsyncConnectionPool(
                conninfo=conn_str,
                min_size=min_size,
                max_size=max_size,
                name="supabase_pool"
            )
            await self.pool.open()
            logger.info(f"Pool de conexiones a Supabase (psycopg_pool) establecido exitosamente. Min: {min_size}, Max: {max_size}")
        except Exception as e:
            logger.error(f"Error al establecer el pool de conexiones a Supabase (psycopg_pool): {e}")
            if isinstance(e, psycopg.Error) and hasattr(e, 'diag') and e.diag:
                 logger.error(f"Detalles del error de PSQL (diag): {e.diag.message_primary}")
            self.pool = None
            raise

    async def disconnect(self):
        if self.session:
            logger.info("Sesión de base de datos inyectada. El cierre es gestionado externamente.")
            return
            
        if self.pool and not self.pool.closed:
            await self.pool.close()
            logger.info("Pool de conexiones a Supabase (psycopg_pool) cerrado.")
            self.pool = None

    async def _get_connection(self):
        """Obtiene una conexión, ya sea del pool o de la sesión inyectada."""
        if self.session:
            connection = await self.session.connection()
            return connection.connection
            
        if not self.pool or self.pool.closed:
            logger.warning("El pool de conexiones está cerrado o no existe. Intentando reconectar...")
            await self.connect()
        
        assert self.pool is not None, "Fallo crítico al reconectar el pool."
        
        try:
            await self.pool.check()
        except Exception as e:
            logger.error(f"Fallo en la comprobación de salud del pool. Intentando reconectar. Error: {e}")
            await self.disconnect()
            await self.connect()
            assert self.pool is not None, "Fallo crítico al reconectar el pool después de un check fallido."
        
        return self.pool.connection()

    async def get_opportunity_by_id(self, opportunity_id: UUID) -> Optional[Opportunity]:
        conn = await self._get_connection()
        query = SQL("SELECT data FROM opportunities WHERE id = %s AND user_id = %s;")

        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (opportunity_id, self.fixed_user_id))
                    record = await cur.fetchone()
                
                if record and record.get('data'):
                    return Opportunity(**record['data'])
                return None
        except Exception as e:
            logger.error(f"Error al obtener oportunidad por ID {opportunity_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def update_opportunity_status(self, opportunity_id: UUID, new_status: OpportunityStatus, status_reason: Optional[str] = None) -> Optional[Opportunity]:
        conn = await self._get_connection()
        query_str: str = """
        UPDATE opportunities
        SET data = data || jsonb_build_object('status', %s, 'status_reason', %s, 'updated_at', timezone('utc'::text, now())::text),
            updated_at = timezone('utc'::text, now())
        WHERE id = %s AND user_id = %s
        RETURNING data;
        """
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query_str), (new_status.value, status_reason, opportunity_id, self.fixed_user_id))
                    record = await cur.fetchone()
                    if record and record.get('data'):
                        return Opportunity(**record['data'])
            return None
        except Exception as e:
            logger.error(f"Error al actualizar estado de oportunidad {opportunity_id} (psycopg_pool): {e}", exc_info=True)
            raise
    
    async def get_user_configuration(self, user_id: UUID) -> Optional[Dict[str, Any]]:
        conn = await self._get_connection()
        query = SQL("SELECT * FROM user_configurations WHERE user_id = %s;")
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (user_id,))
                    record = await cur.fetchone()
                    if record:
                        return dict(record)
            return None
        except Exception as e:
            logger.error(f"Error al obtener configuración de usuario para {user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def upsert_user_configuration(self, config_data: Dict[str, Any]):
        conn = await self._get_connection()
        from psycopg import sql
        import json
        
        config_to_save = config_data.copy()
        user_id = UUID(config_to_save.pop('user_id'))
        config_to_save.pop('id', None)
        config_to_save.pop('createdAt', None)
        config_to_save.pop('updatedAt', None)

        db_columns_map = {
            "telegramChatId": "telegram_chat_id", "notificationPreferences": "notification_preferences",
            "enableTelegramNotifications": "enable_telegram_notifications", "defaultPaperTradingCapital": "default_paper_trading_capital",
            "paperTradingActive": "paper_trading_active",
            "watchlists": "watchlists", "favoritePairs": "favorite_pairs", "riskProfile": "risk_profile",
            "riskProfileSettings": "risk_profile_settings", "realTradingSettings": "real_trading_settings",
            "aiStrategyConfigurations": "ai_strategy_configurations", "aiAnalysisConfidenceThresholds": "ai_analysis_confidence_thresholds",
            "mcpServerPreferences": "mcp_server_preferences", "selectedTheme": "selected_theme",
            "dashboardLayoutProfiles": "dashboard_layout_profiles", "activeDashboardLayoutProfileId": "active_dashboard_layout_profile_id",
            "dashboardLayoutConfig": "dashboard_layout_config", "cloudSyncPreferences": "cloud_sync_preferences",
        }

        def serialize_if_needed(value):
            if value is None:
                return None
            if isinstance(value, (dict, list)):
                return json.dumps(value)
            return value

        insert_values_dict = {db_columns_map.get(k, k): serialize_if_needed(v) for k, v in config_to_save.items()}
        insert_values_dict['user_id'] = user_id

        json_columns = [
            "notification_preferences", "watchlists", "favorite_pairs", "risk_profile_settings",
            "real_trading_settings", "ai_strategy_configurations", "ai_analysis_confidence_thresholds",
            "mcp_server_preferences", "dashboard_layout_profiles", "dashboard_layout_config", "cloud_sync_preferences"
        ]

        for col in json_columns:
            if col in insert_values_dict and insert_values_dict[col] is not None and not isinstance(insert_values_dict[col], str):
                insert_values_dict[col] = json.dumps(insert_values_dict[col])

        columns = [sql.Identifier(col) for col in insert_values_dict.keys()]
        placeholders = [sql.Placeholder() for _ in insert_values_dict]
        update_set_parts = [
            sql.SQL("{} = EXCLUDED.{}" ).format(sql.Identifier(col), sql.Identifier(col))
            for col in insert_values_dict if col != 'user_id'
        ]
        update_set_str = sql.SQL(", ").join(update_set_parts)

        query = sql.SQL("""
            INSERT INTO user_configurations ({columns})
            VALUES ({placeholders})
            ON CONFLICT (user_id) DO UPDATE SET
                {update_set},
                updated_at = timezone('utc'::text, now())
            RETURNING *;
        """).format(
            columns=sql.SQL(', ').join(columns),
            placeholders=sql.SQL(', ').join(placeholders),
            update_set=update_set_str
        )
        try:
            values = tuple(insert_values_dict.values())
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, values)
            logger.info(f"Configuración de usuario para {user_id} guardada/actualizada exitosamente (psycopg_pool).")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar configuración de usuario para {user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_open_paper_trades(self) -> List[Trade]:
        return await self._get_trades_by_status_and_mode('open', 'paper')

    async def get_open_real_trades(self) -> List[Trade]:
        return await self._get_trades_by_status_and_mode('open', 'real')

    async def _get_trades_by_status_and_mode(self, status: str, mode: str) -> List[Trade]:
        conn = await self._get_connection()

        query = SQL("SELECT data FROM trades WHERE user_id = %s AND data->>'status' = %s AND data->>'mode' = %s;")
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id, status, mode))
                    records = await cur.fetchall()
                    return [Trade(**record['data']) for record in records if 'data' in record]
        except Exception as e:
            logger.error(f"Error al obtener trades para usuario {self.fixed_user_id} con estado {status} y modo {mode}: {e}", exc_info=True)
            raise

    async def upsert_trade(self, trade_data: Dict[str, Any]):
        conn = await self._get_connection()
        
        query: str = """
        INSERT INTO trades (id, user_id, data)
        VALUES (%s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            data = EXCLUDED.data,
            updated_at = timezone('utc'::text, now())
        RETURNING id;
        """
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(SQL(query), (trade_data['id'], self.fixed_user_id, Jsonb(trade_data)))
            logger.info(f"Trade {trade_data['id']} guardado/actualizado exitosamente.")
        except Exception as e:
            logger.error(f"Error al guardar/actualizar trade {trade_data['id']}: {e}", exc_info=True)
            raise

    async def get_closed_trades_count(self, is_real_trade: bool) -> int:
        conn = await self._get_connection()
        mode = 'real' if is_real_trade else 'paper'
        query = SQL("SELECT COUNT(*) FROM trades WHERE user_id = %s AND data->>'status' = 'closed' AND data->>'mode' = %s;")
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(query, (self.fixed_user_id, mode))
                    record = await cur.fetchone()
                    if record:
                        return record['count']
                return 0
        except Exception as e:
            logger.error(f"Error al contar trades cerrados para user {self.fixed_user_id}, real_trade={is_real_trade} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_all_trades_for_user(self, mode: Optional[str] = None) -> List[Trade]:
        conn = await self._get_connection()

        query_parts: List[Composable] = [SQL("SELECT data FROM trades WHERE user_id = %s")]
        params_list: List[Any] = [self.fixed_user_id]
        
        if mode:
            query_parts.append(SQL("AND data->>'mode' = %s"))
            params_list.append(mode)
            
        final_query = SQL(" ").join(query_parts) + SQL(" ORDER BY (data->>'executed_at')::timestamptz DESC;")
        
        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, tuple(params_list))
                    records = await cur.fetchall()
                return [Trade(**record['data']) for record in records if 'data' in record]
        except Exception as e:
            logger.error(f"Error al obtener todos los trades para el usuario {self.fixed_user_id} (psycopg_pool): {e}", exc_info=True)
            raise

    async def get_trades_with_filters(self, filters: Dict[str, Any], limit: int, offset: int) -> List[Trade]:
        conn = await self._get_connection()

        query_parts: List[Composable] = [SQL("SELECT data FROM trades")]
        where_clauses: List[Composable] = [SQL("user_id = %s")]
        params: List[Any] = [self.fixed_user_id]

        for key, value in filters.items():
            if value is not None:
                where_clauses.append(SQL("data->>%s = %s").format(Identifier(key)))
                params.append(value)
        
        if where_clauses:
            query_parts.append(SQL("WHERE"))
            query_parts.append(SQL(" AND ").join(where_clauses))

        query_parts.append(SQL("ORDER BY (data->>'executed_at')::timestamptz DESC LIMIT %s OFFSET %s"))
        params.extend([limit, offset])

        final_query = SQL(" ").join(query_parts)

        try:
            async with conn as c:
                async with c.cursor(row_factory=dict_row) as cur:
                    await cur.execute(final_query, tuple(params))
                    records = await cur.fetchall()
                    return [Trade(**record['data']) for record in records if 'data' in record]
        except Exception as e:
            logger.error(f"Error al obtener trades con filtros {filters}: {e}", exc_info=True)
            raise
