import pytest
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from webdriver_manager.chrome import ChromeDriverManager

@pytest.fixture(scope="function")
def driver():
    """
    Fixture de Pytest para gestionar el ciclo de vida del WebDriver de Chrome.

    - Se ejecuta una vez por cada función de test (scope='function').
    - Instala/actualiza y configura automáticamente el driver de Chrome.
    - Configurado para ejecutarse en modo headless para entornos de CI/CD.
    - Inicializa el driver antes del test.
    - Cierra el driver (quit) después de que el test finaliza.
    """
    chrome_options = ChromeOptions()
    chrome_options.binary_location = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Configura y crea una instancia del driver de Chrome utilizando webdriver-manager
    # para asegurar que el driver es compatible con la versión del navegador instalada.
    driver_instance = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=chrome_options
    )
    
    # Cede el control y la instancia del driver al test que lo solicita.
    yield driver_instance
    
    # Teardown: Esta parte se ejecuta después de que el test ha finalizado.
    # Cierra todas las ventanas del navegador y termina el proceso del WebDriver.
    driver_instance.quit()
