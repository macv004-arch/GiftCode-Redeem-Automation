import os
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"
PLAYER_INFO_URL = "https://ks-giftcode.centurygame.com/api/get_player"

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
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {"fid": str(player_id)}
    try:
        response = requests.post(PLAYER_INFO_URL, data=payload, headers=headers, timeout=10)
        res_json = response.json()
        if res_json.get("code") == 0 and "data" in res_json:
            return res_json["data"].get("nickname", "Unknown Player")
    except Exception:
        pass
    return "Unknown Player"

def get_active_codes():
    try:
        res = requests.get("https://kingshot.net/api/cdk", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("codes", [])
    except Exception as e:
        print(f"Failed to fetch codes: {e}")
    return []

def redeem_code(player_id, player_name, code):
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "fid": str(player_id),
        "cdk": str(code)
    }
    try:
        response = requests.post(CLAIM_URL, data=payload, headers=headers, timeout=10)
        res_json = response.json()
        msg = res_json.get("msg", "Response received")
        err_code = res_json.get("err_code", -1)
        
        # Consider code 0 or messages with "SUCCESS" as successful redemptions
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
    if not codes:
        print("No active codes retrieved from kingshot.net.")
        return

    print(f"Processing {len(codes)} code(s) for {len(player_ids)} player account(s)...\n")
    
    successful_list = []
    unsuccessful_list = []

    for pid in player_ids:
        pname = get_player_name(pid)
        for code in codes:
            success, msg, err_code = redeem_code(pid, pname, code)
            entry = f"[{pname}] (ID: {pid}) | Code: {code} -> {msg}"
            
            if success:
                successful_list.append(entry)
            else:
                unsuccessful_list.append(entry)

    # --- Print Structured Summary ---
    print("=" * 60)
    print(" SUCCESSFUL REDEMPTIONS ")
    print("=" * 60)
    if successful_list:
        for item in successful_list:
            print(f" SUCCESS: {item}")
    else:
        print("None (All codes were either previously claimed or invalid)")

    print("\n" + "=" * 60)
    print(" NOT REDEEMED / FAILED / ALREADY CLAIMED ")
    print("=" * 60)
    if unsuccessful_list:
        for item in unsuccessful_list:
            print(f" SKIPPED/FAILED: {item}")
    else:
        print("None")
    print("=" * 60)

if __name__ == "__main__":
    main()
