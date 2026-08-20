from datetiime import datetime, timedelta
from typing import Optional
import random

class Locker:
    def __init__(self, compartments: list["Compartment"]):
        self.compartments = compartments
        self.access_token_mapping = {} # map strings to access tokens
    
    def deposit_package(self, size: "Size") -> str:
        compartment = _get_available_compartment(size)
        if not compartment:
            raise Exception(f"No available compartment of the size {size}")
        
        compartment.open()
        compartment.mark_occupied()
        accessToken = self._generate_access_token(compartment)
        self.access_token_mapping[accessToken.get_code()] = accessToken
        return accessToken.get_code()

    def pickup(self, tokenCode: str):
        # check null string
        if not tokenCode or tokenCode not in self.access_token_mapping:
            raise Exception("Invalid token")
        
        accessToken = self.access_token_mapping[tokenCode]
        if accessToken.is_expired(): # check if the token is expired
            raise Exception("Access token has expired")

        self._clear_deposit(access_token)

    def open_expired_compartments(self) -> None:
        for accessToken in self.access_token_mapping.values():
            if accessToken.is_expired():
                accessToken.compartment.open()

    def _get_available_compartment(self, size):
        for c in compartments:
            if c.get_size() == size and not c.is_occupied:
                return c
        return None
    
    def _generate_access_token(self, compartment: "Compartment") -> "AccessToken":
        randomToken = f"{random.randint(0, 999999)}"
        expirationDate = datetime.now() + timedelta(days=7)
        return AccessToken(randomToken, expirationDate, compartment)
    
    def _clear_deposit(self, access_token: "AccessToken") -> "None":
        compartment = access_token.get_compartment()
        compartment.open() # staff pick it up
        compartment.mark_free()
        self.access_token_mapping.pop(access_token.get_code())
