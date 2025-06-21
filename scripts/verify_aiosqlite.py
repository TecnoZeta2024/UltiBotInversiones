import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, text

async def main():
    # Configurar una URL de base de datos en memoria con aiosqlite
    db_url = "sqlite+aiosqlite:///:memory:"
    print(f"Intentando crear motor asíncrono con URL: {db_url}")

    try:
        engine = create_async_engine(db_url)
        print("✅ Motor asíncrono creado exitosamente.")

        Base = declarative_base()

        class TestTable(Base):
            __tablename__ = "test_table"
            id = Column(Integer, primary_key=True)
            name = Column(String)

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("✅ Tablas creadas exitosamente.")

        async_session = AsyncSession(engine)
        async with async_session as session:
            await session.execute(text("INSERT INTO test_table (name) VALUES ('test_entry');"))
            await session.commit()
            print("✅ Datos insertados exitosamente.")

            result = await session.execute(text("SELECT name FROM test_table;"))
            name = result.scalar_one()
            print(f"✅ Dato recuperado: {name}")
            assert name == "test_entry"

        await engine.dispose()
        print("✅ Motor de base de datos dispuesto exitosamente.")

    except Exception as e:
        print(f"❌ Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Verificación completada.")

if __name__ == "__main__":
    asyncio.run(main())
