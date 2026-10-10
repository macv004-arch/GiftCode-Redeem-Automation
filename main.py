import os
import json
import time
import requests
from playwright.sync_api import sync_playwright

CLAIM_URL = "https://ks-giftcode.centurygame.com/"
SEEN_CODES_FILE = "seen_codes.json"
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

def load_seen_codes():
    if os.path.exists(SEEN_CODES_FILE):
        try:
            with open(SEEN_CODES_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []

def save_seen_codes(seen_list):
    try:
        with open(SEEN_CODES_FILE, "w") as f:
            json.dump(list(set(seen_list)), f, indent=2)
    except Exception:
        pass

def get_active_codes():
    fetched_codes = []
    try:
        res = requests.get("https://kingshot.net/api/cdk", headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            fetched_codes = data.get("codes", [])
    except Exception:
        pass

    return list(dict.fromkeys(fetched_codes + FALLBACK_CODES))

def main():
    player_ids = load_player_ids()
    if not player_ids:
        print("No valid numeric Player IDs found in playerIDs.txt.")
        return

    all_codes = get_active_codes()
    seen_codes = load_seen_codes()

    # Filter out codes that were already completely processed/claimed previously
    codes_to_test = [c for c in all_codes if c not in seen_codes]

    print(f"=== Starting Auto-Redeem Sweep ===")
    print(f"Accounts loaded: {len(player_ids)}")
    print(f"Total active codes found: {len(all_codes)}")
    print(f"Already processed/skipped codes ignored: {len(seen_codes)}")
    print(f"New codes to process this run: {len(codes_to_test)}\n")

    if not codes_to_test:
        print("No new codes to redeem. Everything is up to date!")
        return

    successful_list = []
    unsuccessful_list = []
    newly_seen = list(seen_codes)

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-infobars",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 720}
        )
        page = context.new_page()

        try:
            print("Navigating to portal...")
            page.goto(CLAIM_URL, wait_until="networkidle", timeout=60000)
            time.sleep(4)
        except Exception as e:
            print(f"Navigation warning: {e}")

        for pid in player_ids:
            pname = f"Player_{pid[-4:]}"
            try:
                # Fetch player nickname
                player_data = page.evaluate("""
                    async (fid) => {
                        try {
                            const res = await fetch('/api/get_player', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
                                body: new URLSearchParams({ fid })
                            });
                            const text = await res.text();
                            const data = JSON.parse(text);
                            return data.data ? data.data.nickname : null;
                        } catch (e) {
                            return null;
                        }
                    }
                """, str(pid))
                if player_data:
                    pname = player_data
            except Exception:
                pass

            print(f"\nProcessing Account: {pname} (ID: {pid})")

            for code in codes_to_test:
                try:
                    result = page.evaluate("""
                        async ([fid, cdk]) => {
                            try {
                                const response = await fetch('/api/gift_code', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'
                                    },
                                    body: new URLSearchParams({ fid, cdk })
                                });
                                const text = await response.text();
                                try {
                                    return JSON.parse(text);
                                } catch (e) {
                                    return { err_code: -999, msg: "Cloudflare HTML Block Intercepted" };
                                }
                            } catch (e) {
                                return { err_code: -1, msg: e.toString() };
                            }
                        }
                    """, [str(pid), str(code)])

                    msg = result.get("msg", "No response message")
                    err_code = result.get("err_code", -1)
                    code_val = result.get("code", -1)

                    is_success = (err_code == 0 or code_val == 0) and ("already" not in str(msg).lower())
                    entry = f"[{pname}] (ID: {pid}) | Code: {code} -> {msg}"

                    if is_success:
                        successful_list.append(entry)
                    else:
                        unsuccessful_list.append(entry)

                except Exception as e:
                    unsuccessful_list.append(f"[{pname}] (ID: {pid}) | Code: {code} -> Error: {e}")

                time.sleep(1.5)

        browser.close()

    # Mark tested codes as seen so they are skipped in future sweeps
    for c in codes_to_test:
        if c not in newly_seen:
            newly_seen.append(c)
    save_seen_codes(newly_seen)

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
