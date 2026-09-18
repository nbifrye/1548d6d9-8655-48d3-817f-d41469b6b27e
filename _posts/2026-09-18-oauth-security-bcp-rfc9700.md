---
layout: post
title: "OAuth 2.0 Security BCP (RFC 9700) を実装レビューの基準にする"
date: 2026-09-18 09:10:00 +0900
categories: [authorization, oauth]
---

OAuth 2.0 のセキュリティを評価するとき、RFC 6749 だけを見るのは不十分です。2025年1月公開の **RFC 9700 / BCP 240** は、OAuth 2.0 の運用経験を踏まえて現行のセキュリティ実務をまとめ、RFC 6749、6750、6819 を更新します。

## PKCE
RFC 9700 は public client に PKCE を要求し、confidential client にも PKCE を推奨します。「PKCE はネイティブアプリ専用」という理解は現在の基準では狭すぎます。

レビューでは、code verifier がトランザクション固有であること、redirect URI の照合、authorization code の注入・盗用対策まで確認します。

## Token replay
Bearer token は盗まれれば第三者が使える可能性があります。RFC 9700 は sender-constrained access token の利用を推奨し、代表例として mTLS (RFC 8705) と DPoP (RFC 9449) を挙げます。

JWT 形式であること自体は sender constraint ではありません。token の完全性と「誰が提示できるか」は別の性質です。

## Client authentication
実現可能なら client authentication を強制し、private_key_jwt や mTLS など非対称暗号を使う方式が推奨されます。

## 参照
- https://www.rfc-editor.org/rfc/rfc9700.html
- https://www.rfc-editor.org/rfc/rfc7636.html
- https://www.rfc-editor.org/rfc/rfc9449.html
- https://www.rfc-editor.org/rfc/rfc8705.html

最終確認: 2026-09-18
