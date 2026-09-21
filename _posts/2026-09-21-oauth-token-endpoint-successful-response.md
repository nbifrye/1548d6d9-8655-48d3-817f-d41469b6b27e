---
layout: post
title: "RFC 6749：Token Endpoint の successful response を読む"
date: 2026-09-21 22:44:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 Token Endpoint の成功 response を実装・レビューする開発者  
**この記事で伝えること:** RFC 6749 §5.1 が定義する successful response の HTTP status、JSON member、scope の条件、cache 制御、未知 member の処理を理解する  
**扱わないこと:** 各 grant の request / validation、Token Endpoint の error response、Access Token の内部形式、Bearer Token の Protected Resource への提示、OpenID Connect 固有 response

## Article brief

- **Reader:** OAuth 2.0 Token Endpoint の成功 response を実装・レビューする開発者
- **Question:** Access Token 発行成功時、Authorization Server は HTTP response のどこに何を返し、Client はその response をどう扱うのか
- **Answer:** `200 OK`、JSON top-level member の `access_token` / `token_type` / `expires_in` / `refresh_token` / `scope`、`scope` が必須になる条件、`Cache-Control` / `Pragma`、未知 member の扱いを説明できる
- **Scope:** RFC 6749 §5.1 の Successful Response
- **Out of scope:** RFC 6749 §5.2 の Error Response、個別 grant の request と validation、token type 固有 semantics、Access Token の構造、OpenID Connect
- **Primary sources:** RFC 6749 §5.1
- **Diagram:** Authorization Server が成功 response を構成し、Client が既知 member を処理して未知 member を無視する関係

## 1. successful response は 200 OK の JSON body で返す

RFC 6749 §5.1 では、Access Token request が valid かつ authorized である場合、Authorization Server は Access Token と、発行する場合は Refresh Token を返します。response は HTTP `200 OK` で、parameter は `application/json` の response entity-body に置かれ、各 parameter は JSON object の最上位 member として表現されます。

主な member は次のとおりです。

- **`access_token`:** REQUIRED。Authorization Server が発行した Access Token。
- **`token_type`:** REQUIRED。発行された token の type。値は case-insensitive。
- **`expires_in`:** RECOMMENDED。Access Token の lifetime を秒数で表す JSON number。省略する場合、Authorization Server は expiration time を別の手段で提供するか default value を文書化すべきです（SHOULD, §5.1）。
- **`refresh_token`:** OPTIONAL。発行される場合の Refresh Token。
- **`scope`:** Client が要求した scope と同一なら OPTIONAL、異なる場合は REQUIRED（§5.1）。

次は配置と最小構造を示す**非規範的な例**です。token 値と lifetime は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "access_token": "access-token-example",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read"
}
```

`access_token`、`token_type`、`scope` は JSON string、`expires_in` は JSON number です。member の順序に規範的な意味はありません。

## 2. scope が request と異なる場合は response に含める

RFC 6749 §5.1 は `scope` を常に OPTIONAL としているわけではありません。発行された Access Token の scope が Client の request と同一なら `scope` は OPTIONAL ですが、異なる場合は REQUIRED です。

この要件により、Client は response に `scope` がある場合、実際に発行された Access Token の scope を response から確認できます。どの scope を認可するかという Authorization Server の policy 自体は、この記事の対象外です。

## 3. token を含む response には cache 制御 header が必要

RFC 6749 §5.1 は、token、credential、その他の sensitive information を含む response について、Authorization Server が次の response header を含めなければならない（MUST）と定めています。

- `Cache-Control: no-store`
- `Pragma: no-cache`

これらは JSON member ではなく HTTP response header です。

## 4. Client は未知の response member を無視する

RFC 6749 §5.1 では、Client は認識しない response value name を無視しなければなりません（MUST）。また、token その他の値のサイズは仕様で定義されていません。Client は値のサイズについて仮定することを避けるべきであり、Authorization Server は自身が発行する値のサイズを文書化すべきです（SHOULD, §5.1）。

<pre class="mermaid">
flowchart TD
    A[Authorization Server が Access Token を発行]
    A --> B[200 OK の JSON response を構成]
    B --> C[Cache-Control: no-store と Pragma: no-cache]
    C --> D[Client が response を受信]
    D --> E[既知 member を処理]
    D --> F[未知 member を無視]
</pre>

この図は RFC 6749 §5.1 の response processing を示す**非規範的な要約**です。

## 5. 個別 grant の要件とは分けて読む

§5.1 は Token Endpoint の successful response に共通する response structure を定義します。一方、Refresh Token を発行できるか、または発行すべきでないかといった条件は grant ごとの規定にも依存します。たとえば Client Credentials Grant の Refresh Token については §4.4.3 に別の規定があります。

この記事では §5.1 の共通 response structure のみを扱い、各 grant の request / validation や grant 固有の発行条件は扱いません。

## 一次資料

- RFC 6749, *The OAuth 2.0 Authorization Framework*, §5.1  
  https://www.rfc-editor.org/rfc/rfc6749.html

最終確認日: 2026-09-21
