# 合戦開始フェーズ仕様 — 軍学 / 家門 / 兵種戦法 / 指揮・受動 / 凸特性

## 目的

戦闘開始前に適用される恒常・開幕効果を、ターン中の能動戦法と混在させず、明確な `opening phase` として処理する。

旧Streamlit版にはすでに以下の順で開幕処理が存在する。

1. 凸・特性
2. 家門バフ
3. 軍学
4. 兵種戦法
5. 指揮 / 受動
6. 1ターン目へ移行

ただし、この順序・各数値・重複可否が信長真戦の正式仕様と一致しているかは未確定のため、Phase 1監査対象とする。

---

# 1. Opening Phaseを独立させる

新エンジンでは最低限以下のphaseを分ける。

```ts
type BattlePhase =
  | "setup"
  | "trait"
  | "family_buff"
  | "military_academy"
  | "troop_skill"
  | "passive"
  | "command"
  | "turn_start"
  | "active"
  | "normal_attack"
  | "assault"
  | "turn_end"
```

開幕効果はeventとして記録し、戦闘ログ・デバッグ・兵損グラフ側から参照できるようにする。

---

# 2. 開幕snapshot

ターン1開始前の状態を必ず保存する。

```ts
interface OpeningSnapshot {
  side: "ally" | "enemy"
  troopType: string
  familyBuffLevel: number
  militaryAcademyLevel: number
  units: Array<{
    generalId: string
    statsBefore: Record<string, number>
    statsAfter: Record<string, number>
    damageModifiersBefore: Record<string, number>
    damageModifiersAfter: Record<string, number>
    statuses: string[]
    appliedEffects: OpeningEffectRecord[]
  }>
}
```

これにより「なぜ速度が200になったか」「統率が何で増えたか」「会心率がどこから来たか」を追跡可能にする。

---

# 3. OpeningEffectRecord

```ts
interface OpeningEffectRecord {
  sourceType:
    | "trait"
    | "family_buff"
    | "military_academy"
    | "troop_skill"
    | "passive"
    | "command"
  sourceId?: string
  sourceName: string
  targetIds: string[]
  effectKey: string
  operation: "add" | "multiply" | "set" | "status" | "flag"
  value?: number
  durationTurns?: number
  stackGroup?: string
  stackRule?: "add" | "highest" | "latest" | "exclusive" | "unknown"
  provenance: "confirmed_nobunaga" | "measured_hypothesis" | "legacy_sangokushi" | "unknown_origin"
}
```

由来不明な係数を確定仕様として扱わない。

---

# 4. 軍学

旧版では `GUNGAKU_LEVEL` をLv0〜5で保持し、兵種ごとに開幕補正を適用している。

現状の旧実装:

- 騎兵: 武勇/知略%補正、与ダメ補正等
- 弓兵: 速度加算、与ダメ補正
- 足軽: 統率加算、被ダメ軽減
- 鉄砲: 武勇/知略%補正、与ダメ補正等

さらにLv5はターン条件付きの追加効果が別処理で存在する。

### 重要

現行係数は信長真戦の確定値として扱わない。

特に `damage_taken_bonus` の符号/意味、加算か乗算か、属性上昇が%か固定値かを監査する。

軍学Lv5のターン効果も公式/実測根拠を確認する。

---

# 5. 兵種戦法

兵種戦法は毎ターン発動率判定する戦法ではなく、原則として兵種一致時に合戦開始で効果をセットする設計。

旧版にある例:

- 大太刀 / 大太刀力士隊
- 三河弓 / 三河弓兵隊
- 赤備え隊 / 甲斐赤備
- 甲斐弓
- 母衣武者
- その他 `TROOP_SKILL_REQUIRED_TYPE` 登録分

新実装では戦法名ハードコードだけに依存せず、master側に以下を持てる形を目標にする。

```ts
interface TroopSkillEffect {
  requiredTroopType?: string
  trigger: "battle_start" | "turn_start" | "on_hit" | "on_normal_attack" | "on_assault"
  effects: EffectDefinition[]
}
```

兵種不一致時は発動せず、理由をログに残す。

---

# 6. 家門バフ

家門判定と必要人数、徳川などの特殊な所属判定を開幕処理で適用する。

監査項目:

- 必要人数
- 対象範囲
- 属性上昇
- 与ダメ/被ダメ補正
- 複数家門扱い
- 凸による所属判定変更
- 加算/乗算順序

---

# 7. 凸・特性

凸効果のうち合戦開始時から常時効くものはopening phaseで適用。

例:

- 主要属性補正
- 兵種一致補正
- 会心/奇策
- 洞察/回避/鉄壁
- 固有/能動発動率補正
- 与ダメ/被ダメ補正

ターン開始時や被弾時など条件付きのものはフラグ/triggerとして登録し、開幕時に最終効果まで即時適用しない。

---

# 8. 指揮 / 受動

旧版は指揮・受動を合戦開始後にまとめて適用している。

新実装では `指揮` と `受動` を別phaseとして追跡可能にする。
同種内の発動順が速度/戦法枠/武将順の影響を受ける場合に備え、order keyを持たせる。

```ts
interface OpeningOrderKey {
  phasePriority: number
  speed?: number
  skillSlot?: number
  teamIndex?: number
}
```

順序が未確認なら `unknown_origin` として監査対象にする。

---

# 9. 重複・上書きルール

開幕バフは単純加算を前提にしない。

最低限、各効果に:

- 加算
- 乗算
- 最大値のみ
- 後勝ち
- 排他
- 重複不可

を設定できるようにする。

同じ種類の与ダメージ上昇が複数ある場合など、実ゲームのスタック規則を検証できる構造にする。

---

# 10. UI

編成/シミュレーション画面に「開戦時補正」確認欄を用意する。

例:

```text
開戦時補正

軍学: 足軽 Lv5
家門: 豊臣 Lv8
兵種戦法: 大太刀

黒田官兵衛
知略 229 → 241
統率 167 → 181
与ダメ +x%
被ダメ -y%

[詳細を見る]
```

普段は折りたたみ。
詳細では効果の出典・適用順・加算/乗算を確認できる。

---

# 11. 兵損グラフとの連携

グラフの0T / 開戦時点にOpening Snapshotを紐付ける。

ユーザーが0Tをタップした場合:

- 軍学
- 家門
- 兵種戦法
- 凸特性
- 指揮/受動

で何が変化したかを表示できるようにする。

---

# 12. Acceptance Criteria

- [ ] Opening Phaseがターン処理から分離されている
- [ ] 凸/家門/軍学/兵種戦法/受動/指揮を個別に記録
- [ ] 適用前後のステータスsnapshotを保存
- [ ] 兵種不一致戦法は理由付きで無効化
- [ ] 軍学Lv5のターン効果は開幕バフと分離
- [ ] 効果ごとにprovenanceを持つ
- [ ] 加算/乗算/排他等のstack ruleを持つ
- [ ] 0Tでグラフ/ログから開幕効果を確認可能
- [ ] 現行旧版の重複処理・符号・係数を監査
- [ ] 未検証係数を確定値として扱わない
