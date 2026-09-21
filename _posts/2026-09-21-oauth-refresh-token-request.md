---
layout: post
title: "RFC 6749：Refresh Token で Access Token を更新するときの request / response"
date: 2026-09-21 16:41:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 の Refresh Token を使った Access Token 更新処理を実装・レビューする開発者  
**この記事で伝えること:** Refresh Token を Token Endpoint に送る request の parameter 配置、scope の制約、Authorization Server の検証、新しい Access Token と optional な Refresh Token の response を RFC 6749 に沿って理解する  
**扱わないこと:** Refresh Token の発行判断、Refresh Token rotation を用いた replay detection、sender-constrained token、Token Revocation、個別の client authentication method の選択

## Article brief

- **Reader:** Refresh Token による Access Token 更新処理を実装・レビューする開発者
- **Question:** Refresh Token は Token Endpoint のどこに指定し、Authorization Server は何を検証し、成功時に何を返すのか
- **Answer:** `grant_type=refresh_token` と `refresh_token` を form body に置くこと、`scope` の制約、client authentication が必要になる条件、検証成功後の Access Token response と Refresh Token 更新時の処理を説明できる
- **Scope:** RFC 6749 §1.5, §3.2, §3.2.1, §5.1, §5.2, §6 の refresh request / response
- **Out of scope:** Refresh Token の発行ポリシー、rotation による replay detection、RFC 9700 の Refresh Token protection、Token Revocation、client authentication method の比較
- **Primary sources:** RFC 6749 §1.5, §3.2, §3.2.1, §5.1, §5.2, §6
- **Diagram:** Client が Token Endpoint に Refresh Token を送り、Authorization Server が client と token を検証して Access Token を返す flowchart

## 1. Refresh Token は Token Endpoint に送る

RFC 6749 §1.5 では、Refresh Token は Access Token を取得するための credential です。Authorization Server が Refresh Token を発行するかどうかは optional です。

Refresh Token が発行されている場合、Client は Token Endpoint に refresh request を送ります。Token Endpoint への Access Token Request は HTTP `POST` を使用しなければなりません（MUST, RFC 6749 §3.2）。

<pre class="mermaid">
flowchart TD
    A[Client: Refresh Token を保持]
    A --> B[Token Endpoint に POST]
    B --> C[Authorization Server: client を必要に応じて認証]
    C --> D[Refresh Token を検証]
    D --> E{valid and authorized}
    E -->|Yes| F[Access Token を発行]
    F --> G[必要に応じて新しい Refresh Token を発行]
    E -->|No| H[Token Error Response]
</pre>

## 2. request parameter は form body に置く

RFC 6749 §6 は refresh request の parameter を `application/x-www-form-urlencoded` 形式、UTF-8 の HTTP request entity-body に置くと定義しています。

- **`grant_type`:** REQUIRED。値は `refresh_token` でなければなりません（MUST）。
- **`refresh_token`:** REQUIRED。Client に発行された Refresh Token です。
- **`scope`:** OPTIONAL。要求する scope です。元の Resource Owner が許可していない scope を含めてはなりません（MUST NOT）。省略した場合は、元の grant の scope と同じものとして扱います。

RFC 6749 §3.2 では request parameter を複数回含めてはならない（MUST NOT）としています。

次は parameter の配置を示すための**非規範的な例**です。値は illustrative value です。ここでは RFC 6749 §2.3.1 が定義する HTTP Basic authentication の形式を例示していますが、client authentication method の選択はこの記事の scope 外です。

```http
POST /token HTTP/1.1
Host: authorization.example
Authorization: Basic Y2xpZW50LTEyMzpleGFtcGxlLXNlY3JldA==
Content-Type: application/x-www-form-urlencoded

grant_type=refresh_token&refresh_token=refresh-token-example&scope=read
```

`grant_type`、`refresh_token`、`scope` は query parameter や JSON member ではなく、この request では form body parameter です。

## 3. Client authentication が必要になる場合がある

RFC 6749 §6 は Refresh Token を発行先 Client に bind します。Client が confidential client である場合、または Client に client credentials や別の authentication requirement が割り当てられている場合、Client は Authorization Server に対して認証しなければなりません（MUST, §6。認証要件は §3.2.1）。

Authorization Server は refresh request を処理するとき、RFC 6749 §6 に従って次を行います。

1. confidential client、または client authentication が必要な Client について認証を要求します。
2. client authentication が含まれる場合は Client を認証し、Refresh Token がその Client に発行されたものであることを確認します。
3. Refresh Token を検証します。

Client authentication の具体的な方式そのものは §6 が一つに固定していません。

## 4. 成功すると新しい Access Token を返す

request が valid and authorized であれば、Authorization Server は RFC 6749 §5.1 に従って Access Token を発行します（§6）。Token Response は `200 OK` で、response parameter は JSON object の top level member として返されます。

次は構造を示すための**非規範的な例**です。token value と lifetime は illustrative value です。

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

RFC 6749 §5.1 の主要 member は次のとおりです。

- **`access_token`:** REQUIRED。発行された Access Token。
- **`token_type`:** REQUIRED。発行された token type。
- **`expires_in`:** RECOMMENDED。Access Token の lifetime を秒で表します。
- **`refresh_token`:** OPTIONAL。新しい Refresh Token が発行される場合に含まれます。
- **`scope`:** request した scope と同一なら OPTIONAL、異なる場合は REQUIRED。

Token や credential を含む response では、Authorization Server は `Cache-Control: no-store` と `Pragma: no-cache` を含めなければなりません（MUST, RFC 6749 §5.1）。

## 5. 新しい Refresh Token が返る場合

RFC 6749 §6 では、Authorization Server は refresh response で新しい Refresh Token を発行してもよい（MAY）としています。

新しい Refresh Token が発行された場合、Client は古い Refresh Token を破棄し、新しい Refresh Token に置き換えなければなりません（MUST）。Authorization Server は古い Refresh Token を revoke してもよい（MAY）とされています。また、新しい Refresh Token の scope は request に含まれた Refresh Token の scope と同一でなければなりません（MUST）。

次は新しい Refresh Token を含む response の**非規範的な例**です。

```json
{
  "access_token": "access-token-example-2",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "refresh-token-example-2",
  "scope": "read"
}
```

この §6 の規定は、新しい Refresh Token を常に発行することを要求していません。

## 6. 検証に失敗した場合

RFC 6749 §6 は、request の verification に失敗した場合または request が invalid な場合、Authorization Server が §5.2 の error response を返すと定めています。

たとえば、Refresh Token が invalid、expired、revoked、または別の Client に発行されたものである場合、§5.2 は `invalid_grant` を定義しています。次は response structure を示す**非規範的な例**です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "error": "invalid_grant"
}
```

Refresh Token の有効性や Client との binding をどのデータ構造で保持するかは、この protocol message の形式としては定義されていません。

## 一次資料

- RFC Editor: [RFC 6749 — The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749.html)

参照した主要節: §1.5, §2.3.1, §3.2, §3.2.1, §5.1, §5.2, §6  
最終確認: 2026-09-21
