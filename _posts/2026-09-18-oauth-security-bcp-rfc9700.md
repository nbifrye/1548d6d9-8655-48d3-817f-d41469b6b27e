---
layout: post
title: "RFC 9700：Authorization Code Grant を実装する際のセキュリティ要件"
date: 2026-09-18 09:10:00 +0900
categories: [authorization, oauth]
---

RFC 9700 **Best Current Practice for OAuth 2.0 Security** は、2025年1月に公開された BCP 240 です。

## この記事について

**記事タイプ:** Security Practice / Requirement  
**対象読者:** OAuth 2.0 の Authorization Code Grant を実装・レビューする Client / Authorization Server 開発者  
**この記事で伝えること:** RFC 9700 が Authorization Code Grant に対して追加・更新しているセキュリティ要件  
**扱わないこと:** Refresh Token の保護、Resource Owner Password Credentials Grant、sender-constrained access token、Authorization Server Metadata の詳細

この記事では RFC 9700 全体を要約しません。**Authorization Request から Token Request までの Authorization Code Grant** に範囲を限定し、redirect URI、CSRF、authorization code injection、PKCE に関する規範要件を整理します。

## 1. 対象となるフロー

<pre class="mermaid">
sequenceDiagram
    participant UA as User Agent
    participant C as Client
    participant AS as Authorization Server
    C->>C: transaction-specific security values を生成
    C->>UA: Authorization Request
    UA->>AS: Authorization Request
    AS->>AS: redirect_uri 等を検証
    AS-->>UA: Authorization Response + code
    UA-->>C: redirect
    C->>C: response を検証
    C->>AS: Token Request + code + code_verifier
    AS->>AS: code / redirect_uri / PKCE を検証
    AS-->>C: Access Token
</pre>

RFC 9700 §2.1 と §2.1.1 は、このフローに対して Client と Authorization Server の双方に要件を追加しています。

## 2. Redirect URI は exact string matching

RFC 9700 §2.1 は、Authorization Server が事前登録済み redirect URI とリクエストの redirect URI を比較する場合、native application の `localhost` redirect URI における port 番号を除き、**exact string matching を MUST としています**。

§4.1 は、不十分な redirect URI validation により、Authorization Server が authorization response を攻撃者が制御する URI へ送信し得る攻撃を説明しています。

この要件の対象は Authorization Server による redirect URI の検証です。

## 3. Client は CSRF を防止しなければならない

RFC 9700 §2.1 は、Client が CSRF を防止することを MUST としています。

Authorization Server が PKCE をサポートしていることを Client が確認できる場合、Client は PKCE が提供する CSRF protection に依存してもよいと規定されています。OpenID Connect flow では `nonce` parameter も CSRF protection を提供します。これらを使用しない場合は、User Agent に安全に結び付けた one-time use の CSRF token を `state` parameter で使用しなければなりません（MUST）。

PKCE challenge または OpenID Connect の `nonce` を transaction binding に利用する場合、その値は transaction-specific であり、Client とフローを開始した User Agent に安全に結び付けられていなければなりません。

## 4. Authorization Code Injection を防止する

RFC 9700 §2.1.1 は、Authorization Code Grant を利用する Client が authorization code injection attack と authorization code misuse を防止することを MUST としています。

Public Client は PKCE を使用しなければなりません（MUST）。Confidential Client に対しても PKCE は RECOMMENDED です。追加の対策を満たす Confidential OpenID Connect Client は、代わりに `nonce` parameter と ID Token の対応する Claim を使用してもよい（MAY）とされています。

RFC 9700 は、PKCE に関するこの推奨が native application に限定されず、Web application を含むすべての種類の OAuth Client に適用されると明記しています。

## 5. PKCE の処理

PKCE では Client が `code_verifier` を生成し、そこから `code_challenge` を導出します。Authorization Server は Authorization Request の `code_challenge` を authorization transaction と結び付け、Token Request で受け取る `code_verifier` を検証します。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    C->>C: code_verifier を生成
    C->>C: code_challenge = S256(code_verifier)
    C->>AS: Authorization Request + code_challenge + code_challenge_method=S256
    AS->>AS: code_challenge を transaction に結合
    AS-->>C: authorization code
    C->>AS: Token Request + code + code_verifier
    AS->>AS: verifier から challenge を再計算して照合
    AS-->>C: Access Token
</pre>

RFC 9700 §2.1.1 は、PKCE を使う Client が、Authorization Request で verifier を露出しない challenge method を使用することを SHOULD としています。RFC 9700 公開時点では `S256` がその条件を満たす唯一の方式です。

Authorization Server は PKCE をサポートしなければならず（MUST）、Client が PKCE 対応を検出できる手段も提供しなければなりません（MUST）。

## 6. PKCE downgrade を防止する

RFC 9700 §4.8.2 は PKCE downgrade attack を扱っています。

Authorization Server は、Authorization Request に code challenge が含まれていたかどうかを authorization code と結び付けます。code challenge が存在した場合、Token Request には有効な code verifier が必要です。

また、Authorization Request に code challenge が存在しなかったにもかかわらず Token Request に code verifier が含まれている場合、Authorization Server はその Token Request を拒否しなければなりません（MUST）。

<pre class="mermaid">
flowchart TD
    A[Token Request] --> B{Authorization Request に code_challenge があったか}
    B -->|Yes| C{code_verifier が有効か}
    C -->|Yes| D[Token processing を継続]
    C -->|No| E[拒否]
    B -->|No| F{code_verifier が送られたか}
    F -->|Yes| E
    F -->|No| G[PKCE を使わない transaction として処理]
</pre>

## 7. Authorization Code Grant に関する確認点

この記事の対象範囲にある規範要件は、次のように整理できます。

- **Redirect URI:** 原則として exact string matching を使用する（MUST）。
- **CSRF:** Client は CSRF を防止する（MUST）。
- **Authorization Code Injection:** Client は code injection / misuse を防止する（MUST）。
- **Public Client:** PKCE を使用する（MUST）。
- **Confidential Client:** PKCE の使用が RECOMMENDED。追加条件を満たす Confidential OpenID Connect Client は `nonce` を代替として使用できる（MAY）。
- **Authorization Server:** PKCE をサポートし（MUST）、Client が対応を検出できる手段を提供する（MUST）。
- **PKCE challenge method:** verifier を Authorization Request で露出しない方式を使用する（SHOULD）。
- **PKCE downgrade:** challenge の有無を transaction に結び付け、不整合な Token Request を拒否する。

## 8. この記事で扱っていない RFC 9700 の主題

RFC 9700 には、このほかにも次の主題があります。

- access token replay と sender-constrained token
- refresh token protection
- Resource Owner Password Credentials Grant
- Client Authentication
- Authorization Server Metadata
- open redirector
- mix-up attack
- token leakage

これらは Authorization Code Grant の request / code exchange に直接焦点を当てたこの記事の範囲外です。

## 9. 一次資料

- RFC Editor: [RFC 9700 — Best Current Practice for OAuth 2.0 Security](https://www.rfc-editor.org/rfc/rfc9700.html)
- RFC Editor: [RFC 7636 — Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636.html)

参照した主要節: RFC 9700 §2.1, §2.1.1, §4.1, §4.8.2  
最終確認: 2026-09-19
