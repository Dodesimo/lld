'''
maintains a code, date, the corresponding compartment, and we assess whether expired or not and allow us to fetch the compartment
'''
from datetime import datetime
from typing import Optional

class AccessToken:
    def __init__(self, code: str, expiration: datetime, compartment):
        self.code = code
        self.expiration = expiration
        self.compartment = compartment
    
    def is_expired(self) -> bool:
        return datetime.now() >= self.expiration
    
    def get_compartment(self):
        return self.compartment
    
    def get_code(self) -> str:
        return self.code