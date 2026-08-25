# Branding / Creator Credit / Ad Slots

## 目的

Webアプリの使いやすさを壊さず、作者表示と将来の広告収益化を入れられる構造にする。

---

# 1. Creator Credit

右上ヘッダーに小さく作者名を常設する。

初期表示:

`Created by 沙条愛歌`

または日本語UIでは:

`制作：沙条愛歌`

要件:
- PCでは右上ヘッダー
- スマホではヘッダー右側またはメニュー内に省スペース表示
- ナビゲーションや主要操作より目立たせない
- 名前はハードコードせず `siteConfig.creatorName` などの設定から変更可能にする
- 将来、プロフィール/更新履歴/問い合わせページへリンク可能な構造にする

例:

```ts
export const siteConfig = {
  appName: "信長真戦シミュレーター",
  creatorName: "沙条愛歌",
}
```

---

# 2. 広告配置方針

広告は操作を邪魔しないことを最優先にする。

## 初期MVP

ページ下部に横長の広告枠を1つ用意する。

配置:
- メインコンテンツ終了後
- フッター直前
- スマホ下部ナビとは重ねない
- fixed/stickyで常時画面を塞がない

想定コンポーネント:

```tsx
<AdSlot placement="footer" />
```

広告未設定時は枠自体を非表示にし、無駄な空白を残さない。

---

# 3. Desktop Optional Ad

PCでは将来的に、画面幅に余裕がある場合のみ右側に小さな広告枠を表示できるようにする。

ただし以下では自動非表示:
- 狭い画面
- 編成編集など横幅が重要なページ
- シミュレーターの詳細グラフ表示時

広告のためにメインUIを極端に狭くしない。

---

# 4. Mobile

スマホは下部ナビがあるため、広告を画面最下部にfixed表示しない。

推奨:

```text
メインコンテンツ
↓
小さな広告枠
↓
フッター
↓
固定Bottom Navigation
```

広告がBottom Navigationや保存/実行ボタンを隠さないこと。

---

# 5. Ad Provider Abstraction

最初から特定広告会社へロジックを密結合しない。

```ts
type AdPlacement = "footer" | "desktop-rail"

interface AdConfig {
  enabled: boolean
  provider?: "adsense" | "custom"
  clientId?: string
  slots?: Partial<Record<AdPlacement, string>>
}
```

環境変数例:

```text
NEXT_PUBLIC_ADS_ENABLED=false
NEXT_PUBLIC_AD_PROVIDER=adsense
NEXT_PUBLIC_AD_CLIENT_ID=
NEXT_PUBLIC_AD_FOOTER_SLOT=
```

広告アカウント未作成でもアプリ本体は正常に動作すること。

---

# 6. Performance

- 広告スクリプトは広告有効時のみ読み込む
- レイアウトシフトをできるだけ抑える
- ページ初期操作を広告ロードでブロックしない
- 広告ロード失敗でアプリを壊さない

---

# 7. UX Rule

禁止:
- シミュレートボタンを押そうとして誤タップしやすい広告配置
- 武将選択カード間への大量広告
- モーダルを塞ぐ広告
- Bottom Navigationを覆う広告
- 兵損グラフの上に被せる広告

広告は「少し下側にある」程度を基本とする。

---

# 8. Acceptance Criteria

- [ ] 右上に `沙条愛歌` のcreator creditが表示される
- [ ] creator名はconfigから変更可能
- [ ] ページ下部に `AdSlot` の差し込み口がある
- [ ] 広告無効時は不要な空白を残さない
- [ ] スマホBottom Navigationと広告が重ならない
- [ ] 広告SDK未設定でもbuild/runtimeが壊れない
- [ ] 広告有効/無効を環境変数で切替可能
- [ ] 将来AdSense等を差し込めるprovider abstractionを持つ
