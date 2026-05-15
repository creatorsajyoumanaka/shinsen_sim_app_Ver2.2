import json
import random
import re
from copy import deepcopy
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="信長真戦 編成シュミレーター Ver3.9", layout="wide")

APP_TITLE = "信長真戦 編成シュミレーター Ver3.9"
CREATOR = "沙条愛歌"
DATA_DIR = Path(__file__).resolve().parent / "data"

STATUS_NAMES = [
    "連撃", "封撃", "火傷", "水攻め", "中毒", "消沈", "潰走", "浄化", "奇策", "破陣", "会心", "発動確率",
    "乱舞", "無策", "麻痺", "疲弊", "混乱", "奇策ダメージ", "鉄壁", "挑発", "牽制", "会心ダメージ率",
    "心攻", "肩代わり", "離反", "威圧", "先攻", "心中", "耐性", "恐慌", "洞察", "回避", "反撃", "援護",
    "錯乱", "休養", "回復不可", "同気連枝対象",
]
CONTROL_STATUSES = {"封撃", "無策", "麻痺", "疲弊", "混乱", "威圧", "挑発", "牽制"}
DOT_STATUSES = {"火傷", "水攻め", "中毒", "消沈", "潰走", "恐慌", "錯乱"}

@st.cache_data
def load_json_candidates(names):
    for name in names:
        path = DATA_DIR / name
        if path.exists():
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return list(data.values()) if isinstance(data, dict) else data
    return []

GENERALS = load_json_candidates(["generals_master.json", "generals.json", "units.json"])
SKILLS_RAW = load_json_candidates(["skills_master.json", "skills.json", "unique_skills_master.json", "skill_master.json"])
TRAITS_RAW = load_json_candidates(["traits_master.json", "limit_breaks.json"])

def parse_percent(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) / 100 if float(v) > 1 else float(v)
    s = str(v)
    m = re.search(r"(\d+(?:\.\d+)?)\s*%", s)
    if m:
        return float(m.group(1)) / 100
    try:
        f = float(s)
        return f / 100 if f > 1 else f
    except Exception:
        return None

def parse_proc_from_text(text):
    m = re.search(r"発動確率[】\s]*(\d+(?:\.\d+)?)\s*%", text or "")
    return float(m.group(1)) / 100 if m else None


# ============================================================
# Ver3.9: 戦法分類・ログ・兵種戦法 安全補助
# ============================================================

TROOP_SKILL_TYPES = {"兵種", "兵種戦法", "兵種進化"}

TROOP_SKILL_REQUIRED_TYPE = {
    "大太刀": "足軽",
    "大太刀力士隊": "足軽",
    "三河弓": "弓兵",
    "三河弓兵隊": "弓兵",
    "赤備え隊": "騎兵",
    "甲斐赤備": "騎兵",
    "甲斐弓": "弓兵",
    "母衣武者": "騎兵",
    "薩摩鉄砲兵": "鉄砲",
    "鉄砲僧兵": "鉄砲",
    "僧兵": "足軽",
}

NON_DAMAGE_ASSAULT = {"罵詈雑言"}

OPENING_SKILL_TYPES = {"指揮", "受動", "兵種", "兵種戦法", "兵種進化"}

ACTIVE_SKILL_TYPES = {"能動"}

ASSAULT_SKILL_TYPES = {"突撃"}

def normalize_skill_type(skill):
    """Excel/JSONの表記揺れを吸収して、戦法タイプを返す。"""
    if not isinstance(skill, dict):
        return "能動"
    raw_type = skill.get("skill_type") or skill.get("type") or skill.get("戦法タイプ") or ""
    text = " ".join(str(skill.get(k, "")) for k in ("effect", "detail", "description", "戦法詳細", "text"))
    joined = f"{raw_type} {text}"

    if "【戦法詳細】 兵種" in joined or raw_type in TROOP_SKILL_TYPES:
        return "兵種"
    if "【戦法詳細】 指揮" in joined or raw_type == "指揮":
        return "指揮"
    if "【戦法詳細】 受動" in joined or raw_type == "受動":
        return "受動"
    if "【戦法詳細】 突撃" in joined or raw_type == "突撃":
        return "突撃"
    if "【戦法詳細】 能動" in joined or raw_type == "能動":
        return "能動"

    # 重要：本文中の「突撃戦法」は効果説明の場合があるので、先頭の詳細表記がない限り優先しない
    if joined.strip().startswith("兵種"):
        return "兵種"
    if joined.strip().startswith("指揮"):
        return "指揮"
    if joined.strip().startswith("受動"):
        return "受動"
    if joined.strip().startswith("突撃"):
        return "突撃"
    if joined.strip().startswith("能動"):
        return "能動"
    return "能動"

def skill_name(skill):
    if isinstance(skill, dict):
        return skill.get("name") or skill.get("戦法名") or skill.get("skill_name") or "不明戦法"
    return str(skill)

def skill_proc(skill, default=1.0):
    if not isinstance(skill, dict):
        return default
    val = skill.get("proc", skill.get("rate", skill.get("発動確率", default)))
    try:
        if isinstance(val, str):
            val = val.replace("%", "").replace("％", "").strip()
            num = float(val)
            return num / 100 if num > 1 else num
        num = float(val)
        return num / 100 if num > 1 else num
    except Exception:
        return default

def log_line_safe(log, text):
    if hasattr(log, "line"):
        log.line(text)
    elif hasattr(log, "event"):
        log.event("", "", text)

def log_battle_header(log, title):
    if hasattr(log, "h"):
        log.h(title)
    else:
        log_line_safe(log, f"━━━━━━━━━━━━\n{title}\n━━━━━━━━━━━━")

def true_battle_damage_line(target, source, skill, damage):
    remain = target.get("troops", target.get("兵力", 0)) if isinstance(target, dict) else 0
    tn = target.get("name", "対象") if isinstance(target, dict) else str(target)
    sn = source.get("name", "発動者") if isinstance(source, dict) else str(source)
    return f"［{tn}］は［{sn}］の「{skill}」により、兵力{damage}（残兵{remain}）損失"

def true_battle_heal_line(target, source, skill, amount):
    remain = target.get("troops", target.get("兵力", 0)) if isinstance(target, dict) else 0
    tn = target.get("name", "対象") if isinstance(target, dict) else str(target)
    return f"［{tn}］は「{skill}」により、兵力{amount}（残兵{remain}）回復"

def true_battle_status_line(target, source, skill, status, turns=1):
    tn = target.get("name", "対象") if isinstance(target, dict) else str(target)
    sn = source.get("name", "発動者") if isinstance(source, dict) else str(source)
    return f"［{tn}］は［{sn}］の「{skill}」により、{status}状態になる（{turns}T）"

def list_unit_skills_debug(units, log, enabled=False):
    """戦法が出てこない時の確認用。通常はFalse。"""
    if not enabled:
        return
    log_battle_header(log, "DEBUG：所持戦法確認")
    for unit in units:
        names = []
        for s in unit.get("skills", []):
            names.append(f"{skill_name(s)} / {normalize_skill_type(s)} / {skill_proc(s):.0%}")
        log_line_safe(log, f"【{unit.get('name','不明')}】" + " / ".join(names))


def infer_skill_type(text):
    text = text or ""

    if "【戦法詳細】 兵種" in text:
        return "兵種"
    if "【戦法詳細】 指揮" in text:
        return "指揮"
    if "【戦法詳細】 受動" in text:
        return "受動"
    if "【戦法詳細】 突撃" in text:
        return "突撃"
    if "【戦法詳細】 能動" in text:
        return "能動"

    head = text.strip()[:40]
    if head.startswith("兵種"):
        return "兵種"
    if head.startswith("指揮"):
        return "指揮"
    if head.startswith("受動"):
        return "受動"
    if head.startswith("突撃"):
        return "突撃"
    if head.startswith("能動"):
        return "能動"

    return "能動"

def infer_target_info(effect_text, explicit_target=""):
    t = (explicit_target or "") + " " + (effect_text or "")
    side = "enemy"
    if any(x in t for x in ["自軍", "友軍", "自身", "自分"]):
        side = "ally"
    if "敵軍" in t:
        side = "enemy"
    if any(x in t for x in ["自身", "自分"]):
        scope, lo, hi = "self", 1, 1
    elif "全体" in t or "3名" in t:
        scope, lo, hi = "all", 3, 3
    elif "複数" in t:
        scope = "multi"
        m = re.search(r"(\d+)\s*[～〜\-]\s*(\d+)\s*名", t)
        if m:
            lo, hi = int(m.group(1)), int(m.group(2))
        else:
            m2 = re.search(r"複数（\s*(\d+)\s*名", t)
            lo = hi = int(m2.group(1)) if m2 else 2
    else:
        scope, lo, hi = "single", 1, 1
    if "大将" in t:
        priority = "commander"
    elif "兵力が最も少ない" in t or "兵力の最も低い" in t:
        priority = "lowest_hp"
    elif "武勇が最も高い" in t:
        priority = "highest_str"
    elif "知略が最も高い" in t:
        priority = "highest_int"
    elif "速度が最も高い" in t:
        priority = "highest_spd"
    else:
        priority = "random"
    return {"side": side, "scope": scope, "count_min": lo, "count_max": hi, "priority": priority, "raw": explicit_target or "", "inferred": not bool(explicit_target) or "未判明" in str(explicit_target)}

def extract_rates(text, keyword):
    return [float(m.group(1)) / 100 for m in re.finditer(rf"{keyword}\s*(\d+(?:\.\d+)?)\s*%", text or "")]

def build_sim_from_text(text, target_info):
    text = text or ""
    statuses = [x for x in STATUS_NAMES if x in text]
    dtype = "physical"
    if "兵刃" in text and "計略" in text:
        dtype = "hybrid"
    elif "計略" in text:
        dtype = "strategy"
    damage_rates = extract_rates(text, "ダメージ率")
    heal_rates = extract_rates(text, "回復率")
    if not damage_rates:
        damage_rates = [float(m.group(1)) / 100 for m in re.finditer(r"(\d+(?:\.\d+)?)\s*%\s*の?(?:兵刃|計略)?ダメージ", text)]
    m = re.search(r"(\d+)\s*ターン", text)
    duration = int(m.group(1)) if m else 1
    prepare = 2 if "2ターンの準備" in text else (1 if "1ターンの準備" in text else 0)
    return {"damage_type": dtype, "damage_rates": damage_rates, "heal_rates": heal_rates, "statuses": statuses, "duration": duration, "prepare_turn": prepare, "target": target_info}

def normalize_skill(raw):
    if not isinstance(raw, dict):
        return {}
    name = raw.get("name") or raw.get("skill_name") or "名称不明"
    effect = raw.get("effect") or raw.get("effects_text") or raw.get("戦法詳細") or raw.get("detail") or ""
    proc = parse_percent(raw.get("proc", raw.get("rate", raw.get("発動確率", None))))
    if proc is None:
        proc = parse_proc_from_text(effect)
    target_text = raw.get("target") or raw.get("対象種別") or raw.get("target_type") or ""
    target_info = infer_target_info(effect, target_text)
    return {**raw, "skill_id": raw.get("skill_id") or raw.get("id") or name, "name": name, "proc": proc if proc is not None else 0.35, "effect": effect, "skill_type": raw.get("type") or raw.get("skill_type") or infer_skill_type(effect), "target_info": target_info, "sim": build_sim_from_text(effect, target_info)}

SKILLS = [normalize_skill(s) for s in SKILLS_RAW]
SKILL_BY_ID = {s.get("skill_id"): s for s in SKILLS if s.get("skill_id")}
SKILL_BY_NAME = {s.get("name"): s for s in SKILLS if s.get("name")}

def normalize_traits(raw):
    if isinstance(raw, dict):
        return raw
    out = {}
    for item in raw or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name") or item.get("unit_id")
        effects = item.get("effects") or item.get("traits") or []
        if name:
            out[name] = effects
    return out

TRAITS_BY_NAME = normalize_traits(TRAITS_RAW)


def stat_label(k):
    return {"str":"武勇", "int":"知略", "lea":"統率", "spd":"速度", "pol":"政務", "cha":"魅力"}.get(k, k)

def get_stats(g):
    stats = deepcopy(g.get("base_stats", {})) if g else {}
    for k in ["str", "int", "lea", "spd"]:
        stats.setdefault(k, 100)
    return stats

def get_unique_skill(g):
    if not g:
        return None
    uid = g.get("unique_skill_id")
    if uid and uid in SKILL_BY_ID:
        return SKILL_BY_ID[uid]
    if isinstance(uid, str) and uid.startswith("UNQ_"):
        return SKILL_BY_NAME.get(uid.replace("UNQ_", ""))
    return None

def format_stats(stats):
    return " / ".join(f"{stat_label(k)} {v}" for k, v in stats.items())


class BattleLogger:
    def __init__(self):
        self.sections = []
        self.current = None

    def h(self, text):
        self.current = {"title": text, "lines": []}
        self.sections.append(self.current)

    def line(self, text=""):
        if self.current is None:
            self.h("合戦開始")
        self.current["lines"].append(str(text))

    def info(self, text):
        self.line(f"・{text}")

    def unit(self, name):
        self.line(f"【{name}】")

    def event(self, icon, actor, text):
        self.line(f"{icon}［{actor}］{text}")

    def damage_detail(self, target, source, skill, value):
        self.line(f"🔴［{target['name']}］は［{source['name']}］の『{skill}』により、兵力{value}（残兵{target['troops']}）損失")

    def heal_detail(self, target, source, skill, value):
        self.line(f"🟢［{target['name']}］は［{source['name']}］の『{skill}』により、兵力{value}（残兵{target['troops']}）回復")

    def status_detail(self, target, source, skill, status, turns):
        self.line(f"🟣［{target['name']}］は［{source['name']}］の『{skill}』により、{status}状態になる（{turns}T）")

    def damage(self, actor, target, value, kind="兵刃"):
        # 互換用。なるべく receive_damage の詳細ログを使う。
        self.line(f"🔴［{target}］は［{actor}］の『{kind}』により、兵力{value}損失")

    def heal(self, actor, target, value):
        self.line(f"🟢［{target}］は［{actor}］により、兵力{value}回復")

    def status(self, actor, target, status, turns):
        self.line(f"🟣［{target}］は［{actor}］により、{status}状態になる（{turns}T）")

    def buff(self, actor, target, text):
        self.line(f"🔵［{target}］は［{actor}］により、{text}")

    def text(self):
        out = []
        for sec in self.sections:
            out += ["━━━━━━━━━━━━━━━━", f"■ {sec['title']}", "━━━━━━━━━━━━━━━━"]
            out += sec["lines"] + [""]
        return "\n".join(out).strip()

def make_unit(slot, raw, troops, limit_break, manual_bonus, skills):
    stats = get_stats(raw)
    for k, v in manual_bonus.items():
        stats[k] = stats.get(k, 0) + v
    unique = get_unique_skill(raw)
    final_skills = []
    if unique:
        final_skills.append({**unique, "_is_unique": True})
    final_skills += [s for s in skills if s]
    return {"slot": slot, "name": raw.get("name", slot) if raw else slot, "raw": raw or {}, "stats": stats, "troops": int(troops), "max_troops": int(troops), "limit_break": limit_break, "skills": final_skills, "statuses": {}, "alive": True, "side": None, "crit_rate":0.0, "crit_damage_bonus":0.0, "strategy_crit_rate":0.0, "strategy_crit_damage_bonus":0.0, "physical_damage_bonus":0.0, "strategy_damage_bonus":0.0, "damage_taken_bonus":0.0, "damage_reduce":0.0, "proc_bonus":0.0, "unique_proc_bonus":0.0}

def has_status(u, s): return s in u.get("statuses", {}) and u["statuses"][s].get("turns", 0) > 0

def add_status(u, s, turns=1, value=None, rate=None, source=None, log=None):
    if s in CONTROL_STATUSES and has_status(u, "洞察"):
        if log: log.event("🛡️", u["name"], f"洞察により {s} 無効")
        return False
    u["statuses"][s] = {"turns": turns, "value": value, "rate": rate, "source": source}
    return True

def remove_status(u, s): u.get("statuses", {}).pop(s, None)

def tick_statuses(u):
    expired = []
    for name, data in list(u.get("statuses", {}).items()):
        data["turns"] -= 1
        if data["turns"] <= 0: expired.append(name)
    for name in expired: u["statuses"].pop(name, None)
    return expired

def living(side): return [u for u in side if u["troops"] > 0]
def total_troops(side): return sum(max(0, u["troops"]) for u in side)

def choose_targets(actor, allies, enemies, target_info):
    pool = living(allies if target_info.get("side") == "ally" else enemies)
    if target_info.get("scope") == "self": return [actor]
    if not pool: return []
    pr = target_info.get("priority", "random")
    if pr == "commander": return [pool[0]]
    if pr == "lowest_hp": return [min(pool, key=lambda u:u["troops"])]
    if pr == "highest_str": return [max(pool, key=lambda u:u["stats"].get("str", 0))]
    if pr == "highest_int": return [max(pool, key=lambda u:u["stats"].get("int", 0))]
    if pr == "highest_spd": return [max(pool, key=lambda u:u["stats"].get("spd", 0))]
    hi = min(len(pool), target_info.get("count_max", 1)); lo = min(len(pool), target_info.get("count_min", hi))
    return random.sample(pool, random.randint(lo, hi) if hi >= lo else 1)

def base_damage(actor, target, rate, dtype, base):
    if dtype == "strategy": atk, defense, kind = actor["stats"].get("int",100), target["stats"].get("int",100), "計略"
    elif dtype == "hybrid": atk, defense, kind = max(actor["stats"].get("str",100), actor["stats"].get("int",100)), max(target["stats"].get("lea",100), target["stats"].get("int",100)), "複合"
    else: atk, defense, kind = actor["stats"].get("str",100), target["stats"].get("lea",100), "兵刃"
    stat_ratio = max(0.45, min(1.8, atk / max(1, defense)))
    troop_factor = max(0.35, actor["troops"] / max(1, actor["max_troops"]))
    dmg = int(base * rate * stat_ratio * troop_factor)
    if dtype == "strategy": dmg = int(dmg * (1 + actor.get("strategy_damage_bonus",0)))
    elif dtype == "physical": dmg = int(dmg * (1 + actor.get("physical_damage_bonus",0)))
    dmg = int(dmg * (1 + target.get("damage_taken_bonus",0)) * (1 - target.get("damage_reduce",0)))
    return max(1, dmg), kind

def apply_crit(actor, dmg, dtype, log, crit_base_bonus=0.50):
    if dtype == "strategy": rate, extra, name = actor.get("strategy_crit_rate",0), actor.get("strategy_crit_damage_bonus",0), "奇策"
    else: rate, extra, name = actor.get("crit_rate",0), actor.get("crit_damage_bonus",0), "会心"
    if rate > 0 and random.random() < rate:
        new = int(dmg * (1 + crit_base_bonus + extra))
        log.event("💥", actor["name"], f"{name}発動：{dmg} → {new}（+{int((crit_base_bonus+extra)*100)}%）")
        return new
    return dmg


def heal(actor, target, amount, log, heal_rate, reason="回復"):
    if has_status(target, "回復不可"):
        log.event("🚫", target["name"], f"回復不可により『{reason}』失敗")
        return 0
    amount = int(amount * heal_rate)
    before = target["troops"]
    target["troops"] = min(target["max_troops"], target["troops"] + max(0, amount))
    healed = target["troops"] - before
    if healed > 0:
        log.heal_detail(target, actor, reason, healed)
    return healed

# ============================================================
# 兵種戦法：開戦時適用＋条件トリガー
# ============================================================


# ダメージを伴わない突撃/反応系戦法。発動ログは出しても自動ダメージは出さない。
NON_DAMAGE_ASSAULT_SKILLS = {
    "罵詈雑言",
    "機に乗ず",
}

TROOP_SKILL_TYPES = {"兵種", "兵種戦法", "兵種進化"}

TROOP_SKILL_REQUIRED_TYPE = {
    "母衣武者": "騎兵",
    "甲斐弓騎兵": "弓兵",
    "甲斐弓": "弓兵",
    "赤備え隊": "騎兵",
    "赤備": "騎兵",
    "三河弓兵隊": "弓兵",
    "三河弓": "弓兵",
    "薩摩鉄砲兵": "鉄砲",
    "鉄砲僧兵": "鉄砲",
    "大太刀力士隊": "足軽",
    "大太刀": "足軽",
    "僧兵": "足軽",
}

def is_troop_skill(skill):
    return skill.get("skill_type") in TROOP_SKILL_TYPES or "【戦法詳細】 兵種" in skill.get("effect", "")

def required_troop_type(skill):
    name = skill.get("name", "")
    if name in TROOP_SKILL_REQUIRED_TYPE:
        return TROOP_SKILL_REQUIRED_TYPE[name]
    text = skill.get("effect", "")
    for tp in ["騎兵", "弓兵", "足軽", "鉄砲"]:
        if f"{tp}が" in text or f"【適性兵種】 {tp}" in text:
            return tp
    return None


def apply_troop_skills(side_units, troop_type, log, label):
    """兵種戦法は毎ターン発動判定しない。合戦開始で兵種一致時だけ効果フラグを付与する。"""
    applied = set()
    for owner in side_units:
        for sk in owner.get("skills", []):
            if not is_troop_skill(sk):
                continue
            name = sk.get("name", "")
            req = required_troop_type(sk)
            if req and req != troop_type:
                log.event("🚫", owner["name"], f"兵種戦法『{name}』無効：必要兵種 {req} / 現在 {troop_type}")
                continue
            if (owner["name"], name) in applied:
                continue
            applied.add((owner["name"], name))

            log.unit(owner["name"])
            log.line(f"🛡️ 兵種戦法『{name}』発動")

            if name in {"大太刀", "大太刀力士隊"}:
                for u in side_units:
                    u["otachi_counter_rate"] = max(u.get("otachi_counter_rate", 0), 0.30)
                    u["otachi_counter_damage_rate"] = max(u.get("otachi_counter_damage_rate", 0), 1.00)
                    u["normal_assault_reduce_until_turn"] = max(u.get("normal_assault_reduce_until_turn", 0), 2)
                    u["normal_assault_reduce_rate"] = max(u.get("normal_assault_reduce_rate", 0), 0.18)
                log.line("↩️ 反撃 効果付与済み")
                log.line("🛡️ 通常攻撃・突撃被ダメージ低下 効果付与済み")

            elif name in {"三河弓", "三河弓兵隊"}:
                for u in side_units:
                    u["stats"]["lea"] = u["stats"].get("lea", 0) + 20
                    u["mikawa_heal_until_turn"] = max(u.get("mikawa_heal_until_turn", 0), 3)
                    u["mikawa_heal_rate"] = max(u.get("mikawa_heal_rate", 0), 0.35)
                    u["mikawa_heal_power"] = max(u.get("mikawa_heal_power", 0), 0.65)
                log.line("⬆️ 統率+20")
                log.line("💚 回生 効果付与済み")

            elif name in {"赤備え", "赤備え隊", "甲斐赤備"}:
                for u in side_units:
                    u["crit_rate"] += 0.35
                log.line("🟡 会心率+35% 効果付与済み")

            elif name in {"甲斐弓", "甲斐弓騎兵"}:
                if side_units:
                    side_units[0]["proc_bonus"] += 0.08
                log.line("🎯 配置1番目の能動戦法発動率+8%")

            elif name == "母衣武者":
                for u in side_units:
                    u["stats"]["spd"] = u["stats"].get("spd", 0) + 20
                    u["horo_musha"] = True
                log.line("🐎 自軍全体 速度+20")

            elif name == "薩摩鉄砲兵":
                for u in side_units:
                    u["satsuma_gun"] = True
                    u["strategy_damage_bonus"] += 0.40
                log.line("🔫 計略与ダメージ+40% 効果付与済み")

            elif name == "鉄砲僧兵":
                for u in side_units:
                    u["stats"]["lea"] += 12
                    u["stats"]["int"] += 12
                    u["teppo_sohei_rest"] = True
                log.line("🙏 統率+12 / 知略+12 / 休養予約")

            elif name == "僧兵":
                for u in side_units:
                    u["damage_reduce"] += 0.20
                log.line("🛡️ 兵刃被ダメージ20%低下 効果付与済み")

def process_troop_turn_effects(side_units, troop_type, turn, log, cfg, label):
    # 鉄砲僧兵：1/2/5/6ターン目に休養付与
    if turn in {1, 2, 5, 6}:
        for u in side_units:
            if u.get("teppo_sohei_rest"):
                add_status(u, "休養", 1, value=0.44, source=u, log=log)
                log.event("🙏", u["name"], "鉄砲僧兵：休養付与（1T）")


def receive_damage(actor, target, dmg, dtype, kind, log, cfg, skill_name=None):
    if target["troops"] <= 0:
        return 0
    turn = cfg.get("_turn", 0)
    skill_name = skill_name or cfg.get("_skill_name") or kind or "通常攻撃"

    # 兵種戦法：大太刀などの通常/突撃被ダメ軽減
    if dtype in {"normal", "assault"} and turn <= target.get("normal_assault_reduce_until_turn", 0):
        reduce_rate = target.get("normal_assault_reduce_rate", 0)
        if reduce_rate > 0:
            before_dmg = int(dmg)
            dmg = int(dmg * (1 - reduce_rate))
            log.event("🛡️", target["name"], f"兵種戦法軽減：{before_dmg} → {dmg}")

    if has_status(target, "鉄壁") and not has_status(actor, "心中"):
        remove_status(target, "鉄壁")
        log.event("🛡️", target["name"], "鉄壁でダメージ無効")
        return 0

    if has_status(target, "回避") and not has_status(actor, "心中"):
        ev = target["statuses"]["回避"].get("value") or 0.35
        if random.random() < ev:
            log.event("💨", target["name"], f"回避成功（{int(ev*100)}%）")
            return 0

    if has_status(actor, "疲弊"):
        log.event("🟣", actor["name"], "疲弊により与ダメージ無効")
        return 0

    loss = min(target["troops"], max(0, int(dmg)))
    target["troops"] -= loss
    if target["troops"] <= 0:
        target["alive"] = False

    log.damage_detail(target, actor, skill_name, loss)

    if dtype == "physical" and has_status(actor, "離反"):
        heal(actor, actor, int(loss * (actor["statuses"]["離反"].get("value") or 0.15)), log, cfg["heal_damage_rate"], "離反")
    if dtype == "strategy" and has_status(actor, "心攻"):
        heal(actor, actor, int(loss * (actor["statuses"]["心攻"].get("value") or 0.15)), log, cfg["heal_damage_rate"], "心攻")

    # 三河弓：被ダメ時回復（3Tまで）
    if loss > 0 and turn <= target.get("mikawa_heal_until_turn", 0) and random.random() < target.get("mikawa_heal_rate", 0):
        amount = int(cfg["heal_base"] * target.get("mikawa_heal_power", 0.65) * max(0.6, target["stats"].get("lea", 100) / 150))
        heal(target, target, amount, log, cfg["heal_damage_rate"], "三河弓兵隊")

    # 大太刀：通常攻撃被弾時反撃。反撃ループ防止。
    if loss > 0 and dtype == "normal" and not cfg.get("_countering", False):
        rate = target.get("otachi_counter_rate", 0)
        if rate > 0 and random.random() < rate and actor.get("troops", 0) > 0:
            cfg["_countering"] = True
            counter_rate = target.get("otachi_counter_damage_rate", 1.0)
            cdmg, ckind = base_damage(target, actor, counter_rate, "physical", cfg["normal_damage_base"])
            log.event("↩️", target["name"], f"大太刀反撃：{actor['name']}へ反撃")
            receive_damage(target, actor, cdmg, "counter", "反撃", log, cfg, skill_name="大太刀反撃")
            if target.get("name") == "真柄直隆" and random.random() < 0.25 and actor.get("troops", 0) > 0:
                edmg, _ = base_damage(target, actor, 1.20, "physical", cfg["damage_base"])
                log.event("⚔️", target["name"], "真柄直隆：大太刀追加兵刃")
                receive_damage(target, actor, edmg, "counter", "追加兵刃", log, cfg, skill_name="大太刀追加兵刃")
            cfg["_countering"] = False
    return loss

def process_dot(u, log, cfg):
    for s in list(u.get("statuses", {}).keys()):
        if s not in DOT_STATUSES: continue
        data = u["statuses"][s]; rate = data.get("rate") or (0.72 if s == "潰走" else 0.74); src = data.get("source")
        src_stat = src["stats"].get("str" if s == "潰走" else "int", 100) if src else 120
        defense = u["stats"].get("lea" if s == "潰走" else "int", 100)
        dmg = int(cfg["dot_base"] * rate * max(0.45, min(1.8, src_stat / max(1, defense))))
        u["troops"] = max(0, u["troops"] - dmg); log.event("🔥", u["name"], f"{s} 持続ダメージ {dmg}")

def process_rest(u, log, cfg):
    if has_status(u, "休養"):
        rate = u["statuses"]["休養"].get("value") or 0.76
        amount = int(cfg["heal_base"] * rate * max(0.6, u["stats"].get("int",100) / 150))
        heal(u, u, amount, log, cfg["heal_damage_rate"], "休養")

def get_action_order(a,b): return sorted(living(a)+living(b), key=lambda u:(10000 if has_status(u,"先攻") else 0)+u["stats"].get("spd",0), reverse=True)

def try_active_skill(actor, allies, enemies, skill, log, cfg):
    if skill.get("skill_type") != "能動": return False
    if has_status(actor, "無策"): log.event("🟣", actor["name"], f"無策により「{skill['name']}」不可"); return False
    proc = min(1.0, skill.get("proc",0.35) + actor.get("proc_bonus",0) + (actor.get("unique_proc_bonus",0) if skill.get("_is_unique") else 0))
    log.event("🎲", actor["name"], f"「{skill['name']}」発動判定 {int(proc*100)}%")
    if random.random() > proc: log.event("…", actor["name"], f"「{skill['name']}」不発"); return False
    log.event("✨", actor["name"], f"能動戦法「{skill['name']}」発動")
    sim = skill.get("sim", {})
    if sim.get("prepare_turn",0) > 0: log.event("⏳", actor["name"], "準備戦法：Previewでは即時処理")
    targets = choose_targets(actor, allies, enemies, sim.get("target", {"side":"enemy","scope":"single","count_min":1,"count_max":1}))
    for rate in sim.get("damage_rates", []):
        for t in targets:
            dmg, kind = base_damage(actor, t, rate, sim.get("damage_type","physical"), cfg["damage_base"])
            dmg = apply_crit(actor, dmg, sim.get("damage_type","physical"), log, cfg["crit_base_bonus"])
            receive_damage(actor, t, dmg, sim.get("damage_type","physical"), kind, log, cfg, skill_name=skill["name"])
    if sim.get("heal_rates"):
        heal_targets = targets if sim.get("target",{}).get("side") == "ally" else random.sample(living(allies), min(len(living(allies)), max(1,len(targets))))
        for rate in sim.get("heal_rates", []):
            for t in heal_targets:
                amount = int(cfg["heal_base"] * rate * max(0.6, actor["stats"].get("int",100)/150))
                heal(actor, t, amount, log, cfg["heal_damage_rate"], skill["name"])
    for s in sim.get("statuses", []):
        if s in {"発動確率", "浄化", "奇策ダメージ", "会心ダメージ率"}: continue
        if s in {"会心","奇策","連撃","先攻","洞察","破陣","心攻","離反","鉄壁","回避","反撃","休養"}:
            buff_targets = targets if sim.get("target",{}).get("side") == "ally" else [actor]
            for t in buff_targets:
                value = None; rate = None
                if s == "会心": value = 0.45; t["crit_rate"] += value
                elif s == "奇策": value = 0.45; t["strategy_crit_rate"] += value
                elif s == "心攻": value = 0.22
                elif s == "離反": value = 0.15
                elif s == "回避": value = 0.35
                elif s == "反撃": rate = 1.48
                if add_status(t, s, sim.get("duration",1), value, rate, actor, log): log.buff(actor["name"], t["name"], f"{s}付与（{sim.get('duration',1)}T）")
        elif s in DOT_STATUSES | CONTROL_STATUSES | {"回復不可"}:
            for t in targets:
                if add_status(t, s, sim.get("duration",1), source=actor, log=log): log.status_detail(t, actor, skill["name"], s, sim.get("duration",1))
    return True


def normal_attack(actor, allies, enemies, log, cfg):
    if has_status(actor,"封撃"):
        log.event("🟣", actor["name"], "封撃により通常攻撃不可")
        return
    times = 2 if has_status(actor,"連撃") else 1
    actor["_assault_checked_names"] = set()
    for _ in range(times):
        pool = [u for u in living(allies+enemies) if u is not actor] if has_status(actor,"混乱") else None
        target = random.choice(pool) if pool else (choose_targets(actor, allies, enemies, {"side":"enemy","scope":"single","count_min":1,"count_max":1}) or [None])[0]
        if not target:
            return
        if pool:
            log.event("🌀", actor["name"], "混乱により対象ランダム化")
        dmg, kind = base_damage(actor, target, 1.0, "physical", cfg["normal_damage_base"])
        dmg = apply_crit(actor, dmg, "physical", log, cfg["crit_base_bonus"])
        receive_damage(actor, target, dmg, "normal", kind, log, cfg, skill_name="通常攻撃")
        if actor.get("horo_musha") and target and target.get("troops", 0) > 0:
            target["damage_taken_bonus"] += 0.03
            log.event("🐎", actor["name"], f"母衣武者：{target['name']}の被ダメージ+3%")
        for sk in actor["skills"]:
            if is_troop_skill(sk):
                continue
            if sk.get("skill_type") == "突撃":
                # 1回の行動中に同名突撃を何度も再判定しない。古今独歩などの多重判定対策。
                if sk.get("name") in actor["_assault_checked_names"]:
                    continue
                actor["_assault_checked_names"].add(sk.get("name"))
                proc = min(1.0, sk.get("proc",0.35)+actor.get("proc_bonus",0))
                log.event("🎲", actor["name"], f"突撃『{sk['name']}』判定 {int(proc*100)}%")
                if random.random() <= proc:
                    log.event("⚡", actor["name"], f"突撃戦法『{sk['name']}』発動")
                    sim = sk.get("sim",{})
                    dtype = sim.get("damage_type","physical")
                    does_damage = sk.get("does_damage", None)
                    if does_damage is None:
                        effect_text = sk.get("effect", "")
                        does_damage = ("ダメージ" in effect_text) and ("被ダメージ" not in effect_text) and ("ダメージが低下" not in effect_text)
                    if sk.get("name") in NON_DAMAGE_ASSAULT_SKILLS:
                        does_damage = False
                    if does_damage:
                        for rate in sim.get("damage_rates",[]) or [1.5]:
                            sdmg, skind = base_damage(actor, target, rate, dtype, cfg["damage_base"])
                            sdmg = apply_crit(actor, sdmg, dtype, log, cfg["crit_base_bonus"])
                            receive_damage(actor, target, sdmg, "assault" if dtype == "physical" else dtype, skind, log, cfg, skill_name=sk["name"])
                    else:
                        log.event("🟣", actor["name"], f"『{sk['name']}』は効果付与型のため自動ダメージなし")

def apply_passive_and_command_skills(units, log):
    for u in units:
        for sk in u["skills"]:
            if sk.get("skill_type") not in {"指揮", "受動"}:
                continue
            name, text = sk.get("name", ""), sk.get("effect", "")
            log.unit(u["name"])
            log.line(f"⚡ {sk.get('skill_type')}戦法『{name}』発動")
            if "連撃" in text:
                add_status(u, "連撃", 4, source=u, log=log); log.line("⚔️ 連撃 効果付与済み")
            if "会心" in text:
                m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*の会心", text)
                val = float(m.group(1))/100 if m else 0.20
                u["crit_rate"] += val
                log.line(f"🟡 会心（予備）効果付与済み（{int(val*100)}%）")
            if "奇策" in text:
                m = re.search(r"(\d+(?:\.\d+)?)\s*%\s*の奇策", text)
                val = float(m.group(1))/100 if m else 0.05
                u["strategy_crit_rate"] += val
                log.line(f"🟣 奇策（予備）効果付与済み（{int(val*100)}%）")
            if "会心ダメージ" in text:
                u["crit_damage_bonus"] += 0.30; log.line("🟡 会心ダメージ率+30% 効果付与済み")
            if "奇策ダメージ" in text:
                u["strategy_crit_damage_bonus"] += 0.30; log.line("🟣 奇策ダメージ率+30% 効果付与済み")
            if "回避" in text:
                add_status(u, "回避", 2, value=0.35, source=u, log=log); log.line("💨 回避 効果付与済み")
            if "洞察" in text:
                add_status(u, "洞察", 2, source=u, log=log); log.line("🛡️ 洞察 効果付与済み")
            if "休養" in text:
                add_status(u, "休養", 3, value=0.66, source=u, log=log); log.line("💚 休養 効果付与済み")
            if "被ダメージ" in text and "低下" in text:
                u["damage_reduce"] += 0.12; log.line("🛡️ 被ダメージ低下 効果付与済み")
            if "与ダメージ" in text and "上昇" in text:
                u["physical_damage_bonus"] += 0.10; u["strategy_damage_bonus"] += 0.10; log.line("⬆️ 与ダメージ上昇 効果付与済み")
            if name == "同気連枝":
                u["_ohatsu"] = True; log.line("🌸 同気連枝：被弾時回復支援 効果付与済み")
            if name == "風姿綽約":
                u["_oe"] = True; u["_oe_layers"] = 0; u["_oe_applied"] = set(); log.line("🌺 風姿綽約：武勇累積 効果付与済み")

def special_turn_start(u, allies, enemies, log):
    if u.get("_ohatsu") and random.random() < 0.48:
        for t in random.sample(living(enemies), min(len(living(enemies)), random.randint(2,3))): add_status(t,"同気連枝対象",1,value=0.28,source=u,log=log); log.event("🌸",u["name"],f"同気連枝：{t['name']}を監視対象化")
    if u.get("_oe"):
        u["_oe_layers"] = min(4, u.get("_oe_layers",0)+1)
        for a in random.sample(living(allies), min(2, len(living(allies)))):
            buff = int(a["stats"].get("str",100)*0.04); a["stats"]["str"] += buff; log.event("🌺",u["name"],f"風姿綽約：{a['name']}の武勇 +4%（{u['_oe_layers']}層）")
        if u["_oe_layers"] >= 4 and random.random() < 0.65 and living(enemies):
            t = random.choice(living(enemies)); candidates = [x for x in ["混乱","封撃","無策","疲弊"] if x not in u.get("_oe_applied",set())]
            if candidates:
                s = random.choice(candidates); u["_oe_applied"].add(s); add_status(t,s,1,source=u,log=log); log.status(u["name"],t["name"],s,1)





# ============================================================
# 凸効果
# ============================================================

def first_pct(text, default=0.0):
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[％%]", text or "")
    return float(m.group(1)) / 100 if m else default

def first_number(text, default=0.0):
    m = re.search(r"([0-9]+(?:\.[0-9]+)?)", text or "")
    return float(m.group(1)) if m else default

def troop_matches(effect_text, troop_type):
    txt = effect_text or ""
    if troop_type == "騎兵":
        return "騎兵" in txt or "馬術" in txt or "馬砲" in txt or "馬槍" in txt
    if troop_type == "弓兵":
        return "弓兵" in txt or "弓術" in txt or "弓槍" in txt or "弓・砲" in txt
    if troop_type == "足軽":
        return "足軽" in txt or "槍術" in txt or "弓槍" in txt or "馬槍" in txt
    if troop_type == "鉄砲":
        return "鉄砲" in txt or "砲術" in txt or "馬砲" in txt or "弓・砲" in txt
    return False

def apply_trait_text(unit, effect_name, effect_text, side, troop_type, log):
    text = effect_text or ""
    pct = first_pct(text, 0.0)
    targets = side if "自軍全体" in text else [unit]

    # 兵種レベル：1Lvごとに主要属性2%上昇として反映
    if "部隊の" in text and "レベル" in text and "増加" in text and troop_matches(text + effect_name, troop_type):
        level = int(first_number(effect_name + " " + text, 1))
        bonus = 0.02 * level
        for t in targets:
            for k in ["str", "int", "lea", "spd"]:
                t["stats"][k] = int(t["stats"].get(k, 0) * (1 + bonus))
        log.event("🧩", unit["name"], f"凸効果「{effect_name}」：{troop_type}一致で主要属性 +{int(bonus*100)}%")
        return

    for t in targets:
        if ("武勇" in text or "武威" in effect_name) and ("上昇" in text or "増加" in text):
            t["stats"]["str"] = int(t["stats"].get("str", 0) * (1 + pct))
        if ("知略" in text or "知恵" in effect_name) and ("上昇" in text or "増加" in text):
            t["stats"]["int"] = int(t["stats"].get("int", 0) * (1 + pct))
        if ("統率" in text or "統帥" in effect_name or "統師" in effect_name) and ("上昇" in text or "増加" in text):
            t["stats"]["lea"] = int(t["stats"].get("lea", 0) * (1 + pct))
        if ("速度" in text or "急速" in effect_name) and ("上昇" in text or "増加" in text):
            t["stats"]["spd"] = int(t["stats"].get("spd", 0) * (1 + pct))

        if "兵刃与ダメージ" in text or "兵刃ダメージが" in text and "増加" in text:
            t["physical_damage_bonus"] += pct
        elif "計略与ダメージ" in text or ("計略ダメージ" in text and "増加" in text and "被" not in text and "減少" not in text):
            t["strategy_damage_bonus"] += pct
        elif "与ダメージ" in text and "増加" in text:
            t["physical_damage_bonus"] += pct
            t["strategy_damage_bonus"] += pct

        if "兵刃被ダメージ" in text and "減少" in text:
            t["damage_reduce"] += pct
        elif "計略被ダメージ" in text and "減少" in text:
            t["damage_reduce"] += pct
        elif "被ダメージ" in text and "減少" in text:
            t["damage_reduce"] += pct
        elif "被ダメージ" in text and "上昇" in text:
            t["damage_taken_bonus"] += pct

        if "会心ダメージ率" in text:
            t["crit_damage_bonus"] += pct
        elif "会心" in text and "獲得" in text:
            t["crit_rate"] += pct
        if "奇策" in text and "獲得" in text:
            t["strategy_crit_rate"] += pct

        if "離反" in text and "獲得" in text:
            add_status(t, "離反", 99, value=pct or 0.10, source=unit, log=log)
        if "洞察" in text:
            add_status(t, "洞察", 99, source=unit, log=log)
        if "回避" in text or "通常攻撃を無効" in text:
            add_status(t, "回避", 99, value=pct or 0.25, source=unit, log=log)
        if "鉄壁" in text:
            add_status(t, "鉄壁", 99, source=unit, log=log)
        if "固有" in text and "発動" in text:
            # 固有再判定や固有発動率上昇は unique_proc_bonus に簡易反映
            t["unique_proc_bonus"] += pct
        elif "能動戦法" in text and "発動" in text:
            t["proc_bonus"] += pct

    log.event("🧩", unit["name"], f"凸効果「{effect_name}」適用：{effect_text}")

def apply_limit_break_effects(side, troop_type, log, label):
    for u in side:
        effects = TRAITS_BY_NAME.get(u["name"], [])
        if not effects:
            continue
        lb = u.get("limit_break", 0)
        for item in effects:
            unlock = int(item.get("unlock", 0))
            if lb >= unlock:
                apply_trait_text(u, item.get("name", ""), item.get("effect", ""), side, troop_type, log)


# ============================================================
# 家門バフ・軍学
# ============================================================

KAMON_LEVEL_BONUS = {
    0: (0.0, 0.0),
    1: (1.0, 0.5),
    2: (2.0, 1.0),
    3: (3.0, 1.5),
    4: (0.0, 2.0),
    5: (0.0, 2.5),
    6: (0.0, 3.0),
    7: (0.0, 4.0),
    8: (0.0, 5.0),
    9: (0.0, 6.0),
    10: (0.0, 7.0),
}

GUNGAKU_LEVEL = {
    0: {"str_int_pct": 0.0, "spd": 0.0, "lea": 0.0, "damage": 0.0, "taken": 0.0, "reduce": 0.0},
    1: {"str_int_pct": 0.005, "spd": 1.0, "lea": 1.0, "damage": 0.0025, "taken": 0.0025, "reduce": 0.005},
    2: {"str_int_pct": 0.010, "spd": 2.0, "lea": 2.0, "damage": 0.0050, "taken": 0.0050, "reduce": 0.010},
    3: {"str_int_pct": 0.015, "spd": 3.0, "lea": 3.0, "damage": 0.0075, "taken": 0.0075, "reduce": 0.015},
    4: {"str_int_pct": 0.020, "spd": 4.0, "lea": 4.0, "damage": 0.0100, "taken": 0.0100, "reduce": 0.020},
    5: {"str_int_pct": 0.025, "spd": 5.0, "lea": 5.0, "damage": 0.0125, "taken": 0.0125, "reduce": 0.025},
}

def unit_faction(u):
    raw = u.get("raw", {})
    return raw.get("faction") or raw.get("勢力") or raw.get("camp") or ""

def kamon_factions_for_unit(u, side):
    f = unit_faction(u)
    factions = {f} if f else set()
    # 徳川1凸以上：徳川以外の同一家門が2体いる場合、その家門扱いにも含める
    if f == "徳川" and u.get("limit_break", 0) >= 1:
        others = [unit_faction(x) for x in side if x is not u and unit_faction(x) and unit_faction(x) != "徳川"]
        for of in set(others):
            if others.count(of) >= 2:
                factions.add(of)
    return factions

def apply_kamon_buffs(side, level, log, label):
    if level <= 0:
        return
    main_bonus, other_bonus = KAMON_LEVEL_BONUS.get(level, (0.0, 0.0))
    factions = ["織田", "武田", "上杉", "徳川", "豊臣", "群雄"]
    for f in factions:
        members = [u for u in side if f in kamon_factions_for_unit(u, side)]
        if len(members) >= 3:
            for u in members:
                if main_bonus:
                    u["stats"]["str"] = int(u["stats"].get("str", 0) * (1 + main_bonus / 100))
                    u["stats"]["int"] = int(u["stats"].get("int", 0) * (1 + main_bonus / 100))
                if other_bonus:
                    u["stats"]["lea"] = int(u["stats"].get("lea", 0) * (1 + other_bonus / 100))
                    u["stats"]["spd"] = int(u["stats"].get("spd", 0) * (1 + other_bonus / 100))
                    u["physical_damage_bonus"] += other_bonus / 100
                    u["strategy_damage_bonus"] += other_bonus / 100
                    u["damage_reduce"] += other_bonus / 100
            log.event("🏯", f"{label}軍", f"{f}家門バフLv{level}発動")

def apply_gungaku(side, troop_type, level, log, label):
    if level <= 0:
        return
    g = GUNGAKU_LEVEL.get(level, GUNGAKU_LEVEL[0])
    for u in side:
        if troop_type == "騎兵":
            u["stats"]["str"] = int(u["stats"].get("str", 0) * (1 + g["str_int_pct"]))
            u["stats"]["int"] = int(u["stats"].get("int", 0) * (1 + g["str_int_pct"]))
            u["physical_damage_bonus"] += g["damage"]
            u["strategy_damage_bonus"] += g["damage"]
            u["damage_taken_bonus"] += g["taken"]
        elif troop_type == "弓兵":
            u["stats"]["spd"] = int(u["stats"].get("spd", 0) + g["spd"])
            u["physical_damage_bonus"] += g["damage"]
            u["strategy_damage_bonus"] += g["damage"]
        elif troop_type == "足軽":
            u["stats"]["lea"] = int(u["stats"].get("lea", 0) + g["lea"])
            u["damage_reduce"] += g["reduce"]
        elif troop_type == "鉄砲":
            u["stats"]["str"] = int(u["stats"].get("str", 0) * (1 + g["str_int_pct"]))
            u["stats"]["int"] = int(u["stats"].get("int", 0) * (1 + g["str_int_pct"]))
            u["physical_damage_bonus"] += g["damage"]
            u["strategy_damage_bonus"] += g["damage"]
            u["damage_taken_bonus"] += g["taken"]
    log.event("🎓", f"{label}軍", f"軍学 {troop_type} Lv{level} 適用")

def process_gungaku_lv5(side, enemy, troop_type, level, turn, log, cfg, label):
    if level < 5:
        return
    if troop_type == "弓兵" and turn in {2, 6}:
        attackers = random.sample(living(side), min(len(living(side)), random.randint(2, 3)))
        targets = random.sample(living(enemy), min(len(living(enemy)), random.randint(1, 2)))
        for a in attackers:
            for t in targets:
                dmg, kind = base_damage(a, t, 0.60, "physical", cfg["normal_damage_base"])
                receive_damage(a, t, dmg, "physical", kind, log, cfg, skill_name="軍学Lv5 斉射")
        log.event("🏹", f"{label}軍", "軍学Lv5 斉射 発動")
    elif troop_type == "足軽" and turn == 5:
        for u in random.sample(living(side), min(2, len(living(side)))):
            heal(u, u, int(cfg["heal_base"] * 1.00), log, cfg["heal_damage_rate"], reason="軍学Lv5 守禦")
        log.event("🛡️", f"{label}軍", "軍学Lv5 守禦 発動")
    elif troop_type == "鉄砲" and turn == 3 and living(side):
        u = random.choice(living(side))
        add_status(u, "破陣", 1, value=0.25, source=u, log=log)
        log.event("🔫", f"{label}軍", f"軍学Lv5 破軍：{u['name']}に25%破陣付与")
    elif troop_type == "騎兵" and turn == 1:
        log.event("🐎", f"{label}軍", "軍学Lv5 疾行：移送速度効果のため戦闘内効果なし")


def apply_troop_skill(side_units, troop_type, log):
    for unit in side_units:
        for skill in unit.get("skills", []):
            stype = normalize_skill_type(skill)
            name = skill_name(skill)
            if stype not in TROOP_SKILL_TYPES:
                continue

            required = TROOP_SKILL_REQUIRED_TYPE.get(name)
            if required and required != troop_type:
                log_line_safe(log, f"［{unit.get('name','不明')}］の兵種戦法「{name}」は必要兵種{required}のため発動しません")
                continue

            log_line_safe(log, f"【{unit.get('name','不明')}】")
            log_line_safe(log, f"🛡️ 兵種戦法「{name}」発動")

            if name in {"大太刀", "大太刀力士隊"}:
                for ally in side_units:
                    ally["otachi_counter_rate"] = 0.30
                    ally["otachi_counter_damage_rate"] = 1.00
                    ally["normal_assault_reduce_until_turn"] = 2
                    ally["normal_assault_reduce_rate"] = 0.18
                log_line_safe(log, "↩️ 反撃 効果付与済み")
                log_line_safe(log, "🛡️ 通常攻撃・突撃被ダメ軽減 効果付与済み")

            if name in {"三河弓", "三河弓兵隊"}:
                for ally in side_units:
                    ally["mikawa_heal"] = True
                    ally["stats"]["lea"] = ally.get("stats", {}).get("lea", 0) + 20
                log_line_safe(log, "⬆️ 統率+20")
                log_line_safe(log, "💚 回生 効果付与済み")

            if name in {"赤備え隊", "甲斐赤備"}:
                for ally in side_units:
                    ally["crit_rate"] = ally.get("crit_rate", 0) + 0.35
                log_line_safe(log, "🟡 会心率+35%")

            if name == "甲斐弓" and side_units:
                side_units[0]["active_rate_bonus"] = side_units[0].get("active_rate_bonus", 0) + 0.08
                log_line_safe(log, "🎯 先頭武将 能動発動率+8%")

def simulate_battle(a_units,b_units,max_turns=8,seed=None,cfg=None,meta=None):
    if seed is not None: random.seed(seed)
    cfg = cfg or {}; meta = meta or {}; log = BattleLogger(); a = deepcopy(a_units); b = deepcopy(b_units)
    for u in a: u["side"] = "A"
    for u in b: u["side"] = "B"
    log.h("合戦開始")
    apply_limit_break_effects(a, meta.get("a_troop_type", "騎兵"), log, "A")
    apply_limit_break_effects(b, meta.get("b_troop_type", "騎兵"), log, "B")
    apply_kamon_buffs(a, meta.get("a_kamon_level", 0), log, "A")
    apply_kamon_buffs(b, meta.get("b_kamon_level", 0), log, "B")
    apply_gungaku(a, meta.get("a_troop_type", "騎兵"), meta.get("a_gungaku_level", 0), log, "A")
    apply_gungaku(b, meta.get("b_troop_type", "騎兵"), meta.get("b_gungaku_level", 0), log, "B")
    apply_troop_skills(a, meta.get("a_troop_type", "騎兵"), log, "A")
    apply_troop_skills(b, meta.get("b_troop_type", "騎兵"), log, "B")
    list_unit_skills_debug(a+b, log, meta.get('debug_show_skills', False))
    apply_passive_and_command_skills(a+b, log)
    for turn in range(1, max_turns+1):
        if total_troops(a)<=0 or total_troops(b)<=0: break
        log.h(f"{turn}ターン")
        cfg["_turn"] = turn
        process_troop_turn_effects(a, meta.get("a_troop_type", "騎兵"), turn, log, cfg, "A")
        process_troop_turn_effects(b, meta.get("b_troop_type", "騎兵"), turn, log, cfg, "B")
        process_gungaku_lv5(a, b, meta.get("a_troop_type", "騎兵"), meta.get("a_gungaku_level", 0), turn, log, cfg, "A")
        process_gungaku_lv5(b, a, meta.get("b_troop_type", "騎兵"), meta.get("b_gungaku_level", 0), turn, log, cfg, "B")
        for u in get_action_order(a,b):
            if u["troops"]>0: process_dot(u,log,cfg); process_rest(u,log,cfg)
        order = get_action_order(a,b); log.info("行動順：" + " → ".join(f"{u['name']}({u['stats'].get('spd',0)})" for u in order if u["troops"]>0))
        for actor in order:
            if actor["troops"]<=0: continue
            allies = a if actor["side"]=="A" else b; enemies = b if actor["side"]=="A" else a
            log.event("▶️", actor["name"], "行動開始"); special_turn_start(actor,allies,enemies,log)
            if has_status(actor,"威圧"): log.event("🟣",actor["name"],"威圧により行動不能"); continue
            if has_status(actor,"麻痺") and random.random()<0.30: log.event("⚡",actor["name"],"麻痺により行動不能"); continue
            for sk in actor["skills"]:
                if is_troop_skill(sk):
                    continue
                if sk.get("skill_type") == "能動": try_active_skill(actor,allies,enemies,sk,log,cfg)
            normal_attack(actor,allies,enemies,log,cfg)
            if total_troops(a)<=0 or total_troops(b)<=0: break
        for u in a+b:
            for ex in tick_statuses(u): log.event("⌛",u["name"],f"{ex} 終了")
        log.info(f"ターン終了：A軍 {total_troops(a)} / B軍 {total_troops(b)}")
    fa,fb = total_troops(a), total_troops(b); log.h("結果")
    log.info(("A軍勝利" if fa>fb else "B軍勝利" if fb>fa else "引き分け") + f"：A軍 {fa} / B軍 {fb}")
    return log.text(), fa, fb

def select_item(label, items, key, placeholder="名前で検索"):
    kw = st.text_input(f"{label} 検索", key=f"{key}_search", placeholder=placeholder)
    filtered = [x for x in items if kw in str(x.get("name",""))] if kw else items
    if kw and not filtered: st.caption("該当なし。全件表示に戻しています。"); filtered = items
    names = [x.get("name","名称不明") for x in filtered]
    if not names: st.warning(f"{label}データがありません。dataフォルダを確認してください。"); return None
    selected = st.selectbox(label, names, key=f"{key}_select")
    return next((x for x in filtered if x.get("name","名称不明") == selected), None)

def unit_ui(side, idx):
    prefix = f"{side}_{idx}"; st.markdown(f"### {side} 武将{idx}")
    g = select_item(f"{side} 武将{idx}", GENERALS, f"{prefix}_g", "例：お市、真田昌幸")
    if not g: return make_unit(f"{side}{idx}", {}, 1000, 0, {}, [])
    unique = get_unique_skill(g); cols = st.columns([1,1,1])
    with cols[0]: troops = st.number_input("兵数", min_value=1, max_value=20000, value=int(g.get("max_soldiers",10000)), key=f"{prefix}_troops")
    with cols[1]: lb_label = st.selectbox("凸", ["0凸","1凸","2凸","3凸","4凸","5凸"], key=f"{prefix}_lb"); lb = int(lb_label[0])
    with cols[2]: st.caption("固有戦法"); st.write(f"**{unique.get('name')}** / {unique.get('skill_type')} / {int(unique.get('proc',0)*100)}%" if unique else "未設定")
    trait_items = TRAITS_BY_NAME.get(g.get("name"), [])
    if trait_items:
        with st.expander("凸効果", expanded=False):
            for item in trait_items:
                mark = "✅" if lb >= int(item.get("unlock",0)) else "🔒"
                st.caption(f"{mark} {item.get('unlock',0)}凸：{item.get('name','')} / {item.get('effect','')}")
    limit = 50 + lb*10
    with st.expander("ステ振り・ステータス確認", expanded=False):
        base = get_stats(g)
        st.caption("基礎：" + format_stats(base))
        st.caption(f"ステ振り合計上限：{limit}（0凸50、1凸ごとに+10）")

        bonus = {"str": 0, "int": 0, "lea": 0, "spd": 0}
        cols2 = st.columns(4)

        bonus["str"] = cols2[0].number_input(
            "武勇振り",
            min_value=0,
            max_value=limit,
            value=0,
            step=1,
            key=f"{prefix}_bonus_str",
        )

        remain_after_str = limit - bonus["str"]

        bonus["int"] = cols2[1].number_input(
            "知略振り",
            min_value=0,
            max_value=remain_after_str,
            value=0,
            step=1,
            key=f"{prefix}_bonus_int",
        )

        remain_after_int = remain_after_str - bonus["int"]

        bonus["lea"] = cols2[2].number_input(
            "統率振り",
            min_value=0,
            max_value=remain_after_int,
            value=0,
            step=1,
            key=f"{prefix}_bonus_lea",
        )

        remain_after_lea = remain_after_int - bonus["lea"]

        bonus["spd"] = cols2[3].number_input(
            "速度振り",
            min_value=0,
            max_value=remain_after_lea,
            value=0,
            step=1,
            key=f"{prefix}_bonus_spd",
        )

        used_bonus = sum(bonus.values())
        st.caption(f"使用済み：{used_bonus} / {limit}　残り：{limit - used_bonus}")
    s1 = select_item(f"{side} 戦法1", SKILLS, f"{prefix}_s1", "例：紅蓮の炎、会盟の陣")
    s2 = select_item(f"{side} 戦法2", SKILLS, f"{prefix}_s2", "例：千軍辟易、草木皆兵")
    return make_unit(f"{side}{idx}", g, troops, lb, bonus, [s1,s2])

def main():
    st.title(APP_TITLE); st.markdown(f"<div style='text-align:right; opacity:0.75;'>Created by <b>{CREATOR}</b></div>", unsafe_allow_html=True)
    with st.sidebar:
        st.header("計算設定")
        max_turns = st.selectbox("最大ターン", [4,6,8,10], index=2); seed_text = st.text_input("乱数Seed（空欄可）", value="")
        debug_show_skills = st.checkbox("DEBUG：所持戦法確認", value=False)
        st.divider(); st.subheader("家門バフ・軍学")
        a_troop_type = st.selectbox("A軍 兵種", ["騎兵", "弓兵", "足軽", "鉄砲"], index=0)
        b_troop_type = st.selectbox("B軍 兵種", ["騎兵", "弓兵", "足軽", "鉄砲"], index=0)
        a_gungaku_level = st.selectbox("A軍 軍学Lv", [0,1,2,3,4,5], index=0)
        b_gungaku_level = st.selectbox("B軍 軍学Lv", [0,1,2,3,4,5], index=0)
        a_kamon_level = st.selectbox("A軍 家門バフLv", list(range(0,11)), index=0)
        b_kamon_level = st.selectbox("B軍 家門バフLv", list(range(0,11)), index=0)
        st.divider(); st.subheader("倍率調整")
        cfg = {
            "damage_base": st.number_input("戦法ダメージ基礎値",50,2000,420,10),
            "normal_damage_base": st.number_input("通常攻撃基礎値",50,2000,360,10),
            "dot_base": st.number_input("持続ダメージ基礎値",50,2000,320,10),
            "heal_base": st.number_input("回復基礎値",50,3000,360,10),
            "heal_damage_rate": st.slider("回復倍率",0.10,2.00,1.00,0.05),
            "crit_base_bonus": st.slider("会心/奇策 基本ダメージ増加",0.10,1.00,0.50,0.05),
        }
        st.caption("会心/奇策時：最終ダメージ = 通常ダメージ × (1 + 基本増加 + 会心/奇策ダメージ率上昇)")
    ca, cb = st.columns(2)
    with ca: st.header("A軍"); a_units = [unit_ui("A",i) for i in range(1,4)]
    with cb: st.header("B軍"); b_units = [unit_ui("B",i) for i in range(1,4)]
    st.divider()
    if st.button("シミュレーション実行", type="primary"):
        seed = int(seed_text) if seed_text.strip().isdigit() else None
        meta = {
            "a_troop_type": a_troop_type,
            "b_troop_type": b_troop_type,
            "a_gungaku_level": a_gungaku_level,
            "b_gungaku_level": b_gungaku_level,
            "a_kamon_level": a_kamon_level,
            "b_kamon_level": b_kamon_level,
            "debug_show_skills": debug_show_skills,
        }
        log_text, fa, fb = simulate_battle(a_units,b_units,max_turns=max_turns,seed=seed,cfg=cfg,meta=meta)
        if fa>fb: st.success(f"A軍勝利：A軍 {fa} / B軍 {fb}")
        elif fb>fa: st.error(f"B軍勝利：A軍 {fa} / B軍 {fb}")
        else: st.info(f"引き分け：A軍 {fa} / B軍 {fb}")
        st.subheader("戦闘ログ"); st.text_area("ログ", log_text, height=620)
        st.subheader("コピペ用ログ"); st.text_area("Discord等に貼る用", log_text, height=360, key="copy_log")

if __name__ == "__main__": main()
