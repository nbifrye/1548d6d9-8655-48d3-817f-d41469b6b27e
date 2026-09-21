---
layout: post
title: "RFC 6749：Token Endpoint の error response と error code"
date: 2026-09-21 20:45:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 Token Endpoint の error response を実装・レビューする開発者  
**この記事で伝えること:** Token Endpoint が request を拒否するときの HTTP status、JSON response の構造、RFC 6749 が定義する error code と `invalid_client` の例外的な HTTP 処理を理解する  
**扱わないこと:** Authorization Endpoint の error response、Protected Resource の Bearer error、extension specification が追加する error code、個別 grant の成功 flow

## Article brief

- **Reader:** OAuth 2.0 Token Endpoint の error handling を実装・レビューする開発者
- **Question:** Token Endpoint が Access Token Request を拒否するとき、どの HTTP status と JSON member を返し、標準 error code をどう区別するのか
- **Answer:** 原則 `400 Bad Request` で JSON の `error` を返すこと、`error_description` / `error_uri` は optional であること、6つの標準 error code の意味、`invalid_client` で `401 Unauthorized` と `WWW-Authenticate` が関係する条件を説明できる
- **Scope:** RFC 6749 §5.2 と Appendix A.7–A.9 の Token Error Response
- **Out of scope:** Authorization Endpoint error、RFC 6750 の Protected Resource error、extension error code の個別仕様、grant ごとの request validation 詳細
- **Primary sources:** RFC 6749 §5.2, Appendix A.7–A.9
- **Diagram:** Token Endpoint が request failure を分類し、通常の 400 response と `invalid_client` の 401 response に分岐する flowchart

## 1. Token Endpoint の error response は JSON で返る

RFC 6749 §5.2 は、Access Token Request が失敗した場合の Token Error Response を定義しています。Authorization Server は、別途指定される場合を除き、HTTP `400 Bad Request` を返します。

response parameter は `application/json` の response body に JSON object の top-level member として置かれます。parameter の順序に意味はありません。

<pre class="mermaid">
flowchart TD
    A[Token Endpoint: request を処理]
    A --> B{request 成功?}
    B -->|Yes| C[Token Response]
    B -->|No| D[error code を決定]
    D --> E{invalid_client かつ Authorization header で認証を試行?}
    E -->|Yes| F[401 + WWW-Authenticate]
    E -->|No| G[原則 400]
    F --> H[JSON error response]
    G --> H
</pre>

この図は RFC 6749 §5.2 の response 分岐を簡略化した非規範的な図です。

## 2. `error` は REQUIRED

RFC 6749 §5.2 では `error` は REQUIRED です。値は単一の ASCII error code です。

RFC 6749 §5.2 が定義する code は次の6つです。

- **`invalid_request`:** required parameter の欠落、grant type 以外の unsupported parameter value、parameter の重複、複数 credential の指定、複数の client authentication mechanism の利用など、request が malformed な場合です。
- **`invalid_client`:** unknown client、必要な client authentication の欠落、unsupported authentication method など、client authentication が失敗した場合です。
- **`invalid_grant`:** authorization grant または Refresh Token が invalid、expired、revoked、Authorization Request で使用した redirection URI と不一致、または別 Client に発行された場合などです。
- **`unauthorized_client`:** authenticated Client が、その authorization grant type を使用する権限を持たない場合です。
- **`unsupported_grant_type`:** Authorization Server が authorization grant type をサポートしていない場合です。
- **`invalid_scope`:** requested scope が invalid、unknown、malformed、または Resource Owner が grant した scope を超える場合です。

`error` の値は RFC 6749 §5.2 および Appendix A.7 が定める文字集合の制約に従います。

## 3. `error_description` と `error_uri` は OPTIONAL

RFC 6749 §5.2 では、追加情報を返す2つの member を定義しています。

- **`error_description`:** OPTIONAL。Client developer が error を理解するための human-readable ASCII text です。
- **`error_uri`:** OPTIONAL。Client developer 向けの error 情報を掲載する human-readable web page を識別する URI です。

これらは `error` の代替ではありません。`error` は REQUIRED のままです。

次は JSON member の配置を示すための**非規範的な例**です。説明文と URI は illustrative value です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json;charset=UTF-8
Cache-Control: no-store
Pragma: no-cache

{
  "error": "invalid_request",
  "error_description": "required parameter is missing",
  "error_uri": "https://authorization.example/errors/invalid_request"
}
```

`error`、`error_description`、`error_uri` は HTTP header ではなく JSON response body の member です。

## 4. `invalid_client` では 401 になる場合がある

RFC 6749 §5.2 は `invalid_client` に HTTP status の追加規則を定めています。Authorization Server は、supported HTTP authentication scheme を示すために `401 Unauthorized` を返してもかまいません（MAY）。

ただし、Client が HTTP `Authorization` request header field を使って認証を試みた場合、Authorization Server は `401 Unauthorized` を返し、Client が使用した authentication scheme に対応する `WWW-Authenticate` response header field を含めなければなりません（MUST, RFC 6749 §5.2）。

次は配置を示すための**非規範的な例**です。Client が Basic authentication を `Authorization` header で試行し、その認証が失敗した状況を示します。

```http
HTTP/1.1 401 Unauthorized
Content-Type: application/json;charset=UTF-8
WWW-Authenticate: Basic realm="token"
Cache-Control: no-store
Pragma: no-cache

{
  "error": "invalid_client"
}
```

この例では `WWW-Authenticate` は HTTP response header、`error` は JSON response body の member です。

## 5. error response の最小構造

RFC 6749 §5.2 の Token Error Response で必須なのは `error` です。したがって、最小の JSON object は次の形になります。

```json
{
  "error": "invalid_request"
}
```

これは RFC 6749 §5.2 に掲載される形式に沿った**非規範的な最小例**です。

field の cardinality は次のとおりです。

- `error`: REQUIRED。単一の string value。
- `error_description`: OPTIONAL。指定する場合は単一の string value。
- `error_uri`: OPTIONAL。指定する場合は単一の URI-reference string value。

## 6. この記事の範囲

この記事で扱うのは RFC 6749 §5.2 の Token Endpoint error response です。Authorization Endpoint の error response は RFC 6749 §4.1.2.1 などで別に定義されます。また、Protected Resource への request で用いる Bearer Token の error response は RFC 6750 の範囲です。

したがって、同じ `error` という名前の parameter が現れても、どの endpoint / protocol message の error かを区別して仕様を参照する必要があります。

## Primary sources

- RFC 6749, §5.2 “Error Response”  
  https://www.rfc-editor.org/rfc/rfc6749.html#section-5.2
- RFC 6749, Appendix A.7 “error Syntax”  
  https://www.rfc-editor.org/rfc/rfc6749.html#appendix-A.7
- RFC 6749, Appendix A.8 “error_description Syntax”  
  https://www.rfc-editor.org/rfc/rfc6749.html#appendix-A.8
- RFC 6749, Appendix A.9 “error_uri Syntax”  
  https://www.rfc-editor.org/rfc/rfc6749.html#appendix-A.9
