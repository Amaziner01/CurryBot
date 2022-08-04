# Libraries 
from copy import copy
import datetime
import requests
import json
import os

from typing import Callable, Union, List, Tuple

class CountryCodeError(Exception):
    pass

class RequestError(Exception):
    def __init__(self, response: requests.Response, *args: object) -> None:
        self.status_code = response.status_code
        self.text = response.text
        super().__init__(*args)

    def __str__(self) -> str:
        return super().__str__().join('Status Code: {0}; Body: {1}.'.format(self.status_code, self.text))

class CurrencyConverter:
    def __init__(self, apikey) -> None:
        self.apikey = apikey
        self.convertions = dict()
        self.currencies = dict()

        if not os.path.exists("./data"): # data folder
            os.mkdir("data")

        if not self.try_update_currencies(): # Currency data loading
            self.currencies = self.__load_snapshot("data/currencies_snapshot.json", "currencies")
        if not self.try_update_convertions(): # Convertion data loading
            self.convertions = self.__load_snapshot("data/convertions_snapshot.json", "convertions")

    def __load_snapshot(self, snapshot_path: str, data_name: str) -> dict:
        with open(snapshot_path, 'r') as fp:
            json_body = json.load(fp)
            fetched_data = copy(json_body[data_name])
            fp.close()
        return fetched_data

    def __try_update_snapshot(self, snapshot_path: str, data_name: str, 
                              fetch_n_dump_method: Callable) -> Union[dict, None]:
        
        if os.path.exists(snapshot_path): # Fetch snapshot of convertions.
            # Check when the last snapshot was taken, and compare it with the current time.
            # If 24 hours passed, fetch new data.

            snapshot_datetime = None

            with open(snapshot_path, 'r') as fp:
                curr_time = datetime.datetime.now()
                snapshot = json.load(fp)
                snapshot_datetime = datetime.datetime.fromisoformat(snapshot["datetime"])
                fp.close()
            pass

            time_delta = datetime.datetime.now() - snapshot_datetime
            if time_delta > datetime.timedelta(hours=24):
                # 24 Hours have passed since the last time the data was fetched. An update.
                # should take place.
                fetch_n_dump_method(snapshot_path)
            else:
                return None

        else: # Generate new snapshot.
            fetch_n_dump_method(snapshot_path)
        
        # At this point, the snapshot file must be available.

        """ 
        with open(snapshot_path, 'r') as fp:
            json_body = json.load(fp)
            fetched_data = copy(json_body[data_name])
            fp.close() 
        """

        fetched_data = self.__load_snapshot(snapshot_path, data_name)

        return fetched_data

    def __country_conv_exists(self, cntry: str) -> bool:
        if ("USD" + cntry) in list(self.convertions.keys()):
            return True
        return False

    def __fetch_conversions(self) -> dict:
        url = "https://api.apilayer.com/currency_data/live?source=USD&currencies="
        url += ''.join([i + ',' for i in self.currencies])[:-1]
        res = requests.get(url, headers={ "apikey": self.apikey })
        if res.status_code == 200:
            return res.json()
        raise RequestError(res)

    def __fetch_currencies(self) -> dict:
        url = "https://api.apilayer.com/currency_data/list"
        res = requests.get(url, headers={ "apikey": self.apikey })
        if res.status_code == 200:
            return res.json()
        raise RequestError(res)

    def __fetch_n_dump_conversions(self, filepath: str) -> None:
        convertions = self.__fetch_conversions()

        with open(filepath, 'w') as fp:
            json_body = { "convertions": convertions["quotes"],
                          "datetime": str(datetime.datetime.now()) } 
            fp.write(json.dumps(json_body))
            fp.close()
        pass

    def __fetch_n_dump_currencies(self, filepath: str) -> None:
        convertions = self.__fetch_currencies()

        with open(filepath, 'w') as fp:
            json_body = { "currencies": convertions["currencies"],
                          "datetime": str(datetime.datetime.now()) } 
            fp.write(json.dumps(json_body))
            fp.close()
        pass

    def convert(self, ammount: float, from_cntry: str, to_cntry) -> Union[float, None]: # Currency convertions
        if self.__country_conv_exists(from_cntry) and self.__country_conv_exists(to_cntry):
            return ammount * self.convertions[("USD" + to_cntry)]\
                           / self.convertions[("USD" + from_cntry)]
        return None

    def list_currencies(self) -> List[str]: # Available currencies listing
        return list(self.currencies)

    def list_countries(self) -> List[str]:
        return list(self.currencies.values())

    def list_countries_and_codes(self) -> List[str]:
        return [(i, j) for i, j in zip(self.list_countries(), self.list_currencies())]

    def try_update_currencies(self) -> bool:
        data = self.__try_update_snapshot("data/currencies_snapshot.json", "currencies",
                                                     self.__fetch_n_dump_currencies)
        if data == None:
            return False
        
        self.currencies = data
        return True
    
    def try_update_convertions(self) -> bool:
        data = self.__try_update_snapshot("data/convertions_snapshot.json", "convertions",
                                                     self.__fetch_n_dump_conversions)
        if data == None:
            return False
        
        self.convertions = data
        return True