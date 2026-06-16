import requests
from pathlib import Path


class Downloader:

    @staticmethod
    def download(url, destination):

        destination = Path(destination)

        destination.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        response = requests.get(
            url,
            stream=True
        )

        response.raise_for_status()

        with open(destination, "wb") as f:

            for chunk in response.iter_content(
                chunk_size=8192
            ):
                f.write(chunk)

        return destination