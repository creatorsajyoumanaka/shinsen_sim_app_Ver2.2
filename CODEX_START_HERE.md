# Codex Start Here

Codexにこのリポジトリを開かせたら、まず次の指示で開始してください。

```text
このリポジトリの Issue #1「Codex Phase 1: 全武将監査と戦闘式監査」を実装してください。

必ず codex/app-rebuild-v1 ブランチを基準に作業し、最初に以下を読んでください。
- CODEX_APP_REBUILD_SPEC.md
- docs/RESEARCH_BASELINE_2026-08.md
- docs/LOCAL_PERSISTENCE_AND_GACHA.md
- docs/CODEX_PHASE2_PERSISTENCE_GACHA.md
- Issue #1
- Issue #2

main の既存Streamlit版は削除・破壊しないでください。

Phase 1ではUIを先に作らず、まず以下を完了してください。
1. scripts/audit_generals.py を実行
2. S1/S2/S3/PK(S4)までの全武将データ監査
3. docs/data_audit.md を作成
4. app.py と過去エンジンの戦闘計算式を監査
5. docs/battle_engine_audit.md を作成
6. 三国志真戦由来の仮定、信長真戦の実測仮説、由来不明の式を区別
7. 旧Python版をgolden referenceとして残す新エンジン設計案を作る
8. 変更後に実行したチェック/テスト結果を報告

勝手に公開情報の推定式を公式確定式として扱わないでください。
武将画像は後工程で入れられる構造を作りますが、このPhaseでは画像の無断収集をしないでください。

Phase 1のAcceptance Criteriaを全部満たしたら、変更内容・残課題・次にPhase 2で触るファイルをまとめてください。

Phase 1完了後は、Issue #2「Codex Phase 2: App Shell + 永続保存 + ガチャ履歴」を実装してください。
Phase 2では、Next.js App Shell、武将画像カード/名前検索、IndexedDB永続化、所持管理、保存編成、ガチャ履歴MVP、JSONバックアップ/復元までを対象にします。
```

## Phase 1後

Phase 1の監査結果を確認してから、Issue #2に従ってPhase 2へ進む。

Phase 2主要項目:

- Next.js / TypeScript App Shell
- PCサイドバー（通常 / アイコンのみ / 非表示）
- スマホ下部ナビ
- 武将画像カード + プレースホルダー
- 名前検索
- S1〜S4シーズン切替
- IndexedDB repository layer
- 所持武将 / 凸 / 所持戦法の永続保存
- 保存編成の永続保存
- ガチャ履歴
  - バナー別管理
  - +1
  - 星5記録
  - 1つ戻る
  - 30回天井
  - 星5排出率
- JSONバックアップ / 復元
- 明示的なローカルデータ削除

保存編成・所持データ・ガチャ履歴は、通常のページ更新やブラウザ再起動では消えないこと。ブラウザのサイトデータ削除等では消えるローカル保存とする。

Phase 2以降も、UIだけを完成させて戦闘計算をダミーのまま最終完成扱いしない。
