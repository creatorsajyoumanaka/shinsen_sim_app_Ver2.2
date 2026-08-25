# Master Data Admin Access

## 方針

武将・戦法・兵学・兵種戦法・軍学などの**公式マスターデータを変更できるのはサイト管理者のみ**とする。

一般ユーザーは以下を行えても、master自体は変更できない。

- 所持武将/凸/所持戦法の保存
- 保存編成の作成
- 編成URL共有
- 将来の公開編成投稿
- ガチャ履歴

ユーザー投稿データと公式masterは完全に分離する。

---

## 初期MVP

初期版では公開サイト上にmaster書き込みAPIを用意しない。

新武将/新戦法追加は管理者が以下のいずれかで行う。

1. GitHub上のversioned master JSON/CSVを更新
2. 管理者ローカルでCSV/JSON import + validationを実行し、生成されたmasterをcommit
3. 将来の管理画面が有効な場合のみ `/admin/master` から更新

一般ユーザー向けクライアントからmasterのwrite endpointへ到達できる設計にしない。

---

## `/admin/master` を将来実装する場合

URLを隠すだけではセキュリティにならない。

必須:

- 認証
- server-side authorization
- admin allowlist
- 未認証/非adminは403
- client側判定だけに依存しない
- master更新APIも同じserver-side admin checkを通す
- 操作ログを残す
- preview/dry-run後に確定

管理者判定は将来の認証providerに応じて、環境変数またはDB側のadmin role/UID allowlistで管理できる構造にする。

例:

```text
ADMIN_USER_IDS=<owner uid list>
```

秘密情報やadmin判定用キーをNEXT_PUBLIC_*等のクライアント公開環境変数へ入れない。

---

## CommunityFormationとの分離

一般ユーザーが将来編成を投稿できる場合も、書き込み先は `CommunityFormation` 等のユーザー投稿領域に限定する。

ユーザー投稿から以下を直接変更してはならない。

- generals master
- skills master
- traits master
- gungaku master
- troop skills master
- season manifest

投稿編成内では既存stable IDを参照するだけにする。

未知ID・架空武将・任意テキストをmasterへ昇格させない。

---

## 更新フロー

推奨:

1. 管理者が新データを入力/import
2. schema validation
3. duplicate check
4. missing reference check
5. dry-run差分表示
6. dataVersion更新
7. 管理者が確定
8. deploy

master更新でIndexedDBのユーザーデータを削除しない。

---

## Acceptance Criteria

- [ ] 一般ユーザーにmaster編集UIを表示しない
- [ ] 一般ユーザーからmasterを書き換えられるAPIを公開しない
- [ ] 新武将/新戦法追加は管理者のみ
- [ ] 将来admin UIを作る場合はserver-side authorization必須
- [ ] CommunityFormationとmaster write権限を完全分離
- [ ] admin secret/allowlistをクライアントへ露出しない
- [ ] master更新はvalidation + dry-runを通す
- [ ] master更新でも既存ユーザーデータを保持する
