---
layout: post
title: "RFC 9126：PAR では Authorization Request をどう push するのか"
date: 2026-09-19 13:47:00 +0900
categories: [oauth, authorization]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 の Authorization Request と Pushed Authorization Requests（PAR）を実装・レビューする開発者  
**この記事で伝えること:** Client が Authorization Request の parameter を PAR Endpoint に直接 POST し、返された `request_uri` を Authorization Endpoint で使うまでの request / response 構造と処理順序  
**扱わないこと:** Request Object の署名・暗号化、FAPI 固有要件、Authorization Code の交換、PKCE 自体の処理、PAR の security considerations の詳細

## 1. PAR は Authorization Request を先に Authorization Server へ送る

RFC 9126 §1 は Pushed Authorization Requests（PAR）を、Client が Authorization Request の payload を Authorization Server に直接 push し、そのデータを参照する `request_uri` を受け取る仕組みとして定義しています。

Client はその後、User Agent を Authorization Endpoint へ redirect するときに `request_uri` を使用します。Authorization Request の主要な parameter を User Agent 経由の URL にすべて載せるのではなく、先に PAR Endpoint へ送る点が処理上の特徴です。

この記事では、RFC 9126 §2、§2.1–§2.3、§4 に限定して、この2段階の request を追います。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[PAR Endpoint へ POST]
    B --> C[Authorization Server が検証]
    C --> D[request_uri を返す]
    D --> E[User Agent を Authorization Endpoint へ誘導]
    E --> F[client_id と request_uri を送る]
    F --> G[Authorization Server が Authorization Request を処理]
</pre>

## 2. PAR Endpoint へ送る parameter は form body に置く

RFC 9126 §2 は PAR Endpoint を HTTP API として定義しています。Endpoint URL は `https` scheme を使用しなければなりません（MUST）。Client は HTTP `POST` を使用し、parameter を UTF-8 の `application/x-www-form-urlencoded` request body に入れます。

RFC 9126 §2.1 によれば、PAR Endpoint は Authorization Endpoint で使用できる Authorization Request parameter と、適用可能な extension parameter を受け付けます。`client_id` は Pushed Authorization Request でも required です。

一方、`request_uri` authorization request parameter を Pushed Authorization Request に含めてはなりません（MUST NOT, §2.1）。

### 2.1 parameter の配置

- **HTTP method:** `POST`
- **送信先:** PAR Endpoint
- **Content-Type:** `application/x-www-form-urlencoded`
- **`client_id`:** form body。Pushed Authorization Request でも required
- **`response_type`:** form body。Authorization Request parameter
- **`redirect_uri`:** form body。Authorization Request parameter
- **`scope`:** form body。Authorization Request parameter
- **`state`:** form body。Authorization Request parameter
- **Client authentication parameter / credential:** Client に適用される方式に従い request header または body に置く
- **`request_uri`:** Pushed Authorization Request には含めない（MUST NOT）

以下は RFC 9126 §2.1 の形式を示すための非規範的な例です。値は構造を示すための illustrative value です。

```http
POST /par HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded
Authorization: Basic <client-credential>

response_type=code&client_id=client-123&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&scope=read&state=state-123
```

`Authorization` header は例示した Client authentication の credential です。RFC 9126 §2 は PAR Endpoint に、Token Endpoint request に対する Client authentication の規則を適用します。仕様は Client authentication をこの例の方式だけに限定していません。

## 3. Authorization Server は push された request を検証する

RFC 9126 §2.1 は Authorization Server の処理順序を規定しています。

1. Authorization Server は Token Endpoint と同じ方法で Client を認証します（MUST）。
2. `request_uri` parameter が含まれていれば request を拒否します（MUST）。
3. Authorization Endpoint に送られた Authorization Request と同様に Pushed Authorization Request を検証します（MUST）。

Authorization Server が push の時点で実行できない validation step は省略できます（MAY）。ただし、その check は Authorization Endpoint で Authorization Request を処理するときに実行しなければなりません（MUST, §2.1）。

## 4. 成功すると `request_uri` と `expires_in` が JSON で返る

RFC 9126 §2.2 では、検証に成功した場合、Authorization Server は `request_uri` を生成し、HTTP 201 response で返さなければなりません（MUST）。Response body の media type は `application/json` です。

Response object には次の top-level member が含まれます。

- **`request_uri`:** push された Authorization Request に対応する URI。後続の Authorization Request で参照として使用する。
- **`expires_in`:** positive integer の JSON number。`request_uri` の lifetime を秒数で表す。

`request_uri` は、その Authorization Request を push した Client に bind されなければなりません（MUST, §2.2）。また、その値には、有効な値を予測・推測することが計算上困難になるよう cryptographically strong pseudorandom algorithm で生成した部分を含めなければなりません（MUST, §2.2）。

以下は構造を示すための非規範的な例です。

```http
HTTP/1.1 201 Created
Content-Type: application/json
Cache-Control: no-cache, no-store

{
  "request_uri": "urn:ietf:params:oauth:request_uri:example-reference",
  "expires_in": 60
}
```

`expires_in` の具体的な lifetime は Authorization Server の裁量です。RFC 9126 §2.2 は一律の秒数を要求していません。

## 5. Authorization Endpoint では `request_uri` を参照として送る

RFC 9126 §4 では、Client は PAR Endpoint から受け取った `request_uri` を使って Authorization Request を構築します。

以下は配置を示すための非規範的な例です。

```http
GET /authorize?client_id=client-123&request_uri=urn%3Aietf%3Aparams%3Aoauth%3Arequest_uri%3Aexample-reference HTTP/1.1
Host: authorization.example
```

ここでは `client_id` と `request_uri` が Authorization Endpoint への request の query parameter です。最初の PAR request で form body に送った Authorization Request data は、この段階では `request_uri` から参照されます。

Client は `request_uri` を一度だけ使用しなければなりません（MUST, §4）。Authorization Server は `request_uri` を one-time use として扱うべきですが（SHOULD）、User Agent の reload / refresh による duplicate request を許可できます（MAY）。expired `request_uri` は invalid として拒否しなければなりません（MUST）。

## 6. PAR Endpoint の error response

RFC 9126 §2.3 は、PAR Endpoint の error response に Token Endpoint error response と同じ形式を使用すると規定しています。Authorization Request の初期処理に extension が関係する場合、その extension が定義する error code も使用できます。

次は response object の形を示すための非規範的な例です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
Cache-Control: no-cache, no-store

{
  "error": "invalid_request",
  "error_description": "The request is invalid"
}
```

RFC 9126 §2.3 は、`POST` 以外の method を使用した場合は HTTP 405、Authorization Server が許容する上限を超える request size の場合は HTTP 413、一定期間に Client から許容数を超える request があった場合は HTTP 429 を使用すると規定しています。

## 7. 2つの request で parameter の置き場所が変わる

PAR の処理では、同じ Authorization 処理のために2つの HTTP request が登場します。

最初の Pushed Authorization Request では、Authorization Request parameter を Client から PAR Endpoint へ直接送り、`application/x-www-form-urlencoded` の body に置きます。

次の Authorization Request では、Client は User Agent を Authorization Endpoint へ誘導し、PAR Endpoint から返された `request_uri` を参照として使用します。

この2段階を区別すると、`request_uri` が「最初から Client が用意する Authorization Request data」ではなく、「push した request に対して Authorization Server が返す参照」であることを追えます。

## 一次資料

- RFC Editor: [RFC 9126 — OAuth 2.0 Pushed Authorization Requests](https://www.rfc-editor.org/rfc/rfc9126.html)

参照した主要節: §1, §2, §2.1, §2.2, §2.3, §4  
最終確認: 2026-09-19
