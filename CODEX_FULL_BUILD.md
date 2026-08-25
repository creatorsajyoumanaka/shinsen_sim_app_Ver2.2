# Codex Full Build — 一気通し実装モード

## 目的

このリポジトリの再構築を、Issue #1〜#5を個別に止めながら進めるのではなく、**1回のCodex作業セッション内で可能な限り連続して最後まで進める**ための統合指示書。

ただし「一気にやる」=「全部を1コミットに詰める」ではない。
内部ではフェーズごとに小さく安全に進め、検証を挟み、壊れた状態を放置せず次へ進む。

作業ブランチ:
`codex/app-rebuild-v1`

`main` の既存Streamlit版は削除・破壊しない。

---

# 実行方針

Codexは最初に以下を全て読む。

- `CODEX_APP_REBUILD_SPEC.md`
- `CODEX_START_HERE.md`
- `docs/RESEARCH_BASELINE_2026-08.md`
- `docs/BATTLE_OPENING_PHASE_SPEC.md`
- `docs/LOCAL_PERSISTENCE_AND_GACHA.md`
- `docs/CODEX_PHASE2_PERSISTENCE_GACHA.md`
- `docs/BATTLE_LOSS_GRAPH_SPEC.md`
- `docs/MASTER_DATA_AND_COMMUNITY_SHARING.md`
- Issue #1〜#5

その後、原則としてユーザー確認待ちで停止せず、明確な実装判断は自律的に行い、以下を順番に連続実装する。

---

# Phase 1 — 全武将 / 戦闘式監査

- S1/S2/S3/PK(S4)全武将監査
- 重複/欠損/表記揺れ
- seasonAdded付与方針
- 旧戦闘式の由来分類
  - confirmed_nobunaga
  - measured_hypothesis
  - legacy_sangokushi
  - unknown_origin
- `docs/data_audit.md`
- `docs/battle_engine_audit.md`
- audit script実行

ここで停止せずPhase 1.5へ進む。

---

# Phase 1.5 — Opening Phase監査

ターン1前の処理を明確に分離。

対象:
- 凸/特性
- 家門バフ
- 軍学
- 兵種戦法
- 受動
- 指揮

要件:
- 0T snapshot
- 適用前/適用後ステータス
- stack rule
- provenance
- 兵種不一致理由
- 軍学Lv5ターン効果は通常ターン処理へ分離

ここで停止せずPhase 2へ進む。

---

# Phase 2 — 新Webアプリ土台

Next.js + TypeScript + App Router。

必須:
- PCサイドバー3段階
- スマホ下部ナビ
- ホーム
- 編成
- シミュレータ
- 所持管理
- 武将DB
- 戦法DB
- ガチャ履歴
- 設定

武将選択:
- 画像カード
- プレースホルダー
- 名前検索
- S1〜S4フィルタ
- grid/list切替

ここで停止せず永続化へ進む。

---

# Phase 2.5 — 永続保存 + ガチャ履歴

IndexedDB:
- 所持武将
- 凸
- 所持戦法
- 保存編成
- ガチャバナー
- ガチャイベント
- 設定
- schema version

必須:
- リロードしても消えない
- ブラウザ再起動でも残る
- サイトデータ削除時は消える
- JSON export/import

ガチャ:
- バナーCRUD
- +1
- 星5記録
- 1つ戻る
- 30回天井
- 星5率
- バナー別履歴
- 武将画像/名前検索から星5選択

ここで停止せずPhase 3へ進む。

---

# Phase 3 — 戦闘snapshot + 兵損グラフ

- 0T〜最大8T
- 自軍/敵軍残存兵力
- ターン別兵損
- 累計兵損
- ダメージ
- 回復
- 武将別
- 主要戦法イベント
- 1/100/1000回
- 平均推移
- 将来25〜75%レンジ

可視化層は計算モデルと分離。
保存済みsnapshotから再計算なしで再表示可能にする。

ここで停止せずPhase 4へ進む。

---

# Phase 4 — マスター更新簡略化 + 編成共有

- stable ID
- manifest/dataVersion/schemaVersion
- CSV/JSON import
- validation
- duplicate detection
- missing reference detection
- 新武将/新戦法追加でUIコード変更不要
- master更新でユーザーデータ保持

編成共有:
- URL/共有コード
- read-only preview
- 自分の保存編成へコピー
- シミュレータへ送る
- 対策編成検索へ送れる構造

将来CommunityFormation schemaも作る。
公開投稿バックエンドは初回完成の必須条件にはしない。

---

# Phase 5 — 戦闘エンジン統合

UIだけ完成して戦闘がダミーの状態を禁止。

旧Python版をgolden referenceとして残し、新実装と比較できるようにする。

最低限:
- opening phase
- 行動順
- 通常攻撃
- 能動
- 突撃
- 指揮
- 受動
- 兵種
- 状態異常
- 回復
- 兵種相性
- 与/被ダメ補正
- 会心/奇策
- 乱数
- 丸め
- 1〜8T

計算モデル:
- legacy_sangokushi
- nobunaga_calibrated
- experimental

信長真戦実測値を優先的に検証し、未確認係数を公式扱いしない。

---

# Phase 6 — 仕上げ

- lint
- typecheck
- tests
- build
- 主要ページのレスポンシブ確認
- 画像欠損耐性
- IndexedDB migration確認
- import/export確認
- 保存編成確認
- ガチャ履歴確認
- 兵損グラフ確認
- 旧Streamlit版が残っていること確認

READMEを更新する。

---

# Codexの停止ルール

以下の場合のみ止まってよい。

1. 既存データを破壊する可能性が高い
2. 権利不明の画像を勝手に大量取得する必要がある
3. 公式仕様と実測が矛盾し、勝手な確定が危険
4. ビルド/テスト失敗が解消できず追加情報が必要
5. GitHub権限/環境上の問題で継続不能

それ以外は、TODOだけ残して停止せず、可能な範囲を先へ進める。

---

# コミット方針

一気通しでもコミットは小さく分ける。

例:
- audit: add data and battle formula reports
- engine: isolate opening phase
- web: add app shell and navigation
- data: add general search and season filters
- storage: add IndexedDB repositories
- gacha: add history and pity tracking
- charts: add battle snapshot and troop-loss graph
- sharing: add formation URL serialization
- master: add import/validation pipeline
- test: add golden and regression tests

---

# 最終Acceptance Criteria

- S1〜S4武将監査完了
- 新武将追加が簡単
- 画像付き武将検索
- 編成保存
- 所持管理
- ガチャ履歴
- JSONバックアップ
- Opening Phase 0T
- 軍学/家門/兵種/凸/指揮受動処理
- 1/100/1000回シミュレーション
- 兵損/回復/残存兵力グラフ
- URL編成共有
- スマホ/PC対応
- 旧Streamlit版保持
- lint/typecheck/test/build成功

## Codexへの実行文

```text
CODEX_FULL_BUILD.md を最優先の統合指示として読み、Issue #1〜#5を1回の作業フローとして連続実装してください。
途中で各Issueの完了報告だけして停止せず、次Phaseへ進んでください。
ただし安全のためコミットはフェーズごとに分け、各段階でlint/typecheck/test/build等の実行可能な検証を行ってください。
既存Streamlit版と既存master IDを壊さず、戦闘式の未確認値を公式確定値として扱わないでください。
可能な限り最終Acceptance Criteriaまで一気に到達してください。
```
