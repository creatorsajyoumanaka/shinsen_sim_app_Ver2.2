# Codex Start Here

Codexにこのリポジトリを開かせたら、まず次の指示で開始してください。

```text
このリポジトリの Issue #1「Codex Phase 1: 全武将監査と戦闘式監査」を実装してください。

必ず codex/app-rebuild-v1 ブランチを基準に作業し、最初に以下を読んでください。
- CODEX_APP_REBUILD_SPEC.md
- docs/RESEARCH_BASELINE_2026-08.md
- Issue #1

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
```

## Phase 1後

Phase 1の監査結果を確認してから、Phase 2で以下へ進む。

- Next.js / TypeScript App Shell
- PCサイドバー（通常 / アイコンのみ / 非表示）
- スマホ下部ナビ
- 武将画像カード + プレースホルダー
- 名前検索
- S1〜S4シーズン切替

Phase 2以降も、UIだけを完成させて戦闘計算をダミーのまま最終完成扱いしない。
