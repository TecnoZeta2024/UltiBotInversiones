# Debug Log for Dev Agent (Cline)

## Story 2.3 - Pylance Errors in src/ultibot_ui/widgets/market_data_widget.py (Detected 2025-05-30)

These errors are not directly related to the current task (Subtask 1.1 of Story 2.3) but were detected after a file modification. They are logged here for future reference and will be addressed if they become blockers for the current story or are explicitly requested.

- [Pylance Error] Line 51: "setSectionResizeMode" is not a known attribute of "None"
- [Pylance Error] Line 52: "setVisible" is not a known attribute of "None"
- [Pylance Error] Line 34: Result of async function call is not used; use "await" or assign result to variable
- [Pylance Error] Line 88: Cannot access attribute "AlignRight" for class "type[Qt]"
  Attribute "AlignRight" is unknown
- [Pylance Error] Line 102: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 107: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 121: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 127: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 133: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 144: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 150: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 163: Argument of type "() -> Task[None]" cannot be assigned to parameter "slot" of type "PYQT_SLOT" in function "connect"
  Type "() -> Task[None]" is not assignable to type "PYQT_SLOT"
    Type "() -> Task[None]" is not assignable to type "(...) -> None"
      Function return type "Task[None]" is incompatible with type "None"
        "Task[None]" is not assignable to "None"
    "function" is not assignable to "pyqtBoundSignal"
- [Pylance Error] Line 290: "setSectionResizeMode" is not a known attribute of "None"
- [Pylance Error] Line 291: "setSectionResizeMode" is not a known attribute of "None"
- [Pylance Error] Line 292: "setVisible" is not a known attribute of "None"
- [Pylance Error] Line 277: Cannot access attribute "CaseInsensitive" for class "type[Qt]"
  Attribute "CaseInsensitive" is unknown
- [Pylance Error] Line 350: Cannot access attribute "AlignCenter" for class "type[Qt]"
  Attribute "AlignCenter" is unknown
- [Pylance Error] Line 461: Argument of type "MockMarketDataService" cannot be assigned to parameter "market_data_service" of type "MarketDataService" in function "__init__"
  "MockMarketDataService" is not assignable to "MarketDataService"
- [Pylance Error] Line 461: Argument of type "MockConfigService" cannot be assigned to parameter "config_service" of type "ConfigService" in function "__init__"
  "MockConfigService" is not assignable to "ConfigService"
- [Pylance Error] Line 474: Argument of type "() -> Task[None]" cannot be assigned to parameter "slot" of type "PYQT_SLOT" in function "connect"
  Type "() -> Task[None]" is not assignable to type "PYQT_SLOT"
    Type "() -> Task[None]" is not assignable to type "(...) -> None"
      Function return type "Task[None]" is incompatible with type "None"
        "Task[None]" is not assignable to "None"
    "function" is not assignable to "pyqtBoundSignal"
