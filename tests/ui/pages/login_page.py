from selenium.webdriver.common.by import By
from .base_page import BasePage

class LoginPage(BasePage):
    """
    Page Object para la página de inicio de sesión.
    Define los elementos y las acciones específicas de esta página.
    """
    # --- Localizadores ---
    # Se utilizan tuplas (estrategia, valor) para definir los localizadores de elementos.
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.ID, "error-message")

    def __init__(self, driver):
        """
        Inicializa la página de Login.
        """
        super().__init__(driver)
        # Opcional: verificar que estamos en la página correcta.
        # assert "Login" in self.get_title()

    # --- Acciones de la Página ---
    def enter_username(self, username: str):
        """
        Escribe el nombre de usuario en el campo correspondiente.
        """
        self._type_text(self.USERNAME_INPUT, username)

    def enter_password(self, password: str):
        """
        Escribe la contraseña en el campo correspondiente.
        """
        self._type_text(self.PASSWORD_INPUT, password)

    def click_login_button(self):
        """
        Hace clic en el botón de inicio de sesión.
        """
        self._click(self.LOGIN_BUTTON)

    def get_error_message(self) -> str:
        """
        Obtiene el texto de un mensaje de error, si es visible.
        """
        return self._find_element(self.ERROR_MESSAGE).text

    # --- Flujo de Negocio ---
    def login(self, username: str, password: str):
        """
        Realiza el flujo completo de inicio de sesión.
        
        :param username: El nombre de usuario.
        :param password: La contraseña.
        :return: Una instancia del Page Object de la siguiente página (ej. Dashboard).
        """
        self.enter_username(username)
        self.enter_password(password)
        self.click_login_button()
        
        # Esta es una práctica común en POM: el método de flujo devuelve
        # una instancia de la página a la que se navega.
        # from .main_dashboard_page import MainDashboardPage
        # return MainDashboardPage(self.driver)
        # Como MainDashboardPage no existe aún, lo dejamos comentado.
        return None # Temporalmente
