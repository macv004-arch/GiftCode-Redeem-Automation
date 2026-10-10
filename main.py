import os
import time
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"
PLAYER_INFO_URL = "https://ks-giftcode.centurygame.com/api/get_player"

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
    try:
        with open(filename, "r") as f:
            for line in f:
                clean_id = line.strip().strip('"\'')
                if clean_id and clean_id.isdigit():
                    player_ids.append(clean_id)
    except Exception as e:
        print(f"Error reading {filename}: {e}")
    return player_ids

def get_player_name(player_id, session):
    """Safely retrieves in-game nickname without crashing."""
    payload = {"fid": str(player_id)}
    try:
        response = session.post(PLAYER_INFO_URL, data=payload, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            res_json = response.json()
            if "data" in res_json and isinstance(res_json["data"], dict):
                nickname = res_json["data"].get("nickname")
                if nickname:
                    return nickname
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
        response = session.post(CLAIM_URL, data=payload, headers=HEADERS, timeout=10)
        
        if response.status_code == 403:
            return False, "HTTP 403 (Blocked by anti-bot)", 403
        elif response.status_code != 200:
            return False, f"HTTP Error {response.status_code}", response.status_code

        res_json = response.json()
        msg = res_json.get("msg", "Response received")
        err_code = res_json.get("err_code", -1)
        code_val = res_json.get("code", -1)
        
        # Determine success status
        is_success = (err_code == 0 or code_val == 0) and ("already" not in str(msg).lower())
        return is_success, msg, err_code

    except requests.exceptions.JSONDecodeError:
        return False, "Server returned HTML/Non-JSON response", -1
    except Exception as e:
        return False, f"Request failed: {e}", -1

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No valid numeric Player IDs found in playerIDs.txt.")
        return

    session = requests.Session()
    
    # Pre-warm session cookies to prevent 403 errors
    try:
        session.get("https://ks-giftcode.centurygame.com/", headers=HEADERS, timeout=10)
    except Exception:
        pass

    codes = get_active_codes(session)
    print(f"=== Starting Auto-Redeem for {len(player_ids)} account(s) against {len(codes)} code(s) ===\n")
    
    successful_list = []
    unsuccessful_list = []

    for pid in player_ids:
        pname = get_player_name(pid, session)
        print(f"Processing Account: {pname} (ID: {pid})...")
        
        for code in codes:
            success, msg, err_code = redeem_code(pid, code, session)
            entry = f"[{pname}] (ID: {pid}) | Code: {code} -> {msg}"
            
            if success:
                successful_list.append(entry)
            else:
                unsuccessful_list.append(entry)
            
            time.sleep(1)

    # --- Print Structured Summary ---
    print("\n" + "=" * 60)
    print(" SUCCESSFUL REDEMPTIONS ")
    print("=" * 60)
    if successful_list:
        for item in successful_list:
            print(f" SUCCESS: {item}")
    else:
        print("None (No new codes claimed on this run)")

    print("\n" + "=" * 60)
    print(" NOT REDEEMED / SKIPPED / ALREADY CLAIMED ")
    print("=" * 60)
    if unsuccessful_list:
        for item in unsuccessful_list:
            print(f" SKIPPED/FAILED: {item}")
    else:
        print("None")
    print("=" * 60 + "\n")

if __name__ == "__main__":
    main()
