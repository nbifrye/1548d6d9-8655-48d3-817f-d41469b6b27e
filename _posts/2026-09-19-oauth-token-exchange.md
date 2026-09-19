---
layout: post
title: "RFC 8693：Token Exchange では subject_token をどう新しい token に交換するのか"
date: 2026-09-19 19:41:00 +0900
categories: [oauth]
tags: [OAuth, RFC8693, Token Exchange]
---

RFC 8693 **OAuth 2.0 Token Exchange** は、Client が Authorization Server の Token Endpoint に security token を提示し、別の security token を要求するための extension grant を定義します。

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 の Token Endpoint を実装・レビューし、RFC 8693 の Token Exchange request / response の配置と処理を確認したい開発者  
**この記事で伝えること:** `subject_token` とその token type を Token Endpoint に送り、Authorization Server が検証して新しい security token を返す基本フロー  
**扱わないこと:** delegation / impersonation の詳細、`actor_token` と `act` / `may_act` claim、個別 token type の検証方法、Client authentication method の選択、Token Exchange 後の token 利用方法

## 1. Token Exchange は Token Endpoint への extension grant である

RFC 8693 §2.1 は、Client が OAuth 2.0 の extension grant mechanism を使って Authorization Server の Token Endpoint に security token を要求する手順を定義しています。

Token Exchange request は HTTP `POST` です。parameter は JSON member ではなく、UTF-8 の `application/x-www-form-urlencoded` request body に配置します。

基本フローは次のとおりです。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[Token Endpoint へ POST]
    B --> C[subject_token を検証]
    C --> D[Token Exchange request を評価]
    D --> E[security token を発行]
    E --> F[JSON response]
</pre>

図は `subject_token` を使う基本的な Token Exchange に限定しています。`actor_token` を使う delegation の処理は含めていません。

## 2. request body に何を送るか

RFC 8693 §2.1 では、基本的な Token Exchange request に次の parameter を定義しています。

- `grant_type`: REQUIRED。値は `urn:ietf:params:oauth:grant-type:token-exchange`。
- `subject_token`: REQUIRED。request がその party の behalf で行われることを表す security token。
- `subject_token_type`: REQUIRED。`subject_token` の token type identifier。
- `requested_token_type`: OPTIONAL。要求する security token の type。省略した場合、発行する token type は Authorization Server の裁量です。
- `resource`: OPTIONAL。requested token の target service / resource を URI で示します。
- `audience`: OPTIONAL。requested token の target service を logical name で示します。
- `scope`: OPTIONAL。requested token に要求する scope を示します。

`actor_token` と `actor_token_type` も RFC 8693 §2.1 が定義しますが、これらを使う delegation はこの記事の scope 外です。なお、`actor_token_type` は `actor_token` が存在するとき REQUIRED であり、存在しないときは含めてはなりません（MUST NOT）。

## 3. Token Exchange request の具体例

次は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
POST /token HTTP/1.1
Host: as.example.com
Content-Type: application/x-www-form-urlencoded

grant_type=urn%3Aietf%3Aparams%3Aoauth%3Agrant-type%3Atoken-exchange
&subject_token=illustrative-subject-token
&subject_token_type=urn%3Aietf%3Aparams%3Aoauth%3Atoken-type%3Aaccess_token
&resource=https%3A%2F%2Fapi.example.com%2F
```

`grant_type`、`subject_token`、`subject_token_type`、`resource` はすべて form body parameter です。

この例では `subject_token_type` に `urn:ietf:params:oauth:token-type:access_token` を指定しています。RFC 8693 §3 は、この identifier を、当該 Authorization Server が発行した OAuth 2.0 Access Token を示す token type identifier として定義しています。

Client authentication は Token Exchange 固有の parameter ではありません。RFC 8693 §2.1 は通常の OAuth 2.0 mechanism を使用するとし、どの authentication method を support するか、unauthenticated / unidentified Client を許可するかは Authorization Server の deployment decision に委ねています。

## 4. Authorization Server は提示された token を検証する

RFC 8693 §2.1 により、Authorization Server は `subject_token_type` が示す token type に適した validation procedure を実行しなければなりません（MUST）。個々の token の validity criteria と具体的な validation procedure は RFC 8693 の scope 外であり、それぞれの token type と内容に依存します。

Token Exchange を行ったこと自体は、token type 固有の one-time-use semantics などがない限り、`subject_token` の validity に影響しません。RFC 8693 §2.1 は、input token と output token の間に継続的な linkage が作られるものとしても定義していません。

## 5. successful response は JSON で返る

request が valid であり、Authorization Server の policy その他の criteria を満たす場合、RFC 8693 §2.2.1 は HTTP 200 の Token Response を定義しています。response body の media type は `application/json` です。

次は**非規範的な例**です。token value と lifetime は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-cache, no-store

{
  "access_token": "illustrative-issued-token",
  "issued_token_type": "urn:ietf:params:oauth:token-type:access_token",
  "token_type": "Bearer",
  "expires_in": 600
}
```

主要 member は次のとおりです。

- `access_token`: REQUIRED。Token Exchange により発行された security token を運びます。RFC 8693 §2.2.1 は、member 名が `access_token` であっても、発行された token が OAuth Access Token である必要はないと明記しています。
- `issued_token_type`: REQUIRED。発行された security token の representation を示す identifier です。
- `token_type`: REQUIRED。発行された token の利用方法を示します。発行 token が Access Token ではない、または Access Token として利用できない場合、RFC 8693 §2.2.1 は `N_A` を使用します。
- `expires_in`: RECOMMENDED。発行 token の lifetime を秒数で示します。
- `scope`: 発行 token の scope が Client の request と同一なら OPTIONAL、異なる場合は REQUIRED です。
- `refresh_token`: OPTIONAL です。

`issued_token_type` と `token_type` は同じ意味ではありません。前者は発行された security token の representation を示し、後者は OAuth における token の利用方法を示します。

## 6. invalid request と invalid target

RFC 8693 §2.2.2 は、request 自体が invalid である場合、または `subject_token` が invalid もしくは policy 上受け入れられない場合、Authorization Server が OAuth 2.0 error response を構成しなければならず（MUST）、`error` の値を `invalid_request` としなければならない（MUST）と規定しています。

次は**非規範的な例**です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_request"
}
```

また、`resource` または `audience` が示す target service に対して token を発行する意思がない、または発行できない場合、Authorization Server は `invalid_target` を使用するべきです（SHOULD、RFC 8693 §2.2.2）。

## 7. `resource` の一般仕様とは分けて考える

RFC 8693 §2.1 の Token Exchange request は `resource` parameter を定義していますが、この記事の中心テーマは Token Exchange の input token と output token の request / response flow です。

OAuth における `resource` parameter の一般的な意味、Authorization Request と Access Token Request での配置、audience restriction は RFC 8707 の別テーマです。本記事では Token Exchange request の parameter として現れる位置だけを扱います。

## 一次資料

- RFC Editor: [RFC 8693 — OAuth 2.0 Token Exchange](https://www.rfc-editor.org/rfc/rfc8693.html)

参照した主要節: §1, §2, §2.1, §2.2, §2.2.1, §2.2.2, §3  
最終確認: 2026-09-19
