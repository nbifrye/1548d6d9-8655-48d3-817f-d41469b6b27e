---
layout: post
title: "RFC 7009：Token Revocation では何を送ると token が無効化されるのか"
date: 2026-09-19 11:38:00 +0900
categories: [oauth, token]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Client / Authorization Server で Token Revocation Endpoint を実装・レビューする開発者  
**この記事で伝えること:** Client が Revocation Endpoint に送る parameter、その配置、Authorization Server の検証と無効化、成功・error response の関係  
**扱わないこと:** Token Introspection、refresh token rotation、Resource Server が access token の失効を検知する方法、個別 deployment の revocation policy

## Article brief

- **Reader:** Token Revocation Endpoint を実装・レビューする OAuth 2.0 Client / Authorization Server の開発者
- **Question:** token を無効化するとき、Client は何をどこへ送り、Authorization Server は何を検証してどの response を返すのか
- **Answer:** RFC 7009 §2–§2.2.1 に基づき、revocation request の form parameter、client authentication、token の検証・無効化、HTTP 200 と error response を区別して説明できる
- **Scope:** RFC 7009 §2, §2.1, §2.2, §2.2.1
- **Out of scope:** RFC 7662 Token Introspection、RFC 9700 の refresh token replay detection、Resource Server への失効伝播方式、CORS / JSONP、deployment 固有の cascade policy
- **Primary sources:** RFC 7009 §2–§2.2.1
- **Diagram:** Client から Revocation Endpoint への POST、client/token 検証、token 無効化、response を縦方向の flowchart で示す

## 1. Revocation Endpoint の役割

RFC 7009 §2 は、Client が以前取得した token を無効化するための Token Revocation Endpoint を定義しています。

実装は refresh token の revocation をサポートしなければなりません（MUST）。access token の revocation もサポートすべきです（SHOULD）。Client は revocation endpoint URL が HTTPS URL であることを検証しなければなりません（MUST, §2）。

Endpoint の location をどのように取得するかは RFC 7009 の scope 外です。

## 2. Client は form parameter を POST body に入れる

RFC 7009 §2.1 では、revocation request は HTTP POST です。`token` と `token_type_hint` は JSON member や query parameter ではなく、`application/x-www-form-urlencoded` の request entity-body に入ります。

- **`token`:** REQUIRED。Client が revoke したい token。
- **`token_type_hint`:** OPTIONAL。token type の hint。RFC 7009 は `access_token` と `refresh_token` を定義しています。
- **Client authentication credentials:** RFC 6749 §2.3 に従って request に含めます。

次は構造を示すための非規範的な例です。

```http
POST /revoke HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <client-credentials>

token=REFRESH_TOKEN_VALUE&token_type_hint=refresh_token
```

この例で revoke 対象なのは POST body の `token` です。`Authorization` header は Client の authentication credentials を表しており、revoke 対象 token とは役割が異なります。

`token_type_hint` は lookup の最適化を助けるために Client が送ることができます（MAY）。Authorization Server が hint を使って token を見つけられない場合、サポートするすべての token type に検索を広げなければなりません（MUST）。Authorization Server は hint を無視することもできます（MAY, §2.1）。

## 3. Authorization Server は Client と token を検証する

RFC 7009 §2.1 では、Authorization Server は confidential client の場合に Client credentials を検証し、その後、token が revocation request を行った Client に発行されたものかを検証します。検証に失敗した場合、request を拒否して error を返します。

検証後、Authorization Server は token を無効化します。RFC 7009 は invalidation が直ちに行われ、revocation 後はその token を再利用できないと規定しています。

実際の distributed system では invalidation の propagation delay があり得ることも §2.1 が記載しています。実装はその window を最小化すべきであり、Client は HTTP 200 を受け取った後に token を使用してはなりません。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[POST revocation request]
    B --> C[Authorization Server]
    C --> D[Client credentials を検証]
    D --> E[token と Client の関係を検証]
    E --> F[token を無効化]
    F --> G[HTTP 200]
</pre>

## 4. 関連 token まで revoke されるかは一律ではない

RFC 7009 §2.1 では、ある token の revocation が関連 token や underlying authorization grant に及ぶかは Authorization Server の revocation policy に依存します。

対象が refresh token で、Authorization Server が access token revocation をサポートする場合、同じ authorization grant に基づく access token も無効化すべきです（SHOULD）。対象が access token の場合、対応する refresh token も revoke できます（MAY）。

したがって、RFC 7009 はすべての deployment に同一の cascade behavior を要求していません。

## 5. 成功と invalid token はどちらも HTTP 200 になり得る

RFC 7009 §2.2 では、token の revocation に成功した場合、または Client が invalid token を送った場合、Authorization Server は HTTP 200 を返します。

```http
HTTP/1.1 200 OK
```

Response body の内容は Client によって無視されます。必要な情報は response code で伝えられるためです。

invalid token が通常の error response にならないのは、Client が求めた「その token を無効な状態にする」という結果がすでに成立しているためです。

## 6. `unsupported_token_type` は別の error である

RFC 7009 §2.2.1 は Revocation Endpoint 固有の error code として `unsupported_token_type` を定義しています。これは Authorization Server が提示された token type の revocation をサポートしていない場合に使用します。

一方、単に `token_type_hint` の値が無効である場合、その hint は無視され、revocation response には影響しません（§2.2）。

HTTP 503 が返された場合、Client は token がまだ存在すると仮定しなければなりません。Server は `Retry-After` header を含めることができます（§2.2.1）。

## 一次資料

- RFC Editor: [RFC 7009 — OAuth 2.0 Token Revocation](https://www.rfc-editor.org/rfc/rfc7009.html)

参照した主要節: §2, §2.1, §2.2, §2.2.1  
最終確認: 2026-09-19
