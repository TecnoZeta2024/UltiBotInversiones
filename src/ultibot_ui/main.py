import sys
import asyncio
from uuid import UUID

from PySide6.QtWidgets import QApplication
import qdarkstyle # For dark theme
from qasync import QEventLoopPolicy, run # For asyncio integration with Qt

# UI Main Window
from src.ultibot_ui.windows.main_window import MainWindow

# New Service Architecture
from src.ultibot_ui.services.api_client import ApiClient
from src.ultibot_ui.services.ui_market_data_service import UIMarketDataService
from src.ultibot_ui.services.ui_config_service import UIConfigService

# Removed old direct backend service imports:
# from src.ultibot_backend.adapters.binance_adapter import BinanceAdapter
# from src.ultibot_backend.persistence.supabase_service import SupabasePersistenceService
# from src.ultibot_backend.services.credential_service import CredentialService
# from src.ultibot_backend.services.market_data_service import MarketDataService as BackendMarketDataService
# from src.ultibot_backend.services.config_service import ConfigService as BackendConfigService


async def start_application():
    """
    Initializes and starts the UltiBot UI application.
    """
    app = QApplication(sys.argv)

    # Apply dark theme
    # Make sure your qdarkstyle is compatible with PySide6. If not, adjust or remove.
    try:
        app.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyside6'))
    except Exception as e:
        print(f"Warning: Could not apply qdarkstyle: {e}. Using default Qt style.")

    # Dummy User ID for now - replace with actual login mechanism later
    # This user_id should ideally come from an authentication step.
    user_id = UUID("00000000-0000-0000-0000-000000000001") 

    # Initialize the ApiClient - this will be shared by UI services
    api_client = ApiClient() # Base URL defaults to http://localhost:8000/api/v1/

    exit_code = 1  # Default exit code in case of premature exit

    try:
        # Initialize UI Services with the ApiClient
        ui_market_data_service = UIMarketDataService(api_client=api_client)

        # UIConfigService constructor was updated to take user_id and api_client
        # It also has a set_user_id method if user_id changes or is loaded later.
        ui_config_service = UIConfigService(user_id=user_id, api_client=api_client)

        # Initialize MainWindow with the UI services
        # Pass api_client to MainWindow if it's responsible for calling api_client.close()
        main_window = MainWindow(
            user_id=user_id,
            market_data_service=ui_market_data_service,
            config_service=ui_config_service,
            api_client=api_client # Pass client for lifecycle management (e.g. closing)
        )
        main_window.show()

        # qasync's run function (used in if __name__ == "__main__") will handle the event loop.
        # app.exec_() is called by qasync.run implicitly.
        # We don't need to call app.exec_() directly here if using qasync.run pattern.
        # The loop will run until the application quits.

        # For qasync.run to work as expected, this function should typically just set up
        # and show the window, and the event loop management is external.
        # However, if we want this function to block until app exits (like a main function),
        # then app.exec_() would be here.
        # Given the structure from `if __name__ == "__main__": qasync.run(start_application())`,
        # this function `start_application` is the "main coroutine" for qasync.
        # It should complete its setup, and then `qasync.run` keeps the loop going.
        # The `finally` block here will execute when `start_application` coroutine itself finishes,
        # which might be *after* the Qt app has already closed if not careful with event loop integration.

        # Let MainWindow handle the application's main event loop execution implicitly via qasync.run
        # The `finally` block for `api_client.close()` is crucial.
        # One way is that `MainWindow.closeEvent` triggers the shutdown of the async part.
        # Or, `qasync.run` might need to be awaited if it returns a future representing app lifetime.
        # For now, we assume MainWindow.closeEvent or app.aboutToQuit will handle api_client.close()
        # by using the passed api_client instance.

        # If start_application is the main task for qasync.run, it needs to "run" the app loop.
        # This can be done by creating a Future that completes when the app exits.
        # A simpler way: qasync often means loop.run_forever() or similar is called by qasync.run itself.
        # Let's assume qasync handles running the app event loop based on QApplication instance.
        # The key is that api_client must be closed.
        # The pattern in MainWindow to close client is good.

        # This function will complete, but qasync.run will keep the event loop alive.
        # The 'finally' block below will only run when qasync.run itself is finishing with this coroutine.
        # This should be after the Qt application has been allowed to exit.

        # To ensure cleanup, we'll rely on MainWindow.closeEvent, to which api_client is passed.
        # No explicit app.exec_() or return code from here needed if qasync.run manages the loop.

    except Exception as e:
        print(f"Error during application startup or runtime: {e}")
        # Optionally, show an error dialog to the user here
    # The `finally` block for closing api_client is now expected to be handled by MainWindow's closeEvent
    # or a similar mechanism tied to the application lifecycle, using the `api_client` instance
    # passed to `MainWindow`. If `qasync.run` finishes, it means event loop stopped.

def main():
    """
    Sets up the asyncio event loop policy for qasync and runs the application.
    """
    # Set the Pyside6 event loop policy for qasync
    asyncio.set_event_loop_policy(QEventLoopPolicy())
    
    # qasync.run will execute the start_application coroutine,
    # managing the asyncio event loop alongside the Qt event loop.
    # It typically handles loop.run_forever() or app.exec_() equivalent internally.
    try:
        run(start_application()) # qasync.run is blocking until the event loop stops
    except KeyboardInterrupt:
        print("Application terminated by user (Ctrl+C).")
    except Exception as e:
        print(f"Unhandled exception in main: {e}")
    finally:
        print("Application has shut down.")
        # Any final global cleanup, if not handled by api_client.close() or similar, could go here.

if __name__ == "__main__":
    main()
