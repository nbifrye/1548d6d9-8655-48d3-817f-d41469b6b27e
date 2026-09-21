---
layout: post
title: "OAuth 2.0 Implicit Grant：RFC 6749 の response_type=token と RFC 9700 の SHOULD NOT"
date: 2026-09-22 04:40:00 +0900
categories: [authorization, oauth]
---

## この記事について

**記事タイプ:** Version Difference / Security Practice  
**対象読者:** OAuth 2.0 の既存実装や仕様書で Implicit Grant（`response_type=token`）を確認する開発者・レビュー担当者  
**この記事で伝えること:** RFC 6749 が定義する Implicit Grant の Authorization Request / Access Token Response と、RFC 9700 が現在の Best Current Practice として示す `SHOULD NOT` の要件  
**扱わないこと:** Authorization Code Grant の詳細、PKCE の処理、OpenID Connect の response type、Implicit Grant からの移行設計

## Article brief

- **Reader:** Implicit Grant を含む OAuth 2.0 実装・仕様書を確認する開発者・レビュー担当者
- **Question:** RFC 6749 の Implicit Grant は Access Token をどのように返し、RFC 9700 ではその利用がどの規範強度で扱われているか
- **Answer:** `response_type=token` の request と URI fragment の Access Token response を説明し、RFC 9700 §2.1.2 の `SHOULD NOT` と例外条件を原文の強度のまま区別できる
- **Scope:** RFC 6749 §4.2–§4.2.2、RFC 9700 §2.1.2
- **Out of scope:** Authorization Code Grant / PKCE の詳細、OIDC 固有 response type、移行方式の選定、個別 deployment の判断
- **Primary sources:** RFC 6749 §4.2–§4.2.2、RFC 9700 §2.1.2
- **Diagram:** Authorization Endpoint への request と redirect URI fragment による Access Token delivery

## 1. RFC 6749 が定義する Implicit Grant

RFC 6749 §4.2 は、Implicit Grant を Access Token を取得するための grant type として定義しています。この flow では Authorization Code を発行して Token Endpoint で交換するのではなく、Authorization Request の結果として Access Token が Client に返されます。また、RFC 6749 §4.2 は Implicit Grant が Refresh Token の発行をサポートしないと規定しています。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant UA as User-Agent
    participant AS as Authorization Server
    C->>UA: Authorization Request
    UA->>AS: response_type=token
    AS-->>UA: Redirect with URI fragment
    UA-->>C: Access Token response
</pre>

この図は RFC 6749 §4.2 の関係を簡略化した**非規範的な図**です。

## 2. Authorization Request の parameter 配置

RFC 6749 §4.2.1 では、Client は Authorization Endpoint URI の query component に `application/x-www-form-urlencoded` 形式で parameter を追加します。

- `response_type`: REQUIRED。値は `token` でなければなりません（MUST）。
- `client_id`: REQUIRED。
- `redirect_uri`: OPTIONAL。
- `scope`: OPTIONAL。
- `state`: RECOMMENDED。request と callback の間で state を維持するための opaque value です。

次は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /authorize?response_type=token&client_id=illustrative-client&redirect_uri=https%3A%2F%2Fclient.example%2Fcallback&scope=read&state=illustrative-state HTTP/1.1
Host: authorization.example
```

RFC 6749 §4.2.1 は、Authorization Server が Access Token の送信先となる redirection URI と Client に登録された redirection URI が一致することを検証しなければならないと規定しています（MUST）。

## 3. Access Token は redirect URI の fragment に配置される

Resource Owner が access request を許可した場合、RFC 6749 §4.2.2 は Authorization Server が Access Token を発行し、redirect URI の **fragment component** に `application/x-www-form-urlencoded` 形式で response parameter を追加すると規定しています。

- `access_token`: REQUIRED。
- `token_type`: REQUIRED。
- `expires_in`: RECOMMENDED。
- `scope`: request された scope と同一なら OPTIONAL、異なる場合は REQUIRED。
- `state`: Authorization Request に `state` が含まれていた場合は REQUIRED。Client から受け取った値をそのまま返します。

次は response parameter の配置を示すための**非規範的な例**です。Access Token を含む値は illustrative value です。

```http
HTTP/1.1 302 Found
Location: https://client.example/callback#access_token=illustrative-access-token&token_type=Bearer&expires_in=3600&state=illustrative-state
```

RFC 6749 §4.2.2 では、Authorization Server は HTTP `Location` header の fragment を直接 Client に送るのではなく、User-Agent を Client の redirection endpoint へ向けます。その後、User-Agent は fragment の情報を Client に渡します。

## 4. RFC 9700 §2.1.2 の現在の要件

RFC 9700 §2.1.2 は、Implicit Grant（`response_type=token`）および Authorization Response で Access Token を発行するその他の response type について、Access Token leakage と replay のリスクを説明しています。

そのうえで Client は、Authorization Response への Access Token injection が防止され、かつ RFC 9700 が挙げる token leakage vector が緩和されている場合を除き、Implicit Grant または Authorization Response で Access Token を発行するその他の response type を使用すべきではないと規定しています（**SHOULD NOT**, RFC 9700 §2.1.2）。

RFC 9700 §2.1.2 は続けて、Client は代わりに `response_type=code`、または Access Token を Token Response で発行する response type を使用すべきと規定しています（**SHOULD**, RFC 9700 §2.1.2）。

**RFC 9700 says SHOULD NOT, not MUST NOT, and states the conditions attached to that requirement.**  
（RFC 9700 の規範語は MUST NOT ではなく SHOULD NOT であり、その要件には仕様本文で条件が示されています。）

## 5. RFC 6749 と RFC 9700 を区別して読む

RFC 6749 §4.2–§4.2.2 は Implicit Grant の wire-level protocol を定義しています。一方、RFC 9700 §2.1.2 は、その flow を現在の Best Current Practice でどのように扱うかを規定しています。

この記事では、RFC 9700 の `SHOULD NOT` を `MUST NOT` に読み替えません。また、例外条件を満たすかどうかは個別 deployment の事実関係に依存するため、一方の設計を独自に推奨しません。

## Primary sources

- RFC 6749, §4.2–§4.2.2, *The OAuth 2.0 Authorization Framework*: https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 9700, §2.1.2, *Best Current Practice for OAuth 2.0 Security*: https://www.rfc-editor.org/rfc/rfc9700.html
