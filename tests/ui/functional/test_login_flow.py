import pytest
from tests.ui.pages.login_page import LoginPage

@pytest.mark.functional
def test_successful_login(driver):
    """
    Test funcional para el flujo de inicio de sesión exitoso.

    1. Navega a la página de login.
    2. Utiliza el LoginPage para ingresar credenciales válidas.
    3. Verifica que la navegación a la página segura fue exitosa.
    """
    # 1. Navegar a la página de login de práctica
    driver.get("http://the-internet.herokuapp.com/login")

    # 2. Instanciar el Page Object y ejecutar el flujo de login
    login_page = LoginPage(driver)
    # Las credenciales 'tomsmith' / 'SuperSecretPassword!' son las válidas para este sitio de práctica.
    login_page.login("tomsmith", "SuperSecretPassword!")

    # 3. Verificar el resultado
    # Después de un login exitoso, la URL cambia a /secure
    assert "/secure" in driver.current_url, "La URL no cambió a la página segura después del login."

    # Opcionalmente, se podría crear un SecurePage y verificar elementos allí.
    # Por ejemplo: assert "You logged into a secure area!" in driver.page_source
