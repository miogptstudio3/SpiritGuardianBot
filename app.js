/* Spirit Guardian Web App v2.3 */
const tg = window.Telegram?.WebApp;
if (tg) {
  tg.ready();
  tg.expand();
  try {
    tg.setHeaderColor("#090b12");
    tg.setBackgroundColor("#090b12");
  } catch (_) {}
}

const $ = (id) => document.getElementById(id);
const headers = () => ({
  "X-Telegram-Init-Data": tg?.initData || "",
  "Content-Type": "application/json",
});

let me = null;

function haptic(type = "light") {
  try {
    if (type === "ok") tg?.HapticFeedback?.notificationOccurred("success");
    else if (type === "err") tg?.HapticFeedback?.notificationOccurred("error");
    else tg?.HapticFeedback?.impactOccurred("light");
  } catch (_) {}
}

function notice(text, isError = false) {
  const el = $("notice");
  el.textContent = text;
  el.classList.remove("hidden");
  el.style.borderColor = isError ? "#f87171" : "#252b3c";
  clearTimeout(el._t);
  el._t = setTimeout(() => el.classList.add("hidden"), 3200);
}

async function api(url, opt = {}) {
  opt.headers = { ...headers(), ...(opt.headers || {}) };
  const r = await fetch(url, opt);
  const text = await r.text();
  let data;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    data = { message: text };
  }
  if (!r.ok) {
    const msg = data.message || data.error || text || "خطا";
    throw new Error(typeof msg === "string" ? msg : "خطا در سرور");
  }
  return data;
}

/* ── Tabs ─────────────────────────────────────────── */
function showTab(id) {
  document.querySelectorAll(".tab").forEach((x) => x.classList.remove("active"));
  document.querySelectorAll(".tabs button").forEach((x) => x.classList.remove("active"));
  $(id)?.classList.add("active");
  document.querySelector(`[data-tab="${id}"]`)?.classList.add("active");
  haptic();
  if (id === "inventory") loadInventory();
  if (id === "shop") loadShop();
  if (id === "stories") loadStories();
  if (id === "demons") loadDemons();
  if (id === "rank") loadRank();
  if (id === "upgrade") renderUpgrade();
}

document.querySelectorAll(".tabs button").forEach((b) => {
  b.onclick = () => showTab(b.dataset.tab);
});

/* ── Profile ──────────────────────────────────────── */
async function loadMe() {
  me = await api("/api/me");
  $("playerName").textContent = me.name || "نگهبان";
  $("level").textContent = me.level;
  $("xp").textContent = me.xp;
  $("coins").textContent = me.coins;
  $("energy").textContent = me.energy;
  $("gems").textContent = me.soul_gems;
  $("light").textContent = me.light;
  $("mind").textContent = me.mind_power;
  $("body").textContent = me.body_power;
  $("spirit").textContent = me.spirit_power;
  $("training").textContent = me.training_points;
  $("spiritsSent").textContent = me.spirits_sent;
  $("cleanses").textContent = me.cleanses;
  $("health").textContent = `${me.health}/${me.max_health}`;
  $("coinBonus").textContent = `+${me.coin_bonus_pct}٪`;
  renderUpgrade();
}

async function loadFamily() {
  try {
    const f = await api("/api/family");
    const marriages = (f.marriages || []).filter((m) => m.status === "accepted");
    let text = "";
    if (marriages.length) {
      const m = marriages[0];
      const partner =
        m.user1_id === me?.user_id ? m.name2 : m.name1;
      text += `💑 همسر: ${partner}\n`;
    } else {
      text += "💍 وضعیت: مجرد\n";
    }
    text += `👶 فرزندان: ${(f.children || []).length}`;
    if (f.children?.length) {
      text +=
        "\n" +
        f.children
          .map(
            (c) =>
              `• ${c.name} | سن ${c.age} | 😊 ${c.happiness}%`
          )
          .join("\n");
    }
    $("familyText").textContent = text;
  } catch {
    $("familyText").textContent = "اطلاعات خانواده در دسترس نیست.";
  }
}

async function loadRegions() {
  try {
    const rows = await api("/api/regions");
    $("regionsList").innerHTML = rows
      .map(
        (r) =>
          `<span class="chip ${r.unlocked ? "" : "locked"}">${
            r.unlocked ? "🗺️" : "🔒"
          } ${r.name} <small>سطح ${r.unlock_level}</small></span>`
      )
      .join("");
  } catch {
    $("regionsList").innerHTML = "";
  }
}

/* ── Demons ───────────────────────────────────────── */
async function loadDemons() {
  try {
    const rows = await api("/api/demons");
    if (!rows.length) {
      $("demonsList").innerHTML =
        '<div class="empty">هنوز موجودی ثبت نشده.</div>';
      return;
    }
    $("demonsList").innerHTML = rows
      .map((d) => {
        const status = d.encounter_status;
        const statusTag =
          status === "completed"
            ? '<span class="tag ok">پاک‌سازی‌شده</span>'
            : status === "active"
            ? '<span class="tag warn">در حال پاک‌سازی</span>'
            : '<span class="tag">جدید</span>';
        const stars = "★".repeat(d.rank || 1);
        return `<article class="card item">
          <div class="meta">
            <h3>😈 ${d.name} ${statusTag}</h3>
            <p>
              <span class="tag rank">${stars}</span>
              <span class="tag">${d.region_name}</span>
              <span class="tag">${d.type}</span>
            </p>
            <p class="muted">☠️ آلودگی: ${d.encounter_corruption}٪ • ❤️ ${d.encounter_health} • 🪙 ${d.reward_coins} / XP ${d.reward_xp}</p>
            <p>${d.story || ""}</p>
          </div>
        </article>`;
      })
      .join("");
  } catch (e) {
    notice(e.message, true);
  }
}

/* ── Stories ──────────────────────────────────────── */
async function loadStories() {
  try {
    const rows = await api("/api/stories");
    if (!rows.length) {
      $("storyList").innerHTML =
        '<div class="empty">پرونده‌ای موجود نیست.</div>';
      return;
    }
    $("storyList").innerHTML = rows
      .map(
        (x) => `<article class="card">
        <h3>👻 ${x.name}</h3>
        <p>
          <span class="tag">${x.region_name}</span>
          <span class="tag rank">سختی ${x.difficulty}</span>
          <span class="tag">${x.type}</span>
        </p>
        <p>${x.story}</p>
        <p><b>درخواست:</b> ${x.request}</p>
        <p class="muted">🪙 ${x.reward_coins} • XP ${x.reward_xp}</p>
      </article>`
      )
      .join("");
  } catch (e) {
    notice(e.message, true);
  }
}

/* ── Shop & Inventory ─────────────────────────────── */
async function loadShop() {
  try {
    const rows = await api("/api/shop");
    $("shopList").innerHTML = rows
      .map(
        (x) => `<article class="card item">
        <div class="meta">
          <h3>${x.name}</h3>
          <p>${x.description}</p>
          <p class="muted">🪙 ${x.price_coins} • 🔮 ${x.price_gems}
            ${x.energy_gain ? ` • ⚡ +${x.energy_gain}` : ""}
            ${x.mission_bonus ? ` • ✨ +${x.mission_bonus}` : ""}
          </p>
        </div>
        <button onclick="buyItem(${x.id})">خرید</button>
      </article>`
      )
      .join("");
  } catch (e) {
    notice(e.message, true);
  }
}

async function buyItem(id) {
  try {
    const x = await api(`/api/shop/${id}/buy`, { method: "POST" });
    haptic("ok");
    notice(x.message);
    await Promise.all([loadMe(), loadInventory()]);
  } catch (e) {
    haptic("err");
    notice(e.message, true);
  }
}

async function loadInventory() {
  try {
    const rows = await api("/api/inventory");
    if (!rows.length) {
      $("inventoryList").innerHTML =
        '<div class="empty">کیف خالی است.</div>';
      return;
    }
    $("inventoryList").innerHTML = rows
      .map(
        (x) => `<article class="card item">
        <div class="meta">
          <h3>${x.name} <span class="tag">×${x.quantity}</span></h3>
          <p>${x.description}</p>
          <p class="muted">⚡ +${x.energy_gain} انرژی • ✨ +${x.mission_bonus} قدرت</p>
        </div>
        <button onclick="useItem(${x.item_id})">استفاده</button>
      </article>`
      )
      .join("");
  } catch (e) {
    notice(e.message, true);
  }
}

async function useItem(id) {
  try {
    const x = await api(`/api/inventory/${id}/use`, { method: "POST" });
    haptic("ok");
    notice(x.message);
    await Promise.all([loadMe(), loadInventory()]);
  } catch (e) {
    haptic("err");
    notice(e.message, true);
  }
}

/* ── Rank ─────────────────────────────────────────── */
async function loadRank() {
  try {
    const rows = await api("/api/rank");
    $("rankList").innerHTML = rows
      .map(
        (r, i) => `<article class="card rank-row">
        <div class="rank-num">${i + 1}</div>
        <div class="meta">
          <h3>${r.name}</h3>
          <p class="muted">سطح ${r.level} • 👻 ${r.spirits_sent} • 😈 ${r.cleanses}</p>
        </div>
      </article>`
      )
      .join("");
  } catch (e) {
    notice(e.message, true);
  }
}

/* ── Upgrade coins ────────────────────────────────── */
function renderUpgrade() {
  if (!me) return;
  const level = me.coin_boost || 0;
  const pct = me.coin_bonus_pct || 0;
  $("boostLevel").textContent = `${level}/10`;
  $("boostPct").textContent = `+${pct}٪`;
  if (level >= 10) {
    $("upgradeCost").textContent = "✅ به حداکثر سطح رسیده‌ای";
    $("upgradeBtn").disabled = true;
    $("upgradeBtn").textContent = "حداکثر سطح";
  } else {
    const costCoins = Math.floor(500 * Math.pow(1.6, level));
    const costGems = 2 + level;
    $("upgradeCost").innerHTML =
      `هزینه بعدی:<br>🪙 <b>${costCoins}</b> سکه + 🔮 <b>${costGems}</b> کریستال`;
    $("upgradeBtn").disabled = false;
    $("upgradeBtn").textContent = `⬆️ ارتقا به سطح ${level + 1}`;
  }
}

async function doUpgrade() {
  try {
    const x = await api("/api/upgrade_coins", { method: "POST" });
    haptic("ok");
    notice(x.message);
    await loadMe();
  } catch (e) {
    haptic("err");
    notice(e.message, true);
  }
}

/* ── Actions ──────────────────────────────────────── */
$("trainBtn").onclick = async () => {
  try {
    const x = await api("/api/train/mind", { method: "POST" });
    haptic("ok");
    notice(x.message);
    await loadMe();
  } catch (e) {
    haptic("err");
    notice(e.message, true);
  }
};

$("dailyBtn").onclick = async () => {
  try {
    const x = await api("/api/daily", { method: "POST" });
    haptic("ok");
    notice(x.message);
    await loadMe();
  } catch (e) {
    haptic("err");
    notice(e.message, true);
  }
};

$("upgradeBtn").onclick = doUpgrade;
$("refresh").onclick = () => init(true);
$("demonsRefresh").onclick = loadDemons;
$("storiesRefresh").onclick = loadStories;
$("invRefresh").onclick = loadInventory;

/* ── Boot ─────────────────────────────────────────── */
async function init(silent = false) {
  try {
    await loadMe();
    await Promise.all([loadFamily(), loadRegions()]);
    $("loader").classList.add("hidden");
    $("app").classList.remove("hidden");
    if (!silent) haptic("ok");
  } catch (e) {
    $("loader").innerHTML = `
      <div class="orb"></div>
      <p style="text-align:center;padding:0 20px;color:#f87171">
        ${e.message || "خطا"}<br><br>
        <small style="color:#9ca3b2">Web App را فقط از داخل ربات تلگرام باز کن.</small>
      </p>`;
  }
}

init();
