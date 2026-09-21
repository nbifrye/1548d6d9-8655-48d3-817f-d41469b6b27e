---
layout: post
title: "RFC 6749：Authorization Code を Token Endpoint で交換するときの request / response"
date: 2026-09-21 17:40:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Authorization Code Grant の code exchange を実装・レビューする開発者  
**この記事で伝えること:** Authorization Code を Token Endpoint に送る request の parameter 配置、`redirect_uri` と client authentication の条件、Authorization Server の検証、Access Token Response を RFC 6749 に沿って理解する  
**扱わないこと:** Authorization Request / Authorization Response、PKCE、Authorization Code の取得までの Resource Owner interaction、個別の client authentication method の選択、Access Token の利用

## Article brief

- **Reader:** Authorization Code Grant の Token Endpoint 側の code exchange を実装・レビューする開発者
- **Question:** 取得済み Authorization Code は Token Endpoint のどこに指定し、Authorization Server は何を検証して Access Token を返すのか
- **Answer:** `grant_type`、`code`、条件付きの `redirect_uri` / `client_id` を form body に置くこと、client authentication が必要になる条件、code と Client / redirect URI の検証、成功・失敗 response を説明できる
- **Scope:** RFC 6749 §3.2, §3.2.1, §4.1.3, §4.1.4, §5.1, §5.2 の Authorization Code Access Token Request / Response
- **Out of scope:** Authorization Endpoint での request / response、PKCE（RFC 7636）、RFC 9700 の Authorization Code security practice、client authentication method の比較、Resource Server での Access Token 利用
- **Primary sources:** RFC 6749 §3.2, §3.2.1, §4.1.3, §4.1.4, §5.1, §5.2
- **Diagram:** Client が取得済み Authorization Code を Token Endpoint に送り、Authorization Server が code / Client / redirect URI を検証して Token Response を返す flowchart

## 1. Authorization Code は Token Endpoint で Access Token と交換する

RFC 6749 §4.1.3 では、Client は取得済み Authorization Code を Authorization Server の Token Endpoint に送って Access Token を要求します。Token Endpoint への Access Token Request は HTTP `POST` を使用しなければなりません（MUST, RFC 6749 §3.2）。

<pre class="mermaid">
flowchart TD
    A[Client: Authorization Code を保持]
    A --> B[Token Endpoint に POST]
    B --> C[必要な場合は Client を認証]
    C --> D[Authorization Code を検証]
    D --> E[Client との対応を検証]
    E --> F[redirect_uri を必要に応じて検証]
    F --> G{valid and authorized}
    G -->|Yes| H[Token Response]
    G -->|No| I[Token Error Response]
</pre>

この flowchart は §4.1.3 と §4.1.4 の protocol processing を示す非規範的な要約です。

## 2. request parameter は form body に置く

RFC 6749 §4.1.3 は、Access Token Request の parameter を `application/x-www-form-urlencoded` 形式、UTF-8 の HTTP request entity-body に置くと定義しています。

- **`grant_type`:** REQUIRED。値は `authorization_code` でなければなりません（MUST）。
- **`code`:** REQUIRED。Authorization Server から受け取った Authorization Code です。
- **`redirect_uri`:** Authorization Request に `redirect_uri` を含めていた場合は REQUIRED で、その値は同一でなければなりません（MUST）。
- **`client_id`:** Client が RFC 6749 §3.2.1 に従って Authorization Server に対して認証していない場合は REQUIRED です。

RFC 6749 §3.2 では、request parameter を複数回含めてはならない（MUST NOT）としています。

次は parameter の配置を示すための**非規範的な例**です。code と URI は illustrative value です。ここでは Client が認証していない場合を示すため `client_id` を form body に含めています。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=code-example&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&client_id=client-example
```

`grant_type`、`code`、`redirect_uri`、`client_id` は、この request では query parameter や JSON member ではなく form body parameter です。

## 3. Client authentication が必要になる条件

RFC 6749 §4.1.3 は、Client が confidential client である場合、または client credentials が発行されている、もしくは別の authentication requirement が割り当てられている場合、Client が §3.2.1 に従って Authorization Server に対して認証しなければならない（MUST）と定めています。

Authorization Server は §4.1.3 に従い、confidential client または authentication requirement がある Client には client authentication を要求しなければなりません（MUST）。client authentication が含まれる場合は Client を認証しなければなりません（MUST）。

具体的な client authentication method の選択はこの記事では扱いません。

## 4. Authorization Server は code と Client の対応を検証する

RFC 6749 §4.1.3 では、Authorization Server は Token Request を処理するとき、次を行わなければなりません（MUST）。

1. Authorization Code が valid であることを検証します。
2. authenticated confidential client の場合、Authorization Code がその Client に発行されたことを確認します。
3. public client の場合、Authorization Code が request の `client_id` に対して発行されたことを確認します。
4. Authorization Request に `redirect_uri` が含まれていた場合、Token Request にも `redirect_uri` が存在し、その値が同一であることを確認します。

これらは Token Endpoint で観測される protocol requirement です。Authorization Server が code と Client / redirect URI の対応をどの内部データ構造で保持するかは、RFC 6749 §4.1.3 の request format としては定義されていません。

## 5. 成功すると Access Token Response を返す

Access Token Request が valid and authorized であれば、Authorization Server は Access Token と、optional な Refresh Token を RFC 6749 §5.1 に従って発行します（RFC 6749 §4.1.4）。

次は response structure を示すための**非規範的な例**です。token value と lifetime は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "access_token": "access-token-example",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

RFC 6749 §5.1 の主要 member は次のとおりです。

- **`access_token`:** REQUIRED。Authorization Server が発行した Access Token。
- **`token_type`:** REQUIRED。発行された token type。
- **`expires_in`:** RECOMMENDED。Access Token の lifetime を秒で表します。
- **`refresh_token`:** OPTIONAL。Refresh Token が発行される場合に含まれます。
- **`scope`:** Client が要求した scope と同一なら OPTIONAL、異なる場合は REQUIRED。

Token や credential を含む response では、Authorization Server は `Cache-Control: no-store` と `Pragma: no-cache` を含めなければなりません（MUST, RFC 6749 §5.1）。

## 6. 検証に失敗した場合

RFC 6749 §4.1.4 は、Access Token Request が invalid である場合、または client authentication が失敗した場合に §5.2 の error response を返すと定めています。

たとえば、Authorization Code が invalid、expired、revoked、`redirect_uri` と一致しない、または別の Client に発行されたものである場合、RFC 6749 §5.2 は `invalid_grant` を定義しています。

次は response structure を示す**非規範的な例**です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "error": "invalid_grant"
}
```

client authentication 自体が失敗した場合には、§5.2 の `invalid_client` が適用されます。HTTP status code と `WWW-Authenticate` の扱いは、Client がどの authentication scheme を使用したかによって §5.2 の規定が適用されます。

## 一次資料

- RFC Editor: [RFC 6749 — The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749.html)

参照した主要節: §3.2, §3.2.1, §4.1.3, §4.1.4, §5.1, §5.2  
最終確認: 2026-09-21
