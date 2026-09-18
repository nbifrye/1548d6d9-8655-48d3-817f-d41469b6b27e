---
layout: post
title: "RFC 9700：OAuth 2.0 Security Best Current Practice の要件と処理フロー"
date: 2026-09-18 09:10:00 +0900
categories: [authorization, oauth]
---

RFC 9700 **Best Current Practice for OAuth 2.0 Security** は、2025年1月に RFC Editor から公開された BCP 240 です。OAuth 2.0 の既知の攻撃、実装上の弱点、および対策を整理し、RFC 6749、RFC 6750、RFC 6819 を更新します。

この記事では RFC 9700 の規範的な記述を、Authorization Code Grant を中心に整理します。MUST / SHOULD / MAY などの規範語は RFC 9700 の強度を維持して記載します。

## 1. RFC 9700 の位置づけ

RFC 9700 §1 は、OAuth 2.0 が API protection や OpenID Connect の基盤として広く使われる一方、既知の implementation weakness や anti-pattern が引き続き悪用されていること、高いセキュリティ要件を持つ環境で利用されていること、当初想定より動的な構成で利用されていることを背景として挙げています。

§2 は OAuth 実装者向けの主要な Best Practices、§3 は更新された attacker model、§4 は具体的な攻撃と対策を定義しています。

## 2. Authorization Code Grant の基本フロー

RFC 9700 は Authorization Code Grant に対して、redirect URI の厳密な照合、authorization code injection の防止、CSRF 対策、PKCE などの要件を規定します。

<pre class="mermaid">
sequenceDiagram
    participant U as User Agent
    participant C as Client
    participant AS as Authorization Server
    participant RS as Resource Server
    C->>C: transaction-specific state / PKCE 情報を生成
    C->>U: authorization request
    U->>AS: authorization request
    AS->>AS: redirect_uri 等を検証し Resource Owner を認証
    AS-->>U: authorization response + code
    U-->>C: redirect to client
    C->>C: issuer / state / code 等を検証
    C->>AS: token request + code + code_verifier + client authentication(該当時)
    AS->>AS: code / redirect_uri / PKCE / client binding を検証
    AS-->>C: access token / optional refresh token
    C->>RS: access token
    RS-->>C: protected resource
</pre>

## 3. Redirect URI の照合

RFC 9700 §2.1 は、Authorization Server が事前登録済み redirect URI とリクエストの redirect URI を比較する場合、native application の `localhost` redirect URI における port 番号を除き、**exact string matching を MUST としています**。

この要件は、authorization code または access token の漏えいを防ぐ対策として記載されています。§4.1 は、不十分な redirect URI validation によって Authorization Server が攻撃者管理 URI へ authorization response を送信する攻撃を説明しています。

## 4. CSRF と authorization code injection

RFC 9700 §2.1 は、Client に CSRF の防止を MUST としています。Authorization Server が PKCE をサポートしていることを Client が確認できている場合、Client は PKCE が提供する CSRF protection に依存してもよいと規定されています。

Authorization Code Grant について §2.1.1 は、Client が authorization code injection attack と authorization code misuse を防止することを MUST としています。

Public Client については PKCE の利用が MUST です。Confidential Client については PKCE が RECOMMENDED です。RFC 9700 は、この助言が native application だけでなく Web application を含むすべての種類の OAuth Client に適用されると明記しています。

PKCE challenge または OpenID Connect の `nonce` をこの目的に使う場合、その値は transaction-specific であり、Client とフローを開始した User Agent に安全に結び付けられていなければなりません。

## 5. PKCE の処理

PKCE では Client が authorization request の前に `code_verifier` を生成し、そこから `code_challenge` を導出します。Authorization Server は authorization request と authorization code の間で `code_challenge` を結び付け、token request の `code_verifier` を検証します。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    C->>C: code_verifier を生成
    C->>C: code_challenge = S256(code_verifier)
    C->>AS: Authorization Request + code_challenge + code_challenge_method=S256
    AS->>AS: code_challenge を authorization transaction に結合
    AS-->>C: authorization code
    C->>AS: Token Request + code + code_verifier
    AS->>AS: code_verifier から challenge を再計算して照合
    AS-->>C: Access Token
</pre>

RFC 9700 §2.1.1 は、PKCE を使う Client が authorization request で verifier を露出しない challenge method を SHOULD use としています。RFC 公開時点では `S256` がその条件を満たす唯一の方式として記載されています。

§4.8.2 は PKCE downgrade attack への対策として、Authorization Server が PKCE 対応時に authorization request に code challenge が含まれていたかを code と結び付けること、code challenge が存在した場合には token request に有効な code verifier を要求することを説明しています。また、authorization request に code challenge が存在しなかったのに token request に code verifier が含まれる場合、その token request を拒否することを MUST としています。

## 6. Implicit Grant

RFC 9700 §2.1.2 は、Implicit Grant（`response_type=token`）および authorization response で access token を発行する response type が access token leakage と replay の影響を受けることを説明しています。

Client は、authorization response への access token injection が防止され、同節が挙げる leakage vector が緩和されている場合を除き、Implicit Grant を **SHOULD NOT use** とされています。代わりに `response_type=code` など、access token が token response で発行される方式を SHOULD use としています。

## 7. Access Token replay と sender-constrained token

RFC 9700 §2.2 および §4.10 は token replay prevention を扱います。§4.10 は、Authorization Server が access token を sender-constrained かつ audience-restricted にすることを SHOULD としています。

Sender-constrained access token は、特定の sender に token の利用可能性を制限します。RFC 9700 は OAuth Working Group で定義され、実運用されている方式として次の2つを挙げています。

| 方式 | RFC | RFC 9700 に記載された仕組み |
|---|---|---|
| Mutual TLS | RFC 8705 | TLS client certificate の public key と token を結び付け、Resource Server が証明書側の key と比較する |
| DPoP | RFC 9449 | 公開鍵・秘密鍵ペアと application-level signature により proof of possession を行う |

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant RS as Resource Server
    C->>AS: Token Request + proof of sender key
    AS->>AS: sender key と Access Token を結び付ける
    AS-->>C: sender-constrained Access Token
    C->>RS: Access Token + proof
    RS->>RS: token と proof の key binding を検証
    RS->>RS: proof replay が成立しないことを検証
    RS-->>C: Protected Resource
</pre>

RFC 9700 は、token と key material の両方を攻撃者が取得した場合、sender-constrained token のセキュリティが損なわれることも明記しています。

## 8. Refresh Token

RFC 9700 §2.2.2 は、Public Client に発行される refresh token について、sender-constrained とするか refresh token rotation を使用することを MUST としています。

§4.14.2 はさらに次を規定します。

- refresh token が発行される場合、resource owner が同意した scope と resource server に binding されなければならない（MUST）。
- Public Client では malicious actor による refresh token replay を検出するため、sender-constrained refresh token または refresh token rotation のいずれかを Authorization Server が使用しなければならない（MUST）。
- refresh token は Client が一定期間 inactive であった場合に expire することが SHOULD とされている。

Rotation では、Access Token refresh のたびに新しい refresh token を発行し、以前の token を無効化します。以前の token と新しい token の関係を Authorization Server が保持し、無効化済み refresh token が提示された場合に active refresh token を revoke できる方式として記載されています。

## 9. Resource Owner Password Credentials Grant

RFC 9700 §2.4 は、Resource Owner Password Credentials Grant を **MUST NOT be used** と規定しています。

同節は、この grant が resource owner の credential を Client に露出させること、credential が漏えいし得る場所を増やすこと、複数の user interaction step や two-factor authentication を伴う authentication process 向けに設計されていないことを理由として説明しています。

## 10. Client Authentication

RFC 9700 §2.5 は、Client credential の発行・登録プロセスを構築し、その confidentiality を確保できる deployment では、Authorization Server が Client Authentication を enforce することを SHOULD としています。

Client Authentication には asymmetric cryptography を利用する方式が RECOMMENDED であり、RFC 8705 の mutual TLS と、RFC 7521 / RFC 7523 および OpenID Connect で定義される `private_key_jwt` が例示されています。

## 11. Authorization Server Metadata

RFC 9700 §2.6 は、Authorization Server が RFC 8414 に従って OAuth Authorization Server Metadata を公開し、Client が利用可能な場合にその metadata で自身を構成することを RECOMMENDED としています。

## 12. 一次資料

- RFC Editor: [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)
- RFC Editor: [RFC 7636 — Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636.html)
- RFC Editor: [RFC 8705 — OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens](https://www.rfc-editor.org/rfc/rfc8705.html)
- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession](https://www.rfc-editor.org/rfc/rfc9449.html)
- RFC Editor: [RFC 8414 — OAuth 2.0 Authorization Server Metadata](https://www.rfc-editor.org/rfc/rfc8414.html)

参照した主要節: RFC 9700 §1, §2.1, §2.1.1, §2.1.2, §2.2, §2.2.2, §2.4, §2.5, §2.6, §4.1, §4.8.2, §4.10, §4.14  
最終確認: 2026-09-18
