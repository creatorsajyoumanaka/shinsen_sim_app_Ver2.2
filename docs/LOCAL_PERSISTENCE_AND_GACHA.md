# ローカル永続化 + ガチャ履歴機能 仕様

## 目的

Webアプリ上で、ユーザーが自分で入力した以下のデータを**ページ更新・ブラウザ再起動・端末再起動・サイト側アップデート後も残す**。

- ガチャ履歴
- 保存した編成
- 所持武将
- 武将の凸数
- 所持戦法
- お気に入り
- UI設定（サイドバー状態、一覧表示形式など）

サーバー保存を必須にせず、初期版は端末・ブラウザ内のローカル保存で成立させる。

> 注意: 一般に「キャッシュ削除」だけではLocalStorage/IndexedDBが消えない場合がある。ユーザーの意図は「通常利用では消えず、自分でサイトデータを削除したときに消える」挙動と解釈する。ブラウザの「履歴・Cookie・サイトデータ削除」、PWA削除、ストレージ自動整理、プライベートモード等では消える可能性がある。

---

# 1. 保存方式

## IndexedDBを主保存先にする

ガチャ履歴・保存編成などの構造化データは `IndexedDB` を使用する。

理由:
- LocalStorageより容量が大きい
- 配列・履歴データを扱いやすい
- 将来データ量が増えても耐えやすい
- トランザクションが使える
- JSONの巨大文字列1本より安全

## LocalStorageを補助利用

軽量設定のみLocalStorage。

例:
- sidebar mode
- dark mode
- list/grid mode
- last selected season
- last selected gacha banner

---

# 2. ローカルDB案

DB名例:

`shinsen-app-local-v1`

Stores:

```text
user_profile
owned_generals
owned_skills
saved_formations
gacha_banners
gacha_events
app_settings
schema_meta
```

## schema version

必ず `schema_meta` にバージョンを持ち、アプリ更新時にmigration可能にする。

既存ユーザーデータをアプリ更新で消さないこと。

---

# 3. 保存編成

保存した編成はIndexedDBへ永続化する。

```ts
interface SavedFormation {
  id: string
  name: string
  season: "S1" | "S2" | "S3" | "S4"
  troopType?: string
  members: Array<{
    generalId: string
    isLeader: boolean
    limitBreak: number
    skillIds: string[]
    academy?: string[]
    traits?: string[]
    statAllocation?: Record<string, number>
  }>
  notes?: string
  tags?: string[]
  createdAt: string
  updatedAt: string
}
```

## 必須機能

- 保存
- 上書き保存
- 複製
- 名前変更
- 削除
- お気に入り
- 検索
- タグ
- 最終更新日時

保存後、リロード・再起動しても残る。

---

# 4. ガチャ履歴ツール

参考UX:
`https://www.sanguo-zhi.com/wiki/tools/gacha-record/`

参考ページは、ガチャパックごとに履歴を分け、公式30回天井、星5の高排出連続回数、低排出天井の目安、合計ガチャ数などをローカル保存している。

当アプリでも同等以上の使い勝手を目標にする。

## ガチャバナー/記録単位

```ts
interface GachaBanner {
  id: string
  name: string
  season: "S1" | "S2" | "S3" | "S4"
  bannerType?: "meisho" | "pickup" | "limited" | "custom"
  createdAt: string
  updatedAt: string
  resetAt?: string
  totalPulls: number
}
```

ユーザーが任意に追加・名前変更可能。

例:
- S4 名将
- 守護没落
- ピックアップA

---

# 5. ガチャ履歴イベント

1回ごとの履歴をeventとして残す。

```ts
interface GachaEvent {
  id: string
  bannerId: string
  eventType: "pull" | "five_star" | "reset" | "manual_adjust"
  pullCountDelta: number
  generalId?: string
  rarity?: number
  isLowRate?: boolean
  isFree?: boolean
  isHalfPrice?: boolean
  obtainedAt?: string
  note?: string
  createdAt: string
}
```

## 重要

「現在値だけ」を保存するのではなく、**イベント履歴を残して現在値を再計算できる設計**にする。

これにより:
- 1つ戻る
- 間違えた記録を修正
- 履歴一覧
- 日別集計
- シーズン集計
- 排出率集計
が安全にできる。

---

# 6. ガチャ操作UI

最低限:

- `+1 ガチャを引いた`
- `星5を引いた`
- `1つ戻る`
- `ガチャ追加`
- `名前変更`
- `シーズン跨ぎリセット`
- `このガチャを削除`

星5入力時は武将画像 + 名前検索から選択できるようにする。

既存の武将DBと共通コンポーネントを使う。

---

# 7. 天井・集計

## 公式30回天井

名将系など対象バナーでは、星5を引いた時点から次の星5までのカウントを管理。

表示例:

```text
公式天井まで 12 / 30
残り最大18回
```

ただしバナー種別ごとにルールが異なる可能性があるため、天井ルールを設定化する。

```ts
interface GachaRuleConfig {
  officialFiveStarPity?: number
  highRateStreakForLowRatePity?: number
  resetOnSeasonChange: boolean
}
```

## 低排出天井

公開攻略情報で言われている「高排出星5を5連続 → 次の星5が低排出」という挙動は、**非公式/観測ルール**として扱う。

UI上も:

`低排出天井目安（非公式）`

と表示し、公式仕様のように断定しない。

低排出分類は武将マスター側にseason/banner単位のmetadataを持たせられる構造にする。

---

# 8. ガチャ集計画面

最低限表示:

- 合計ガチャ回数
- 星5総数
- 星5排出率
- 星5までの平均回数
- 最短/最長
- 現在の公式天井カウント
- 高排出連続回数
- 低排出天井目安
- 武将別獲得回数
- 日付別履歴

将来:
- シーズン比較
- バナー比較
- 円/金貨換算
- グラフ
- 画像保存

---

# 9. 一括バックアップ

ローカル保存は便利だが、サイトデータ削除や端末変更で消えるため、**エクスポート/インポート**を必須寄り機能として用意する。

## JSONエクスポート

一括で:
- 所持武将
- 凸
- 所持戦法
- 保存編成
- ガチャ履歴
- 設定

を1ファイルへ出力。

例:

`shinsen-backup-2026-08-25.json`

## インポート

- schema version確認
- 既存データへマージ / 全置換を選択
- 壊れたデータは拒否
- マスターに存在しない古いIDは削除せずunknownとして保持

---

# 10. データ削除UI

設定画面に明示的な削除機能を置く。

- ガチャ履歴だけ削除
- 保存編成だけ削除
- 所持データだけ削除
- 全ローカルデータ削除

`全削除` は確認ダイアログ必須。

ブラウザ側でサイトデータを削除した場合にも当然消える。

---

# 11. PWA/スマホ注意

iPhone Safari / PWAでは通常は再読込・再起動で保持されるが、OS/ブラウザ都合のストレージ整理があり得る。

そのためUI内に:

`このデータはこの端末のブラウザ内に保存されています。端末変更やサイトデータ削除に備えてバックアップを推奨します。`

という説明を出す。

---

# 12. Codex実装優先順位

## Phase A
- IndexedDB repository layer
- LocalStorage settings layer
- schema version/migration
- 保存編成の永続化
- 所持データ永続化

## Phase B
- ガチャバナーCRUD
- +1
- 星5記録
- 1つ戻る
- 履歴一覧
- 30回天井
- 非公式低排出天井目安

## Phase C
- 集計
- JSON backup/import
- 画像保存
- 高度なグラフ

---

# 13. Acceptance Criteria

- [ ] リロードしても保存編成が残る
- [ ] ブラウザを閉じて開き直しても保存編成が残る
- [ ] リロードしてもガチャ履歴が残る
- [ ] バナーごとに履歴が独立する
- [ ] +1 / 星5 / 1つ戻るが履歴イベントとして整合する
- [ ] 30回天井カウントが表示される
- [ ] 非公式低排出天井を公式仕様と誤表記しない
- [ ] アプリ更新でIndexedDBを無条件初期化しない
- [ ] JSONで全データをバックアップできる
- [ ] JSONから復元できる
- [ ] 明示的な全削除ができる
- [ ] サイトデータ削除時に消えるローカル保存であることをユーザーへ説明する

