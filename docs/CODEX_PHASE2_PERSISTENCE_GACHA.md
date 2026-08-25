# Codex Phase 2 追加タスク — 永続保存 + ガチャ履歴

Phase 1監査後、Next.js App Shellと並行して `docs/LOCAL_PERSISTENCE_AND_GACHA.md` を実装対象へ含める。

## 必須優先
1. IndexedDB repository layer
2. schema migration
3. 保存編成の永続化
4. 所持武将/凸/所持戦法の永続化
5. ガチャバナー管理
6. +1 / 星5 / 1つ戻る
7. 30回公式天井
8. 低排出天井目安（非公式であることを明示）
9. バナー別履歴
10. JSONバックアップ/復元

参考UX:
https://www.sanguo-zhi.com/wiki/tools/gacha-record/

コピーを作るのではなく、本アプリの武将画像カード・名前検索・シーズンDBと統合すること。

特に保存編成とガチャ履歴は、リロード/ブラウザ再起動/端末再起動/サイト更新では消さない。ブラウザのサイトデータ削除等では消えるローカル保存とする。
