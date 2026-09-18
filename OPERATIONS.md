# Blog Operations

このリポジトリは、デジタルアイデンティティとアクセスコントロールの標準仕様を継続的に解説するために運営します。

## Weekly editorial loop

1. IETF / RFC Editor、OpenID Foundation、W3C の一次資料を確認する
2. 新しい RFC / BCP / Final Specification / Recommendation を優先する
3. Draft は実装影響が大きい場合のみ扱い、「未確定」と明記する
4. 既存記事と重複しないテーマを選ぶ
5. 記事を `_posts/YYYY-MM-DD-slug.md` に追加する
6. 必要なら `standards.md` を更新する
7. 参照仕様と「最終確認日」を記事末尾に置く
8. main への push 後、GitHub Pages の build/deploy 結果を確認する

## Article quality gate

公開前に以下を満たすこと。

- 一次資料を少なくとも1件参照
- 仕様のステータスと日付を確認
- MUST / SHOULD / MAY を独自解釈で弱めない
- 「仕様の要求」と「筆者の推奨」を分ける
- token / assertion / credential / session 等の用語を混同しない
- deprecated / superseded な仕様を現行推奨として扱わない
- セキュリティ上の主張には threat model を添える
- ベンダー固有機能を標準仕様として説明しない

## Update policy

既存記事の仕様が更新された場合、記事冒頭または末尾に追記し、古い記述が誤解を招くなら本文も修正します。重大な変更は新記事として差分を解説します。

## Current editorial priorities

1. WebAuthn Level 3
2. OAuth 2.0 Security BCP / RFC 9700
3. FAPI 2.0 Security Profile
4. SCIM 2.0
5. DPoP / mTLS
6. Rich Authorization Requests
7. OpenID Connect Core and related profiles
8. Authorization models (ABAC / ReBAC) and policy interoperability
