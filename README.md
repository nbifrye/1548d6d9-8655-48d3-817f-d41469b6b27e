# Identity & Access Standards Notes

デジタルアイデンティティ、認証、認可、API セキュリティ、identity provisioning に関する標準仕様を、一次資料に基づいて日本語で整理するブログです。

## Editorial principles

- 技術的事実の根拠には、IETF / RFC Editor、OpenID Foundation、W3C、OASIS など仕様策定主体の一次資料を使用する
- 二次資料、ベンダーブログ、ニュース記事、個人ブログを、標準仕様上の事実を確定する根拠として使用しない
- RFC / BCP / Recommendation / Final Specification / Draft などの文書ステータスと発行日を明記する
- 筆者独自の推奨、評価、見解、予測を記事へ追加しない
- MUST / MUST NOT / SHOULD / SHOULD NOT / MAY 等の規範語は原文の強度を変更せず、参照 section を示す
- protocol / ceremony / resource lifecycle など処理順序がある記事には、仕様本文に沿った Mermaid 図を掲載する
- request / response、data structure、validation、error processing、security / privacy considerations を一次資料に沿って記載する
- 公開前に日本語を校正し、直訳調や主体の不明確な文を残さない
- 仕様更新時は既存記事も再確認し、一次資料と整合しない記述を修正する

詳細な編集・品質基準は [OPERATIONS.md](./OPERATIONS.md) を参照してください。

## Publishing

GitHub Pages / Jekyll 向けの構成です。`.github/workflows/pages.yml` が `main` への push をビルド・デプロイします。初回のみ Settings → Pages → Build and deployment → Source で `GitHub Actions` を選択してください。

> GitHub Pages は private repository をソースにしても公開サイトになる場合があります。機密情報は置かないでください。

## Scope

OAuth / OpenID Connect / FAPI / WebAuthn / SCIM / SAML / JOSE / DPoP / mTLS / RAR / identity assurance / access control など。
