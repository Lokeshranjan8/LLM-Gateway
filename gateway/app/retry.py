"""Simple retry helper for calls from the gateway to a provider."""

from fastapi import HTTPException
import requests

MAX_RETRIES = 2


def call_provider(provider_name: str, url: str, message: str) -> dict:
    """Call one provider. Retry timeout, connection, and HTTP 5xx failures."""

    for attempt in range(1, MAX_RETRIES + 2):
        print(f"Calling {provider_name}...")

        try:
            response = requests.post(
                url,
                json={"message": message},
                timeout=10,
            )

            if 200 <= response.status_code < 300:
                print(f"Attempt {attempt} succeeded")
                return response.json()

            if response.status_code >= 500:
                print(f"Attempt {attempt} failed: HTTP {response.status_code}")

                if attempt <= MAX_RETRIES:
                    print("Retrying...")
                    continue

                raise HTTPException(
                    status_code=502,
                    detail=f"{provider_name} failed after {MAX_RETRIES} retries.",
                )

            # HTTP 400-499 are client errors. Do not retry them.
            print(f"HTTP {response.status_code} received. Not retrying.")
            raise HTTPException(
                status_code=response.status_code,
                detail=f"{provider_name} returned a client error.",
            )

        except requests.exceptions.Timeout:
            print(f"Attempt {attempt} failed: request timed out")

            if attempt <= MAX_RETRIES:
                print("Retrying...")
                continue

            raise HTTPException(
                status_code=504,
                detail=f"{provider_name} timed out after {MAX_RETRIES} retries.",
            )

        except requests.exceptions.ConnectionError:
            print(f"Attempt {attempt} failed: unable to connect")

            if attempt <= MAX_RETRIES:
                print("Retrying...")
                continue

            raise HTTPException(
                status_code=503,
                detail=f"Unable to connect to {provider_name} after {MAX_RETRIES} retries.",
            )

        except HTTPException:
            raise

        except Exception as error:
            print(f"Unexpected provider error: {str(error)}")
            raise HTTPException(
                status_code=500,
                detail="An unexpected provider error occurred.",
            )
