import asyncio
import aiohttp

from django.core.management.base import BaseCommand


# TARGET_URL = 'https://send-conversions-to-google-ads-t2px3tzmra-uc.a.run.app/conversion'
TARGET_URL = "http://192.168.1.149:3000/process"


async def make_post_request(session, data):
    max_retries = 3
    wait_time = 2
    retries = 0
    while retries < max_retries:
        try:
            response = await session.post(TARGET_URL, json=data, timeout=240)
            response.raise_for_status()
            return response.status
        except (
            Exception,
            aiohttp.ClientResponseError,
            aiohttp.ClientConnectionError,
        ) as e:
            retries += 1
            print(f"Retrying request after exception: {e}")  # noqa
            await asyncio.sleep(wait_time)
    return 500


class Command(BaseCommand):

    def handle(self, *args, **options):
        async def main():
            request_batch = []
            for _ in range(0, 10):
                tickets_container = []
                for _ in range(0, 10):
                    data = {
                        "customer_id": "2874732500",
                        "mcc_id": "5764436564",
                        "conversions": [
                            {
                                "conversion_action_id": "704314739",
                                "conversion_date_time": "2024-03-10 12:50:00+00:00",  # noqa
                                "gclid": "CjwKCAiAxaCvBhBaEiwAvsLmWAHtzZd7RLPO4FHZhFI6qFGVWvtFk-NptumcgfKZwher6ZCUJlOWJRoCAygQAvD_BwE",  # noqa
                                "order_id": "REPLACE ME: order_id_of_call_for_deduplication.",  # noqa
                                "conversion_value": 1.01,
                            }
                        ],
                    }
                    tickets_container.append(data)
                request_batch.append(tickets_container)
            async with aiohttp.ClientSession() as session:
                tasks = []
                for request in request_batch:
                    tasks.append(make_post_request(session, request))
                responses = await asyncio.gather(*tasks)

                for idx, status in enumerate(responses):
                    if status == 200:
                        print(f"Success: request {idx+1}")  # noqa
                    else:
                        print(f"Failed: request {idx+1}")  # noqa

        asyncio.run(main())
