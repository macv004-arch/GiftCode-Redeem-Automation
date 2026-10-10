import os
import requests

CLAIM_URL = "https://ks-giftcode.centurygame.com/api/gift_code"

def load_player_ids():
    filename = "playerIDs.txt"
    if not os.path.exists(filename):
        print(f"Error: {filename} not found!")
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip()]

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
        "fid": player_id,
        "cdk": code
    }
    try:
        response = requests.post(CLAIM_URL, data=payload, headers=headers, timeout=10)
        res_json = response.json()
        msg = res_json.get("msg", "Response received")
        print(f"Player {player_id} | Code: {code} -> {msg}")
    except Exception as e:
        print(f"Error redeeming {code} for {player_id}: {e}")

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No Player IDs found in playerIDs.txt.")
        return

    codes = get_active_codes()
    if not codes:
        print("No active codes retrieved.")
        return

    print(f"Processing {len(codes)} codes for {len(player_ids)} account(s)...")
    for pid in player_ids:
        for code in codes:
            redeem_code(pid, code)

if __name__ == "__main__":
    main()
