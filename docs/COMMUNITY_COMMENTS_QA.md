# Community Comments / Q&A 仕様

## 目的

公開編成を「見るだけ」で終わらせず、投稿者や他ユーザーに編成相談できるようにする。

典型例:
- 「この枠、○○でも大丈夫ですか？」
- 「この武将を持っていない場合は誰で代用できますか？」
- 「この戦法がない場合の代替は？」
- 「兵学はこの振り方で合っていますか？」
- 「S4環境でも使えますか？」

CommunityFormation のコメント欄と、質問専用UIを同じコミュニティ基盤で扱う。

---

## 1. 公開ニックネーム

ユーザーは公開用の `displayName`（ニックネーム）を設定できる。

最低限:
- displayName
- optional avatar
- createdAt
- optional bio

ログイン用メールアドレス等は公開しない。

将来の公開投稿・コメント・質問は `userId` で内部識別し、画面には `displayName` を表示する。

---

## 2. 編成ページのコメント欄

公開編成詳細ページの下部にコメント欄を置く。

可能な操作:
- コメント投稿
- 自分のコメント編集
- 自分のコメント削除
- 返信
- いいね
- 通報

返信は最初は1〜2階層程度でよい。無制限ネストは避ける。

投稿者本人の返信には `投稿者` バッジを表示できるようにする。
管理者には `管理者` バッジを表示できるようにする。

---

## 3. 「この枠について質問」機能

公開編成の各武将カード・各戦法欄に、

`この枠について質問`

ボタンを置けるようにする。

押すと質問フォームへ以下を自動入力する。

- formationId
- slotIndex
- originalGeneralId
- originalSkillIds
- troopType
- season

ユーザーは追加で

- 代わりに使いたい武将
- 代わりに使いたい戦法
- 自分の凸
- 所持状況
- 質問本文

を入力できる。

例:

`北条氏康を持っていないのですが、この枠を福島正則に変えても大丈夫ですか？`

質問カードには元編成と代替候補を画像+名前で並べて表示できるようにする。

---

## 4. Question schema

```ts
interface CommunityQuestion {
  id: string
  authorId: string
  authorDisplayName: string
  formationId?: string
  season?: string
  category: "formation" | "general" | "skill" | "troop" | "gungaku" | "other"
  title: string
  body: string
  target?: {
    slotIndex?: number
    originalGeneralId?: string
    replacementGeneralId?: string
    originalSkillIds?: string[]
    replacementSkillIds?: string[]
  }
  status: "open" | "answered" | "resolved"
  acceptedAnswerId?: string
  createdAt: string
  updatedAt: string
}
```

---

## 5. Comment / Answer schema

```ts
interface CommunityComment {
  id: string
  resourceType: "formation" | "question"
  resourceId: string
  authorId: string
  authorDisplayName: string
  parentCommentId?: string
  body: string
  likeCount: number
  createdAt: string
  updatedAt: string
  deletedAt?: string
}
```

Questionへのトップレベル回答は `acceptedAnswerId` でベスト回答として選択可能にする。

質問者は回答を `解決済み` にできる。

---

## 6. 質問一覧ページ

将来 `/questions` を用意。

フィルタ:
- 未回答
- 回答済み
- 解決済み
- シーズン
- 武将名
- 戦法名
- 兵種
- カテゴリ

公開編成ページ内だけでなく、

`このキャラの場合はどう組めばいい？`

のような一般質問にも使える構造にする。

---

## 7. 編成・シミュレータ連携

質問内の

- 元編成
- 代替武将
- 代替戦法

をワンタップでシミュレータへ送れるようにする。

将来的に:

`元編成 vs 代替版を比較`

でA/Bシミュレーションできる構造にする。

これにより回答者が「たぶん大丈夫」ではなく、シミュレーション結果を添えて回答できるようにする。

---

## 8. 認証・荒らし対策

公開コメント/質問投稿は原則ログインユーザーのみ。

理由:
- なりすまし防止
- 削除/編集
- 通報
- spam対策
- nickname保持

最低限:
- rate limit
- report
- mute/ban用schema
- soft delete
- 管理者非表示
- NGワード等を後付け可能な構造

匿名閲覧は可能。

---

## 9. master権限との分離

コメント・質問・公開編成を投稿できても、公式masterは変更できない。

Community DB と master write権限は完全に分離する。

---

## 10. MVP優先度

Full Build中に公開バックエンドまで作れない場合でも、最低限以下は先に実装/定義する。

- displayName schema
- CommunityQuestion schema
- CommunityComment schema
- 編成詳細のコメントUI skeleton
- `この枠について質問` UI skeleton
- `/questions` route skeleton
- repository/service abstraction

Supabase等のbackendを後から接続してもUIを書き直さずに済む構造にする。

---

## Acceptance Criteria

- [ ] ニックネーム(displayName)を公開名として使える
- [ ] 公開編成にコメントできる設計
- [ ] コメント返信ができる設計
- [ ] 投稿者/管理者バッジ
- [ ] 各武将枠から「この枠について質問」へ進める
- [ ] 代替武将/代替戦法を指定して質問できる
- [ ] 質問に回答できる
- [ ] 質問者が解決済みにできる
- [ ] accepted answerを保持できる
- [ ] `/questions` に拡張可能
- [ ] 質問内容をシミュレータへ送れる
- [ ] 通報/削除/rate limit等のmoderation拡張余地
- [ ] Community権限とmaster編集権限を分離
