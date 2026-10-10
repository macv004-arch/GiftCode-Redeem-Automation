import os
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"

def load_player_ids():
    filename = "playerIDs.txt"
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    
    player_ids = []
    with open(filename, "r") as f:
        for line in f:
            # Clean up whitespace, tabs, or quotes from each line
            clean_id = line.strip().strip('"\'')
            if clean_id and clean_id.isdigit():
                player_ids.append(clean_id)
    
    return player_ids

def get_active_codes():
    try:
        res = requests.get("https://kingshot.net/api/cdk", timeout=10)
        if res.status_code == 200:
            data = res.json()
            return data.get("codes", [])
    except Exception as e:
        print(f"Failed to fetch codes: {e}")
    return []

def redeem_code(player_id, code):
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
        print(f"Player {player_id} | Code: {code} -> Status: {msg} (Code: {err_code})")
    except Exception as e:
        print(f"Error redeeming {code} for {player_id}: {e}")

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No valid numeric Player IDs found in playerIDs.txt.")
        return

    codes = get_active_codes()
    if not codes:
        print("No active codes retrieved from kingshot.net.")
        return

    print(f"Found {len(codes)} code(s) to process for {len(player_ids)} player account(s)...")
    for pid in player_ids:
        for code in codes:
            redeem_code(pid, code)

if __name__ == "__main__":
    main()
