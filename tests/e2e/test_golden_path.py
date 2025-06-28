import re
from playwright.sync_api import Page, expect

def test_homepage_has_ultibot_in_title(page: Page, live_server):
    """
    Verifies that the homepage loads and has the correct title.
    """
    # Navigate to the local application's homepage.
    page.goto(live_server)

    # Expect the title to contain "UltiBot".
    expect(page).to_have_title(re.compile("UltiBot"))
