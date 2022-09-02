import json
from urllib import response
import requests
import logging
import aiohttp

from .exceptions import *

logger = logging.getLogger(__name__)


API_ENDPOINT = "https://apigw.verymobile.it/api"
REQUIRED_HEADERS = {"X-Wind-Client": "app-and", "X-Language": "en", "X-Brand": "DEA"}

class VeryAPI():
    def __init__(self, username, password, session=None) -> None:
        self._token = ""
        self._lines = {} # format "LINE_NUMBER": "CONTRACT_ID"
        self._username = username
        self._password = password

        self._session = aiohttp.ClientSession() if session is not None else session
    
    async def login(self):
        
        data = {
            "username": self._username,
            "password": self._password,
            "rememberMe": False
        }

        async with self._session.post(url=f"{API_ENDPOINT}/v4/login/credentials", headers=REQUIRED_HEADERS, json=data) as resp:
            logger.debug(f"W3 response status {resp.status}")
            logger.debug(await resp.text())

            
            if resp.status != 200:
                logger.error(f"VeryAPI: response code {resp.status}")
                raise AuthenticationException(resp.json())

            if "X-W3-Token" not in resp.headers:
                logger.error(f"VeryAPI: token not in header")
                raise AuthenticationException(resp.json())

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

    async def _request_unfolded(self, lineid, contractid):
        headers = REQUIRED_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self._token}"

        data = {"contractId": contractid, "lineId": lineid}

        async with self._session.get(url=f"{API_ENDPOINT}/ob/v2/contract/lineunfolded", headers=headers, params=data) as resp:

            if resp.status != 200:
                logger.error(f"VeryAPI: response code {resp.status}")
                raise RuntimeError(f"VeryAPI: response code {resp.status}")
        
            return await resp.json()

    async def get_counters(self, line):

        json = await self._request_unfolded(line, self._lines[line])

        for oline in json["data"]["lines"]:
            
            if oline["id"] != line:
                continue
            
            sel_line = oline
        
        insights = oline["insightsSummary"]

        return {
            "credit": oline["credit"],
            "voiceMinutes": insights["national"]["voice"]["available"] if not insights["national"]["voice"]["unlimited"] else -1,
            "sms": insights["national"]["sms"]["available"] if not insights["national"]["sms"]["unlimited"] else -1,
            "dataNational": insights["national"]["data"]["available"] if not insights["national"]["data"]["unlimited"] else -1,
            "dataRoaming": insights["roaming"]["data"]["available"] if not insights["roaming"]["data"]["unlimited"] else -1,
        }
            



    



