export default {
  async scheduled(event, env, ctx) {
    // Add your KingShot gift code redemption logic here
    console.log("KingShot redeemer cron triggered");
  },
  async fetch(request, env, ctx) {
    return new Response("KingShot Redeemer Worker is active!", { status: 200 });
  },
};
