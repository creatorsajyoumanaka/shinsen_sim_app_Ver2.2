# Community Notifications / 見逃し防止仕様

## 目的

公開編成・コメント・質問/Q&Aで、投稿者や質問者が返信や新着コメントを見逃さないようにする。

コメント機能を作るだけではなく、**自分に関係する更新を1か所で確認できる通知センター**を用意する。

---

# 1. 通知センター

ヘッダーまたはスマホBottom Navigation付近にベルアイコンを配置する。

- 未読件数badge
- `/notifications` で一覧
- 未読 / 既読
- すべて既読
- 通知単位で既読
- 通知を押すと対象の編成・コメント・質問へ直接遷移

スマホではBottom Navigationと干渉しない位置にする。

---

# 2. 通知対象

最低限以下を通知対象とする。

## 自分が投稿した公開編成
- 新しいコメント
- コメントへの返信
- 自分宛てmention
- 自分の編成から新しい質問が作られた

## 自分が投稿した質問
- 新しい回答
- 回答への返信
- accepted answerが付いた
- 質問がanswered/resolvedへ変更された

## 自分のコメント/回答
- 返信
- mention
- 投稿者または質問者からaccepted answerに選ばれた

## 管理系
- 自分の投稿/コメント/質問がmoderationされた場合
- 管理者からのお知らせ（将来）

---

# 3. Notification schema

```ts
interface CommunityNotification {
  id: string
  userId: string
  type:
    | "formation_comment"
    | "comment_reply"
    | "question_created"
    | "question_answer"
    | "question_reply"
    | "accepted_answer"
    | "mention"
    | "moderation"
    | "admin_announcement"
  actorUserId?: string
  actorDisplayName?: string
  formationId?: string
  commentId?: string
  questionId?: string
  answerId?: string
  title: string
  bodyPreview?: string
  targetUrl: string
  isRead: boolean
  createdAt: string
  readAt?: string
}
```

通知本文に大量のコメント本文を複製しない。preview程度にする。

---

# 4. 自動購読

以下は明示操作なしで自動購読する。

- 自分が公開した編成
- 自分が投稿した質問
- 自分が書いたコメント/回答の返信スレッド

ただし設定画面で個別にON/OFFできるようにする。

公開編成の閲覧者が任意で `この編成をフォロー` できる拡張も可能にする。

---

# 5. 通知設定

`/settings` に通知設定を追加。

例:
- 自分の編成へのコメント
- 自分の質問への回答
- コメント返信
- mention
- accepted answer
- 管理者通知

初期MVPではサイト内通知を必須とする。

将来的に:
- Web Push
- PWA Push
- Email

をprovider abstractionで追加可能にする。

メール/Pushはユーザーが明示的に有効化した場合のみ送信する設計にする。

---

# 6. 通知生成

コメント・返信・質問・回答などの作成成功後にNotificationを生成する。

重要:
- 自分自身の操作で自分へ通知しない
- 同じイベントを重複通知しない
- 削除済み対象への通知は安全に扱う
- soft delete後も通知一覧がクラッシュしない
- rate limit/spam対策と連携可能

---

# 7. UI例

```text
🔔 3

未読
沙条太郎さんがあなたの編成にコメントしました
「北条氏康の枠、福島正則でも大丈夫ですか？」
2分前

真戦初心者さんが質問に回答しました
「千軍がないなら理非でも…」
15分前

あなたの回答が参考になった回答に選ばれました
1時間前
```

通知をタップすると対象コメント/質問位置までscroll/highlightできるようにする。

---

# 8. 将来のPush通知

公開backend/auth導入後はWeb Push/PWA Pushに拡張できるようにする。

例:
- 「あなたの編成に新しいコメントがあります」
- 「質問に回答が付きました」
- 「あなたの回答が参考になった回答に選ばれました」

ただし初期MVPではPush実装を必須にせず、schema / service abstraction / settings拡張余地を用意する。

---

# 9. Acceptance Criteria

- [ ] notification schema
- [ ] `/notifications` route
- [ ] ベルアイコン + 未読badge
- [ ] 未読/既読
- [ ] すべて既読
- [ ] 自分の公開編成への新規コメント通知
- [ ] コメント返信通知
- [ ] 自分の質問への回答通知
- [ ] accepted answer通知
- [ ] mention拡張可能
- [ ] 通知クリックで対象へ直接遷移
- [ ] 自分自身の操作では通知しない
- [ ] notification settings schema
- [ ] 将来Web Push/Emailへ差し替え可能なprovider abstraction
- [ ] Community領域とmaster編集権限を分離したままにする
