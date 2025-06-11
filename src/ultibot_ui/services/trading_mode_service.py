import logging
from enum import Enum, auto

from PyQt5.QtCore import QObject, pyqtSignal

logger = logging.getLogger(__name__)

class TradingMode(Enum):
    PAPER = auto()
    REAL = auto()

    def __str__(self):
        return self.name.capitalize()

class TradingModeService(QObject):
    '''
    Manages the global trading mode (Paper or Real) for the UI.
    '''
    mode_changed = pyqtSignal(TradingMode) # Signal to indicate mode change

    def __init__(self, default_mode: TradingMode = TradingMode.PAPER):
        super().__init__()
        self._current_mode: TradingMode = default_mode
        logger.info(f"TradingModeService initialized with mode: {self._current_mode}")

    def get_current_mode(self) -> TradingMode:
        '''
        Returns the current trading mode.
        '''
        return self._current_mode

    def set_mode(self, mode: TradingMode):
        '''
        Sets the trading mode and emits a signal if it changes.
        '''
        logger.debug(f"TradingModeService.set_mode called with {mode}. Current mode is {self._current_mode}")
        if not isinstance(mode, TradingMode):
            logger.error(f"Attempted to set invalid trading mode type: {type(mode)}. Value: {mode}")
            raise ValueError("Mode must be an instance of TradingMode Enum")

        if self._current_mode != mode:
            self._current_mode = mode
            logger.info(f"Trading mode changed to: {self._current_mode}")
            self.mode_changed.emit(self._current_mode)
        else:
            logger.debug(f"Trading mode set to {mode}, but no change detected from current mode {self._current_mode}.")

    def is_paper_mode(self) -> bool:
        '''Returns True if current mode is Paper Trading.'''
        return self._current_mode == TradingMode.PAPER

    def is_real_mode(self) -> bool:
        '''Returns True if current mode is Real Trading.'''
        return self._current_mode == TradingMode.REAL

if __name__ == '__main__':
    # Example Usage (for testing purposes)
    service = TradingModeService()

    def on_mode_change(new_mode):
        print(f"Mode changed via signal: {new_mode}")
        print(f"Is paper: {service.is_paper_mode()}")
        print(f"Is real: {service.is_real_mode()}")

    service.mode_changed.connect(on_mode_change)

    print(f"Initial mode: {service.get_current_mode()}")
    service.set_mode(TradingMode.REAL)
    service.set_mode(TradingMode.REAL) # No change
    service.set_mode(TradingMode.PAPER)

    try:
        service.set_mode("invalid_mode_string")
    except ValueError as e:
        print(f"Error caught: {e}")
