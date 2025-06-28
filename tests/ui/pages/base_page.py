from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class BasePage:
    """
    Clase base para todas las páginas (Page Objects).
    Abstrae las interacciones comunes con el WebDriver de Selenium.
    """
    def __init__(self, driver: WebDriver):
        """
        Inicializa la BasePage con una instancia del WebDriver.

        :param driver: La instancia del WebDriver de Selenium.
        """
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)  # Espera explícita por defecto de 10 segundos

    def _find_element(self, locator: tuple):
        """
        Encuentra un elemento esperando a que sea visible.

        :param locator: Tupla que contiene la estrategia de localización y el valor (ej. (By.ID, 'mi-id')).
        :return: El objeto WebElement encontrado.
        """
        return self.wait.until(EC.visibility_of_element_located(locator))

    def _click(self, locator: tuple):
        """
        Hace clic en un elemento después de asegurarse de que es clickeable.

        :param locator: Tupla del localizador del elemento.
        """
        self.wait.until(EC.element_to_be_clickable(locator)).click()

    def _type_text(self, locator: tuple, text: str):
        """
        Limpia un campo de texto y escribe el texto proporcionado.

        :param locator: Tupla del localizador del elemento.
        :param text: El texto a escribir en el campo.
        """
        element = self._find_element(locator)
        element.clear()
        element.send_keys(text)

    def get_title(self) -> str:
        """
        Obtiene el título de la página actual.

        :return: El título de la página como una cadena de texto.
        """
        return self.driver.title
