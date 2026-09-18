---
layout: post
title: "WebAuthn Level 3 が W3C Recommendation に：まず何を理解すべきか"
date: 2026-09-18 09:00:00 +0900
categories: [authentication, webauthn]
---

Web Authentication (WebAuthn) Level 3 は、2026年8月25日に **W3C Recommendation** になりました。中心にあるのは「パスキー」という製品用語ではなく、Web アプリケーションが公開鍵クレデンシャルを作成・利用し、ユーザーを強く認証するための API とデータモデルです。

## 何を標準化するのか
Relying Party (RP) は User Agent を介して Authenticator に処理を依頼します。Authenticator はユーザーの同意のもとで鍵を扱い、秘密鍵そのものを RP へ送らずに署名を生成します。クレデンシャルは RP にスコープされます。

## 実装時に分けて考える層
1. WebAuthn API と credential model
2. Authenticator の鍵生成・署名・user verification
3. 登録・復旧・複数端末などの credential lifecycle
4. OIDC 等で認証結果を別システムへ伝える federation

WebAuthn を採用しても、account recovery や authorization が自動的に安全になるわけではありません。

## レビュー項目
- challenge をトランザクションごとに生成・結合する
- RP ID と origin の期待値を明示する
- user verification の要否をユースケースごとに定義する
- attestation を求める場合は信頼モデルとプライバシー影響を説明できるようにする
- account recovery を WebAuthn より弱い経路に落とさない

## 参照
- https://www.w3.org/TR/webauthn-3/
- https://www.w3.org/news/2026/web-authentication-an-api-for-accessing-public-key-credentials-level-3-is-now-a-w3c-recommendation/

最終確認: 2026-09-18
