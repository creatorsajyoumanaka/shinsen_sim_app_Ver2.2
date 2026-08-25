# Codex Start Here

Codexにこのリポジトリを開かせたら、まず次の指示で開始してください。

```text
このリポジトリの Issue #1「Codex Phase 1: 全武将監査と戦闘式監査」を実装してください。

必ず codex/app-rebuild-v1 ブランチを基準に作業し、最初に以下を読んでください。
- CODEX_APP_REBUILD_SPEC.md
- docs/RESEARCH_BASELINE_2026-08.md
- docs/LOCAL_PERSISTENCE_AND_GACHA.md
- docs/CODEX_PHASE2_PERSISTENCE_GACHA.md
- docs/BATTLE_LOSS_GRAPH_SPEC.md
- docs/BATTLE_OPENING_PHASE_SPEC.md
- docs/MASTER_DATA_AND_COMMUNITY_SHARING.md
- Issue #1
- Issue #2
- Issue #3
- Issue #4
- Issue #5

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

Phase 1と並行または直後に、Issue #4「合戦開始バフ / 軍学 / 兵種戦法の処理順監査」を実施し、Opening Phaseの出力型を確定してください。
軍学・家門・兵種戦法・凸/特性・指揮/受動など、ターン1より前にかかる補正を明確に分離し、0T snapshotに保持してください。

Phase 1/1.5完了後は、Issue #2「Codex Phase 2: App Shell + 永続保存 + ガチャ履歴」を実装してください。
Phase 2では、Next.js App Shell、武将画像カード/名前検索、IndexedDB永続化、所持管理、保存編成、ガチャ履歴MVP、JSONバックアップ/復元までを対象にします。

Phase 2完了後は、Issue #3「Codex Phase 3: 兵損グラフ + 戦闘結果可視化」を実装してください。
Phase 3では、戦闘snapshotを基準に、残存兵力・ターン別兵損・累計兵損・回復・武将別推移をグラフ化します。
Opening Phaseの0T snapshotもグラフ/詳細から確認できるようにしてください。

Phase 3後または並行で、Issue #5「Codex Phase 4: マスター更新簡略化 + 編成共有/公開」を実装してください。
Phase 4では、今後の新シーズン追加時にコード変更を最小化するマスター更新基盤、CSV/JSON一括import、stable ID、保存編成のURL/共有コード化を実装します。
将来の公開編成ギャラリーはschemaまで先に用意し、初期MVPではURL共有を優先してください。

重要:
- グラフのデフォルトは自軍合計 vs 敵軍合計の2系列にする
- 武将別6系列はユーザーが必要なものだけON/OFFできるようにする
- 兵力差を単純にダメージ扱いせず、damageTaken / healingReceived / troopsEnd を分ける
- 1回/100回/1000回に対応し、100/1000回では平均推移を表示する
- PC hover / スマホ tap でターン詳細を確認できるようにする
- 主要戦法イベントと兵損/回復を同じターン情報から追えるようにする
- 保存済みシミュレーション結果から再計算なしでグラフ再表示できるsnapshot schemaにする
- 戦闘式が更新されてもグラフUIを作り直さなくて済むよう、可視化層を戦闘計算モデルから分離する
- 新武将追加のためにUIコードを毎回修正しない
- master更新でユーザーの所持/編成/ガチャ履歴を消さない
- 共有URLを開いただけで受信者のローカルデータを書き換えない
```

## Phase 1後

Phase 1の監査結果を確認し、Issue #4のOpening Phase監査を反映してからIssue #2に従ってPhase 2へ進む。

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

## Phase 2後

Issue #3に従ってPhase 3へ進む。

Phase 3主要項目:

- 開戦時0T〜最大8Tの残存兵力折れ線グラフ
- 自軍合計 vs 敵軍合計
- 残存兵力 / ターン別兵損 / 累計兵損 / 武将別 の表示切替
- ダメージ / 回復の分離集計
- 武将画像とグラフ系列の連動
- 武将別表示のON/OFF
- ターン詳細と主要戦法イベント
- 100回 / 1000回の平均兵力推移
- 将来的な25〜75%レンジ表示用schema
- 保存済みsim snapshotの再表示
- スマホレスポンシブ

## Phase 3後

Issue #5に従ってPhase 4へ進む。

Phase 4主要項目:

- versioned master data
- stable ID
- seasonAdded
- CSV/JSON import
- duplicate/missing reference validation
- 新武将/新戦法追加時のUIコード変更不要化
- 保存編成のURL/共有コード化
- read-only preview
- 自分の保存編成へコピー
- シミュレータへ送る
- 将来のCommunity Formation Gallery schema

Phase 2以降も、UIだけを完成させて戦闘計算をダミーのまま最終完成扱いしない。
