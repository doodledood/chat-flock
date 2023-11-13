from typing import Any, Optional, Tuple

import json
import logging
import os
import time

from bs4 import BeautifulSoup
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_fixed, wait_random

from ..errors import NonTransientHTTPError, TransientHTTPError
from .base import PageRetriever

try:
    from selenium import webdriver
    from selenium.common import NoSuchElementException, StaleElementReferenceException
    from selenium.common.exceptions import NoSuchFrameException, TimeoutException, WebDriverException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.webdriver import WebDriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.remote.remote_connection import LOGGER
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.wait import WebDriverWait
    from webdriver_manager.chrome import ChromeDriverManager
except ModuleNotFoundError as e:
    raise ImportError(
        "Selenium or webdriver_manager is not installed. "
        "Please install these packages to use the SeleniumPageRetriever. "
        "You can do this by running `pip install selenium webdriver_manager`."
    ) from e

LOGGER.setLevel(logging.NOTSET)


class SeleniumPageRetriever(PageRetriever):
    def __init__(
        self,
        headless: bool = False,
        main_page_timeout: int = 10,
        main_page_min_wait: int = 2,
        driver_implicit_wait: int = 1,
        driver_page_load_timeout: Optional[int] = None,
        include_iframe_html: bool = True,
        iframe_timeout: int = 10,
        user_agent: Optional[str] = None,
    ):
        if main_page_timeout < main_page_min_wait:
            raise ValueError("Main page timeout must be greater than or equal to main_page_min_wait.")

        self.main_page_min_wait = main_page_min_wait
        self.main_page_timeout = main_page_timeout
        self.driver_implicit_wait = driver_implicit_wait
        self.driver_page_load_timeout = driver_page_load_timeout or main_page_timeout
        self.include_iframe_html = include_iframe_html
        self.iframe_timeout = iframe_timeout
        self.user_agent = user_agent
        self.headless = headless

        self.service: Optional[Service] = None
        self.driver: Optional[WebDriver] = None

    def create_driver_and_service(self) -> Tuple[WebDriver, Service]:
        if self.driver is not None and self.service is not None:
            return self.driver, self.service

        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        chrome_options.add_argument("--no-sandbox")  # Bypass OS security model
        chrome_options.add_argument("--disable-gpu")  # Applicable to windows os only
        chrome_options.add_argument("start-maximized")  # Open the browser in maximized mode
        chrome_options.add_argument("disable-infobars")  # Disabling infobars
        chrome_options.add_argument("--disable-extensions")  # Disabling extensions
        chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
        chrome_options.add_argument("--ignore-certificate-errors")  # Ignore certificate errors
        chrome_options.add_argument("--incognito")  # Incognito mode
        chrome_options.add_argument("--log-level=0")  # To disable the logging

        if self.user_agent:
            chrome_options.add_argument(f"user-agent={self.user_agent}")

        # To solve tbsCertificate logging issue
        chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

        # Enable Performance Logging
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        chrome_options.set_capability("pageLoadStrategy", "normal")

        service = Service(ChromeDriverManager().install(), log_output=os.devnull)
        driver = webdriver.Chrome(service=service, options=chrome_options)

        return driver, service

    def extract_html_from_driver(self, driver: WebDriver) -> str:
        # Wait for minimum time first
        time.sleep(self.main_page_min_wait)

        try:
            # Wait for the main document to be ready
            WebDriverWait(driver, self.main_page_timeout - self.main_page_min_wait).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )

            iframe_contents = {}

            if self.include_iframe_html:
                # Find all iframe elements
                iframes = driver.find_elements(By.TAG_NAME, "iframe")

                # Iterate over each iframe, switch to it, and capture its HTML
                for iframe in iframes:
                    try:
                        # Wait for the iframe to be available and for its document to be fully loaded
                        WebDriverWait(driver, self.iframe_timeout).until(
                            lambda d: EC.frame_to_be_available_and_switch_to_it(iframe)(d)  # type: ignore
                            and d.execute_script("return document.readyState") == "complete"
                        )

                        # Set a temporary ID on the iframe, so we can find it later
                        driver.execute_script(
                            "arguments[0].setAttribute('selenium-temp-id', arguments[1])", iframe, iframe.id
                        )
                        iframe_id = iframe.get_attribute("selenium-temp-id")

                        # Capture the iframe HTML
                        iframe_html = driver.page_source

                        iframe_soup = BeautifulSoup(iframe_html, "html.parser")
                        iframe_body = iframe_soup.find("body")

                        iframe_contents[iframe_id] = iframe_body
                    except (StaleElementReferenceException, NoSuchFrameException, NoSuchElementException):
                        # If the iframe is no longer available, skip it
                        pass
                    finally:
                        # Switch back to the main content after each iframe
                        driver.switch_to.default_content()

            # Capture the main document HTML
            main_html = driver.page_source
            soup = BeautifulSoup(main_html, "html.parser")

            for frame_id, iframe_body in iframe_contents.items():
                # Insert the iframe body after the iframe element in the main document
                soup_iframe = soup.find("iframe", {"selenium-temp-id": frame_id})
                if soup_iframe is None:
                    continue

                soup_iframe.insert_after(iframe_body)

            # The soup object now contains the modified HTML
            full_html = str(soup)

            return full_html
        except (WebDriverException, NoSuchFrameException) as e:
            return f"An error occurred while retrieving the page: {e}"

    @retry(
        retry=retry_if_exception_type(TransientHTTPError),
        wait=wait_fixed(2) + wait_random(0, 2),
        stop=stop_after_attempt(3),
    )
    def retrieve_html(self, url: str, **kwargs: Any) -> str:
        try:
            driver, service = self.create_driver_and_service()

            # Implicitly wait for elements to be available and set timeout
            driver.implicitly_wait(self.driver_implicit_wait)
            driver.set_page_load_timeout(self.driver_page_load_timeout)

            driver.get(url)

            # Wait and extract the HTML
            full_html = self.extract_html_from_driver(driver)

            # Now retrieve the logs and check the status code
            logs = driver.get_log("performance")
            status_code = None
            for entry in logs:
                log = json.loads(entry["message"])["message"]
                if log["method"] == "Network.responseReceived" and "response" in log["params"]:
                    status_code = log["params"]["response"]["status"]
                    break

            if status_code is None:
                raise Exception("No HTTP response received.")
            elif status_code >= 500:
                raise TransientHTTPError(status_code, "Server error encountered.")
            elif 400 <= status_code < 500:
                raise NonTransientHTTPError(status_code, "Client error encountered.")

            return full_html  # or driver.page_source if you wish to return the original source
        except TimeoutException:
            raise TransientHTTPError(408, "Timeout while waiting for the page to load.")

    def close(self):
        if self.driver:
            self.driver.quit()

        if self.service:
            self.service.stop()
