import asyncio
import json
from urllib import response
import requests
import logging
import aiohttp
import time

from .exceptions import *

logger = logging.getLogger(__name__)


API_ENDPOINT = "https://apigw.verymobile.it/api"
REQUIRED_HEADERS = {"X-Wind-Client": "app-and", "X-Language": "en", "X-Brand": "DEA"}
RATE_LIMIT = 7
MAX_RETRY = 3

class W3API():
    def __init__(self, username, password, session=None) -> None:
        self._token = ""
        self._lines = {} # format "LINE_NUMBER": "CONTRACT_ID"
        self._username = username
        self._password = password
        self._last_request = 0

        self._session = aiohttp.ClientSession() if session is None else session
    
    async def login(self, depth=0):
        
        data = {
            "username": self._username,
            "password": self._password,
            "rememberMe": False
        }

        if abs(time.time() - self._last_request) < RATE_LIMIT:
            logger.warn("W3: rate limiting")
            await asyncio.sleep(RATE_LIMIT)

        async with self._session.post(url=f"{API_ENDPOINT}/v4/login/credentials", headers=REQUIRED_HEADERS, json=data) as resp:
            self._last_request = time.time()
            logger.debug(f"W3 response status {resp.status}")
 
            if resp.status == 429:
                if depth > MAX_RETRY:
                    raise RateLimitException()

                logger.warn("W3: rate limiting")
                await asyncio.sleep(RATE_LIMIT)

                return await self.login(depth+1)

            if resp.status != 200:
                logger.error(f"VeryAPI: response code {resp.status}")
                raise AuthenticationException(await resp.json())

            if "X-W3-Token" not in resp.headers:
                logger.error(f"VeryAPI: token not in header")
                raise AuthenticationException(await resp.json())

            self._token = resp.headers["X-W3-Token"]
            
            json_resp = await resp.json()

        for contract in json_resp["data"]["contracts"]:
            for line in contract["lines"]:
                if not line["mobile"]:
                    logger.info(f"Line {line['id']} is not a mobile line, skipping")
                    continue

                self._lines[line["id"]] = line["contractId"] # will there ever only be one per contract? sperèm

    def get_line_numbers(self):
        return self._lines.keys()

    async def _request_unfolded(self, lineid, contractid, depth=0):
        if self._token is None:
            self.login()

        headers = REQUIRED_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self._token}"

        data = {"contractId": contractid, "lineId": lineid}

        if abs(time.time() - self._last_request) < RATE_LIMIT:
            logger.warn("W3: rate limiting")
            await asyncio.sleep(RATE_LIMIT)

        async with self._session.get(url=f"{API_ENDPOINT}/ob/v2/contract/lineunfolded", headers=headers, params=data) as resp:
            self._last_request = time.time()

            if resp.status == 429:
                if depth > MAX_RETRY:
                    raise RateLimitException()

                logger.warn("W3: rate limiting")
                await asyncio.sleep(RATE_LIMIT)

                return await self._request_unfolded(lineid, contractid, depth+1)
            
            if resp.status != 200:
                logger.error(f"VeryAPI: response code {resp.status}")
                raise RuntimeError(f"VeryAPI: response code {resp.status}")
        
            return await resp.json()

    async def get_lines_counters(self):
        counters = []

        for id,cid in self._lines.items():
            cnt = await self.get_counters(id)
        
        counters.append(cnt)

        return counters

    async def get_counters(self, line):

        json = await self._request_unfolded(line, self._lines[line])

        for oline in json["data"]["lines"]:
            
            if oline["id"] != line:
                continue
            
            sel_line = oline
        
        insights = oline["insightsSummary"]

        return {
            "number": line,
            "credit": oline["credit"],
            "voiceMinutes": insights["national"]["voice"]["available"] if not insights["national"]["voice"]["unlimited"] else -1,
            "sms": insights["national"]["sms"]["available"] if not insights["national"]["sms"]["unlimited"] else -1,
            "dataNational": insights["national"]["data"]["available"] if not insights["national"]["data"]["unlimited"] else -1,
            "dataRoaming": insights["roaming"]["data"]["available"] if not insights["roaming"]["data"]["unlimited"] else -1,
        }
    
    async def close(self):
        await self._session.close()
        self._session = None



    



