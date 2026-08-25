# マスターデータ更新 + 編成共有/公開機能 仕様

## 目的

今後PKシーズン以降も武将・戦法・兵学・兵種戦法等が継続追加される前提で、**コードを直接触らなくても新データを追加・検証・配信できる構造**にする。

同時に、ユーザーが作った編成をURL/共有コードで渡したり、将来的に公開ギャラリーへ投稿して他ユーザーが閲覧・保存・シミュレーションできるようにする。

---

# 1. マスターデータはコードから分離

UIや戦闘エンジンに武将名・戦法名をハードコードしない。

推奨構造:

```text
data/master/
  manifest.json
  seasons.json
  generals.json
  skills.json
  traits.json
  statuses.json
  troop_skills.json
  gungaku.json
  formations_reference.json
```

`manifest.json` には最低限:

```ts
interface MasterManifest {
  schemaVersion: number
  dataVersion: string
  updatedAt: string
  latestSeason: string
  changelog?: string[]
}
```

アプリ画面に `データVer` と `最終更新日` を表示できるようにする。

---

# 2. 新武将追加を1レコードで完了できるようにする

武将追加時にアプリコードを変更しなくてもよい構造にする。

```ts
interface GeneralMaster {
  id: string
  name: string
  reading?: string
  aliases?: string[]
  faction: string
  rarity?: number
  seasonAdded: string
  cost?: number
  gender?: string
  image?: string
  baseStats: {
    str: number
    int: number
    lea: number
    spd: number
    pol?: number
    cha?: number
  }
  growthStats?: Record<string, number>
  troopAptitudes?: Record<string, string | number>
  uniqueSkillId: string
  source?: string
  checkedAt?: string
}
```

必須:
- 既存IDと重複しない
- `uniqueSkillId` が存在する
- seasonがmanifestに存在する
- 画像が無くても追加可能
- 画像欠損はplaceholder
- 読み/aliasは後付け可能

---

# 3. 管理者向け「データ追加ウィザード」

将来的に `/admin/master` などの非公開管理画面を用意できる設計にする。

### 武将追加フォーム
- 名前
- 読み
- 勢力
- シーズン
- コスト
- レア度
- 武勇/知略/統率/速度/政治/魅力
- 兵種適性
- 固有戦法
- 画像
- 出典URL
- メモ

入力後:
1. schema validation
2. ID重複確認
3. 固有戦法参照確認
4. preview
5. JSON出力
6. 必要ならGitHub master更新用データを生成

初期版では管理画面を必須にせず、**CSV/JSON import** だけでもよい。

---

# 4. CSV / JSON一括追加

シーズン開始時に8〜20名まとめて追加できるようにする。

例:

`general_import_template.csv`

Codexは:
- import parser
- schema validator
- duplicate detector
- missing reference detector
- dry-run report
を作る。

エラーが1件あっても既存masterを壊さない。

---

# 5. マスター更新とローカルユーザーデータを分離

重要。

アプリの武将/戦法masterを更新しても、IndexedDB内の:
- 所持武将
- 凸数
- 保存編成
- ガチャ履歴
- お気に入り
を消さない。

IDを安定させる。

武将名の表記修正があっても `id` は変更しない。

削除/統合された古いIDも、保存編成内ではunknown placeholderとして保持する。

---

# 6. 編成共有レベル1 — URL共有（ログイン不要）

まず最優先で実装しやすい方式。

保存編成をシリアライズしてURLまたは共有コードにする。

共有対象:
- season
- troopType
- 3武将
- 大将/副将
- 凸
- 戦法
- 兵学
- 特性
- ステ振り
- 軍学Lv
- 家門Lv
- メモ（任意）

例:

```text
/share?f=ENCODED_PAYLOAD
```

受け取った側は:
- 編成を閲覧
- 自分の保存編成へコピー
- そのままシミュレータへ送る
- 自分の所持戦法との競合確認

ができる。

共有URLを開いただけでは勝手に自分のローカルデータを書き換えない。

---

# 7. 編成共有レベル2 — 公開編成ギャラリー

将来的にサーバーDB（Supabase等）を導入して、他ユーザーが公開した編成を一覧表示できるようにする。

### CommunityFormation

```ts
interface CommunityFormation {
  id: string
  authorId?: string
  authorDisplayName?: string
  title: string
  season: string
  formation: SavedFormation
  tags?: string[]
  description?: string
  visibility: "private" | "unlisted" | "public"
  sourceType: "user" | "reference" | "admin"
  sourceUrl?: string
  createdAt: string
  updatedAt: string
  version: number
}
```

### 公開一覧で可能にしたい操作
- シーズン絞り込み
- 兵種絞り込み
- 武将名検索
- 戦法名検索
- タグ検索
- 新着
- 人気
- お気に入り/保存
- 自分の所持のみで再現できるか確認
- 戦法競合チェック
- 自分のシミュレータへコピー

---

# 8. 投稿者が公開した編成を安全に扱う

他人の公開編成を勝手に収集するのではなく、基本は:
- ユーザー本人が投稿
- 管理者が出典付きでreference登録
- 公開URLからユーザーが手動import

のいずれか。

外部サイトを自動巡回して大量転載する設計にはしない。

参考編成を登録する場合は:
- 編成構造
- season
- 出典名
- source URL
- checkedAt
のみを保持し、記事本文の大量転載は避ける。

---

# 9. 公開編成の信頼度/バージョン

編成はシーズンや環境で古くなるため:

- season
- dataVersion
- createdAt
- updatedAt
- `verifiedAgainstCurrentMaster`

を持つ。

master更新で戦法ID等が変わった場合、公開編成に:

`この編成は旧データVerで作成されています`

と表示可能にする。

---

# 10. 公開編成から直接シミュレーション

公開編成カードに:

- 保存
- コピーして編集
- シミュレーション
- 対策編成を探す

を配置できるようにする。

これにより将来的に:

`人気編成 → 自分の手持ちで対策検索`

まで繋げられる。

---

# 11. 公開時の荒らし/スパム対策

公開ギャラリーを実装する段階では最低限:

- ログイン必須投稿
- 投稿回数制限
- 通報
- 非表示/削除
- 管理者moderation
- 同一編成の大量重複対策

を設計する。

初期MVPではサーバー投稿を無理に入れず、URL共有を先に完成させる。

---

# 12. おすすめ実装順

## Phase A — master更新を簡単にする
- schema定義
- manifest
- seasonAdded
- validation script
- CSV/JSON import
- duplicate/missing reference check

## Phase B — URL共有
- SavedFormation serializer
- share URL / share code
- read-only preview
- 自分の保存編成へコピー
- simulatorへ送る

## Phase C — Community Gallery
- auth
- backend DB
- public/unlisted/private
- search/filter
- save/copy/simulate
- moderation

---

# 13. Acceptance Criteria

- [ ] 新武将追加でUIコード変更不要
- [ ] 新戦法追加でUIコード変更不要
- [ ] CSV/JSONで複数データを追加可能
- [ ] validationで重複/参照切れを検出
- [ ] master更新でIndexedDBユーザーデータを消さない
- [ ] 武将名変更でもstable IDを維持
- [ ] 保存編成をURL/共有コード化できる
- [ ] 共有編成をread-only previewできる
- [ ] 共有編成を自分の保存へコピーできる
- [ ] 共有編成をシミュレータへ送れる
- [ ] 将来の公開ギャラリー用schemaがある
- [ ] reference編成にはsource URL/checkedAtを保持
- [ ] 外部記事本文を大量転載しない
