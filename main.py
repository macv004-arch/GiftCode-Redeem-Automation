import os
import time
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"
PLAYER_INFO_URL = "https://kingshot.net/api/player-info"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Content-Type": "application/x-www-form-urlencoded",
    "Origin": "https://ks-giftcode.centurygame.com",
    "Referer": "https://ks-giftcode.centurygame.com/",
    "Sec-Ch-Ua": '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
    "Sec-Ch-Ua-Mobile": "?0",
    "Sec-Ch-Ua-Platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin"
}

FALLBACK_CODES = ["Hangul2026", "WELLDONE", "Kingshot888", "VIP777"]

def load_player_ids():
    filename = "playerIDs.txt"
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    
    player_ids = []
    with open(filename, "r") as f:
        for line in f:
            clean_id = line.strip().strip('"\'')
            if clean_id and clean_id.isdigit():
                player_ids.append(clean_id)
    return player_ids

def get_player_name(player_id, session):
    """Fetches in-game player name using the Kingshot player API."""
    try:
        url = f"{PLAYER_INFO_URL}?playerId={player_id}"
        response = session.get(url, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and isinstance(res_json["data"], dict):
                nickname = res_json["data"].get("nickname") or res_json["data"].get("name")
                if nickname:
                    return nickname
            elif "nickname" in res_json:
                return res_json["nickname"]
            elif "name" in res_json:
                return res_json["name"]
    except Exception:
        pass
    return f"Player_{player_id[-4:]}"

def get_active_codes(session):
    fetched_codes = []
    try:
        res = session.get("https://kingshot.net/api/cdk", timeout=10)
        if res.status_code == 200:
            data = res.json()
            fetched_codes = data.get("codes", [])
    except Exception:
        pass

    all_codes = list(dict.fromkeys(fetched_codes + FALLBACK_CODES))
    return all_codes

def redeem_code(player_id, code, session):
    payload = {
        "fid": str(player_id),
        "cdk": str(code)
    }
    try:
        response = session.post(CLAIM_URL, data=payload, timeout=10)
        
        if response.status_code == 403:
            return False, "HTTP 403 Forbidden (Blocked)", 403
        elif response.status_code != 200:
            return False, f"HTTP Error {response.status_code}", response.status_code

        res_json = response.json()
        msg = res_json.get("msg", "Response received")
        err_code = res_json.get("err_code", -1)
        code_val = res_json.get("code", -1)
        
        is_success = (err_code == 0 or code_val == 0) and ("already" not in str(msg).lower())
        return is_success, msg, err_code

    except ValueError:
        return False, "Invalid non-JSON response", -1
    except Exception as e:
        return False, str(e), -1

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No valid numeric Player IDs found in playerIDs.txt.")
        return

    session = requests.Session()
    session.headers.update(HEADERS)
    
    # Warm up session cookies
    try
