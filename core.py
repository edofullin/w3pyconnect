import requests
import logging

logger = logging.getLogger(__name__)

API_ENDPOINT = "https://apigw.verymobile.it/api"
REQUIRED_HEADERS = {"X-Wind-Client": "app-and", "X-Language": "en", "X-Brand": "DEA"}

class VeryAPI():
    def __init__(self, username, password) -> None:
        self._token = ""
        self._lines = {} # format "LINE_NUMBER": "CONTRACT_ID"
        self._username = username
        self._password = password
    
    def login(self):
        
        data = {
            "username": self._username,
            "password": self._password,
            "rememberMe": False
        }

        resp = requests.post(f"{API_ENDPOINT}/v4/login/credentials", headers=REQUIRED_HEADERS, json=data)

        if resp.status_code != 200:
            logger.error(f"VeryAPI: response code {resp.status_code}")
            raise RuntimeError(f"VeryAPI: response code {resp.status_code}")

        if "X-W3-Token" not in resp.headers:
            logger.error(f"VeryAPI: token not in header")
            raise RuntimeError(f"VeryAPI: token not in header")

        self._token = resp.headers["X-W3-Token"]
        
        json_resp = resp.json()

        for contract in json_resp["data"]["contracts"]:
            for line in contract["lines"]:
                self._lines[line["id"]] = line["contractId"] # will there ever only be one per contract? sperèm

    def get_line_numbers(self):
        return self._lines.keys()

    def _request_unfolded(self, lineid, contractid):
        headers = REQUIRED_HEADERS.copy()
        headers["Authorization"] = f"Bearer {self._token}"

        data = {"contractId": contractid, "lineId": lineid}

        resp = requests.get(f"{API_ENDPOINT}/ob/v2/contract/lineunfolded", headers=headers, params=data)

        if self._token == "" or resp.status_code == 401:
            self.login()
            resp = requests.get(f"{API_ENDPOINT}/ob/v2/contract/lineunfolded")
        
        if resp.status_code != 200:
            logger.error(f"VeryAPI: response code {resp.status_code}")
            raise RuntimeError(f"VeryAPI: response code {resp.status_code}")
        
        return resp.json()

    def get_counters(self, line):

        json = self._request_unfolded(line, self._lines[line])
        sel_line = None

        for oline in json["data"]["lines"]:
            
            if oline["id"] != line:
                continue
            
            sel_line = oline
        
        insights = oline["insightsSummary"]

        return {
            "CREDIT": oline["credit"],
            "VOICE": insights["national"]["voice"]["available"] if not insights["national"]["voice"]["unlimited"] else -1,
            "SMS": insights["national"]["sms"]["available"] if not insights["national"]["sms"]["unlimited"] else -1,
            "DATA_NATIONAL": insights["national"]["data"]["available"] if not insights["national"]["data"]["unlimited"] else -1,
            "DATA_ROAMING": insights["roaming"]["data"]["available"] if not insights["roaming"]["data"]["unlimited"] else -1,
        }
            



    



