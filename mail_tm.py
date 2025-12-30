import requests
import time
import random
import string
import re

class MailTm:
    BASE_URL = "https://api.mail.tm"

    def __init__(self):
        self.session = requests.Session()
        self.domain = self._get_domain()
        self.address = None
        self.password = None
        self.token = None
        self.account_id = None

    def _get_domain(self):
        res = self.session.get(f"{self.BASE_URL}/domains")
        return res.json()["hydra:member"][0]["domain"]

    def create_account(self):
        username = "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
        self.address = f"{username}@{self.domain}"
        self.password = "pass12345"
        
        res = self.session.post(f"{self.BASE_URL}/accounts", json={
            "address": self.address,
            "password": self.password
        })
        if res.status_code == 201:
            self.account_id = res.json()["id"]
            return self.address
        return None

    def login(self):
        res = self.session.post(f"{self.BASE_URL}/token", json={
            "address": self.address,
            "password": self.password
        })
        if res.status_code == 200:
            self.token = res.json()["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return True
        return False

    def get_otp(self, timeout=120):
        print(f"Waiting for OTP for {self.address}...")
        start = time.time()
        while time.time() - start < timeout:
            try:
                res = self.session.get(f"{self.BASE_URL}/messages")
                if res.status_code == 200:
                    messages = res.json()["hydra:member"]
                    if messages:
                        for msg in messages:
                            msg_id = msg["id"]
                            msg_res = self.session.get(f"{self.BASE_URL}/messages/{msg_id}")
                            if msg_res.status_code == 200:
                                data = msg_res.json()
                                # Check intro, text, and html
                                content = (data.get("intro") or "") + (data.get("text") or "") + (data.get("html") or [""])[0]
                                print(f"Checking message: {data.get('subject')}")
                                otp = re.search(r"\b(\d{6})\b", content)
                                if otp:
                                    print(f"Found OTP: {otp.group(1)}")
                                    return otp.group(1)
            except Exception as e:
                print(f"Error checking messages: {e}")
            time.sleep(5)
        print("OTP timeout reached")
        return None
