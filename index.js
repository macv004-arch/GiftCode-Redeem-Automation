export default {
  async fetch(request, env, ctx) {
    const results = await runRedemptionLogic();
    return new Response(JSON.stringify(results, null, 2), {
      headers: { "Content-Type": "application/json" }
    });
  },

  async scheduled(event, env, ctx) {
    ctx.waitUntil(runRedemptionLogic());
  }
};

async function runRedemptionLogic() {
  // Replace or add your numeric player IDs here
  const playerIds = ["372774997"]; 
  const fallbackCodes = ["Hangul2026", "WELLDONE", "Kingshot888", "VIP777"];

  let codes = [...fallbackCodes];
  try {
    const res = await fetch("https://kingshot.net/api/cdk", {
      headers: { 
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, Gecko) Chrome/122.0.0.0 Safari/537.36" 
      }
    });
    if (res.ok) {
      const data = await res.json();
      if (data.codes && Array.isArray(data.codes)) {
        codes = [...new Set([...data.codes, ...fallbackCodes])];
      }
    }
  } catch (e) {}

  const results = [];

  for (const pid of playerIds) {
    let pname = `Player_${pid.slice(-4)}`;
    try {
      const nameRes = await fetch("https://ks-giftcode.centurygame.com/api/get_player", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ fid: pid })
      });
      const nameData = await nameRes.json();
      if (nameData.data && nameData.data.nickname) {
        pname = nameData.data.nickname;
      }
    } catch (e) {}

    for (const code of codes) {
      try {
        const res = await fetch("https://ks-giftcode.centurygame.com/api/gift_code", {
          method: "POST",
          headers: { "Content-Type": "application/x-www-form-urlencoded" },
          body: new URLSearchParams({ fid: pid, cdk: code })
        });
        const json = await res.json();
        results.push({
          player: pname,
          id: pid,
          code: code,
          msg: json.msg || "Unknown",
          err_code: json.err_code ?? -1
        });
      } catch (err) {
        results.push({
          player: pname,
          id: pid,
          code: code,
          msg: err.toString(),
          err_code: -1
        });
      }
    }
  }

  return results;
}
