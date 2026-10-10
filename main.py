import os
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"
PLAYER_INFO_URL = "https://ks-giftcode.centurygame.com/api/get_player"

# Standard browser headers to avoid Cloudflare/WAF blocks
HEADERS = {
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Origin": "https://ks-giftcode.centurygame.com",
    "Referer": "https://ks-giftcode.centurygame.com/"
}

# Fallback codes in case the api feed is unreachable
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

def get_player_name(player_id):
    """Fetches the in-game nickname associated with the Player ID."""
    payload = {"fid": str(player_id)}
    try:
        response = requests.post(PLAYER_INFO_URL, data=payload, headers=HEADERS, timeout=10)
        res_json = response.json()
        if "data" in res_json and isinstance(res_json["data"], dict):
            nickname = res_json["data"].get("nickname")
            if nickname:
                return nickname
    except Exception:
        pass
    return "Player"

def get_active_codes():
    fetched_codes = []
    api_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        res = requests.get("https://kingshot.net/api/cdk", headers=api_headers, timeout=10)
        if res.status_code == 200:
            data = res.json()
            fetched_codes = data.get("codes", [])
    except Exception as e:
        print(f"Notice: Could not fetch live codes from API ({e}). Using static list.")

    # Merge live codes with fallbacks to guarantee we always test active codes
    all_codes = list(dict.fromkeys(fetched_codes + FALLBACK_CODES))
    return all_codes

def redeem_code(player_id, code):
    payload = {
        "fid": str(player_id),
        "cdk": str(code)
    }
    try:
        response = requests.post(CLAIM_URL, data=payload, headers=HEADERS, timeout=10)
        res_json = response.json()
        msg = res_json.get("msg", "Response received")
        err_code = res_json.get("err_code", -1)
        
        is_success = (err_code == 0) or ("success" in str(msg).lower())
        return is_success, msg, err_code
    except Exception as e:
        return False, str(e), -1

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No valid numeric Player IDs found in playerIDs.txt.")
        return

    codes = get_active_codes()
    print(f"=== Starting Auto-Redeem for {len(player_ids)} account(s) against {len(codes)} code(s) ===\n")
    
    successful_list = []
    unsuccessful_list = []

    for pid in player_ids:
        pname = get_player_name(pid)
        for code in codes:
            success, msg, err_code = redeem_code(pid, code)
            entry = f"[{pname}] (ID: {pid}) | Code: {code} -> {msg}"
            
            if success:
                successful_list.append(entry)
            else:
                unsuccessful_list.append(entry)

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
