import os
import re
import json
import requests
from dotenv import load_dotenv
from termcolor import colored


class AmazonScraper:

    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Load API key from environment variables
        self.apiKey = os.getenv("APIKEY")

        # List of domain names associated with Amazon
        self.domainNames = ["amazon", "amzn"]

        # URL for the scraper API
        self.scraperUrl = "https://api.scraperapi.com/structured/amazon/product"

    def getDomain(self, url: str) -> str:
        try:
            # Extract domain name from URL
            domainName = url.split("/")[2][::-1].split(".")[1][::-1]

            if domainName in self.domainNames:
                return domainName
            else:
                raise ValueError("The domain name is not valid.")

        # Raise error when exception occurs while trying to extract domain name from URL
        except IndexError:
            raise ValueError("Please enter a valid URL with a domain name.")

        except Exception as e:
            raise ValueError(f"{e}")

    def extractASIN(self, url: str) -> str:
        # Regular expression pattern to extract ASIN from URL
        asinPattern = r"/([A-Z0-9]{10})(?:[/?]|$)"

        # Search for ASIN pattern in URL
        match = re.search(asinPattern, url)

        if match:
            return match.group(1)
        else:
            return None

    def fetchProductASIN(self, url: str, domainName: str) -> str:
        if domainName == self.domainNames[0]:
            # If domain is "amazon", directly extract ASIN from URL
            productASIN = self.extractASIN(url)

        elif domainName == self.domainNames[1]:
            # If domain is "amzn", follow redirects to actual Amazon URL and then extract ASIN
            response = requests.get(url, allow_redirects=True)
            productASIN = self.extractASIN(response.url)

        return productASIN

    def fetchProductImage(self, imageUrl: str) -> str:
        try:
            response = requests.get(imageUrl)

            if response.status_code == 200:
                with open("static/images/Amazon/image.jpg", "wb") as f:
                    f.write(response.content)
            else:
                print(f"Failed to fetch image. Status code: {response.status_code}")

        except Exception as e:
            print(f"An error occurred while fetching the image: {e}")

    def fetchProductData(self, payload: dict) -> str:
        try:
            # Send request to scraper API with payload
            response = requests.get(self.scraperUrl, params=payload)
            response.raise_for_status()  # Raise HTTPError for status codes 4xx or 5xx

            data = json.loads(response.text)

            productName = data.get("name")
            productPrice = data.get("pricing")
            productImageUrl = data.get("images")[0]

            if productName and productPrice and productImageUrl:
                print(
                    colored("\nProduct Name: ", "yellow")
                    + colored(f"{productName}", "cyan")
                )
                print(
                    colored("Product Price: ", "yellow")
                    + colored(f"{productPrice}\n", "cyan")
                )
                self.fetchProductImage(productImageUrl)

            else:
                print("Incomplete data received from the Scraper API")

        except requests.exceptions.RequestException as e:
            print(f"Error occurred while making the request to the Scraper API: {e}")

        except (KeyError, json.JSONDecodeError) as e:
            print(
                f"Error occurred while parsing the response from the Scraper API: {e}"
            )

        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def main():
    # Create object of AmazonScraper class
    scraper = AmazonScraper()

    try:
        # Get target product URL from user
        targetUrl = input(
            colored("\nEnter the URL of the product to track it's price: ", "yellow")
        )

        # Determine domain from URL
        domainName = scraper.getDomain(targetUrl)

        if domainName:
            # Fetch ASIN of the product
            productASIN = scraper.fetchProductASIN(targetUrl, domainName)

            if productASIN:
                # Prepare payload for fetching product data
                payload = {
                    "api_key": scraper.apiKey,
                    "asin": productASIN,
                    "country": "in",
                    "tld": "in",
                    "autoparse": "true",
                }
                # Fetch product data using payload
                scraper.fetchProductData(payload)
            else:
                print(
                    colored("Error: ", "red") + "Failed to extract ASIN from given URL"
                )
        else:
            print(
                colored("Error: ", "red")
                + "Failed to determine domain from provided URL"
            )

    except ValueError as ve:
        print(colored("Error: ", "red") + f"{ve}")

    except Exception as e:
        print(colored("Error: ", "red") + f"{e}")


# Entry point of the script
if __name__ == "__main__":
    main()
