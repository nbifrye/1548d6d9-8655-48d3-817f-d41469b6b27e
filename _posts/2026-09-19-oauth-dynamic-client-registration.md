---
layout: post
title: "RFC 7591：Dynamic Client Registration では何を送って何が返るのか"
date: 2026-09-19 10:42:00 +0900
categories: [oauth, client-registration]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 の Dynamic Client Registration を実装・レビューする Client / Authorization Server の開発者  
**この記事で伝えること:** Client Registration Endpoint に送る JSON client metadata と、成功時に返る client information の構造と処理の流れ  
**扱わないこと:** RFC 7592 の registration management、software statement の内部構造と検証、個別 deployment の registration policy、Authorization Code Flow など登録後の OAuth フロー

RFC 7591 は 2015 年 7 月公開の Proposed Standard です。

## 1. Registration Request は JSON object を POST する

RFC 7591 §3.1 では、Client または Client Developer は Client Registration Endpoint に HTTP POST を送り、`Content-Type` を `application/json` とします。HTTP entity body は JSON object で、要求する client metadata を top-level member として配置します。

以下は構造を示すための非規範的な例です。

```http
POST /register HTTP/1.1
Host: server.example
Content-Type: application/json
Accept: application/json

{
  "redirect_uris": [
    "https://client.example/callback"
  ],
  "client_name": "Example Client",
  "token_endpoint_auth_method": "client_secret_basic",
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

ここでは metadata は query parameter や form parameter ではなく、JSON request body の top-level member です。

RFC 7591 §3 は Client Registration Endpoint を transport-layer security mechanism で保護しなければならない（MUST）と規定しています。さらに §5 では、Authorization Server は TLS 1.2 をサポートしなければならず（MUST）、TLS を使用する Client は server certificate を検証しなければなりません（MUST）。RFC 7591 がこの検証について参照する RFC 6125 は、2023 年 11 月公開の RFC 9525 によって廃止・置換されています。RFC 7591 は TLS の実装上の security considerations の参照先として BCP 195 を挙げており、現在の BCP 195 は RFC 8996、RFC 9325、RFC 9852 で構成されています。

Authorization Server が initial access token を要求する構成では、その token を使って Registration Endpoint へのアクセスを制限できます（MAY, §3）。initial access token の取得方法と endpoint における検証方法は RFC 7591 の scope 外です。一方、open registration と interoperability を支援するため、Client Registration Endpoint は authorization なし、すなわち initial access token なしの registration request を許可することが推奨されています（SHOULD, §3）。

## 2. Client metadata は登録したい Client の属性を表す

RFC 7591 §2 は、登録された Client に Authorization Server 上の `client_id` と関連付けられた metadata があると定義しています。metadata は registration request の入力と registration response の出力の両方で使われます。

前の例で使用した member の型と役割は次のとおりです。

- **`redirect_uris`:** URI string の array。redirect-based flow を使う Client は redirect URI を登録しなければなりません（MUST, §2）。Dynamic Registration を redirect-based flow 向けにサポートする Authorization Server はこの metadata をサポートしなければなりません（MUST, §2）。
- **`client_name`:** human-readable string。OPTIONAL metadata。RFC 7591 は Client が常に送ることを RECOMMENDED としています（§2）。
- **`token_endpoint_auth_method`:** string。Token Endpoint で要求する Client authentication method を示します。
- **`grant_types`:** string の array。Client が使用する OAuth 2.0 grant type を示します。
- **`response_types`:** string の array。Client が使用する OAuth 2.0 response type を示します。

RFC 7591 §2 は、特に記載がない限り client metadata field の実装と使用を OPTIONAL としています。

Authorization Server は理解できない client metadata を無視しなければなりません（MUST, §2）。また、要求された metadata value を適切な default に置き換えるか、§3.2.2 の error response を返すことができます（MAY, §2）。

## 3. Authorization Server が registration を処理する

<pre class="mermaid">
flowchart TD
    A[Client / Developer] --> B[JSON metadata を POST]
    B --> C[Registration Endpoint]
    C --> D[Authorization Server が登録を処理]
    D --> E{成功したか}
    E -->|Yes| F[Client Information Response]
    E -->|No| G[Registration Error Response]
</pre>

RFC 7591 §1.3 の abstract flow では、Client または Developer が desired registration metadata を endpoint に送り、Authorization Server が Client を登録します。成功時には登録済み metadata、client identifier、および該当する場合は client secret などの credential が返ります。

どの Client を登録可能とするか、どの metadata value を受け入れるかは Authorization Server の処理に関係します。RFC 7591 が deployment や policy に委ねている判断について、この記事では一方の方針を選びません。

## 4. 成功 response は登録結果を JSON で返す

RFC 7591 §3.2 では、registration が成功した場合、Authorization Server は HTTP `201 Created` と `application/json` の body を返します。§3.2.1 では、その成功 response に `client_id` が含まれます。client secret を発行する場合は `client_secret` も含まれます。

以下は構造を示すための非規範的な例です。

```json
{
  "client_id": "client-123",
  "client_secret": "SECRET_VALUE",
  "client_id_issued_at": 1790000000,
  "client_secret_expires_at": 0,
  "redirect_uris": [
    "https://client.example/callback"
  ],
  "token_endpoint_auth_method": "client_secret_basic",
  "grant_types": ["authorization_code"],
  "response_types": ["code"]
}
```

主要 member は次の位置と意味を持ちます。

- **`client_id`:** top-level string。REQUIRED。Authorization Server が発行する OAuth 2.0 client identifier。RFC 7591 §3.2.1 の公開本文では、他の登録済み Client に対して現在有効な値であるべきではない（SHOULD NOT）一方、同じ登録済み Client の複数 instance に同一の `client_id` を発行してもよい（MAY）とされています。
- **`client_secret`:** top-level string。OPTIONAL。発行される場合、その `client_id` に対して一意でなければなりません（MUST, §3.2.1）。
- **`client_id_issued_at`:** top-level number。OPTIONAL。1970-01-01T00:00:00Z からの秒数で表す発行時刻。
- **`client_secret_expires_at`:** `client_secret` が発行された場合は REQUIRED。expiration time を秒数で表し、`0` は expire しないことを示します。

Authorization Server は、この Client について登録された metadata をすべて返さなければなりません（MUST, §3.2.1）。これには Authorization Server 自身が provision した field も含まれます。

そのため、request で送った値と response の登録結果が常に同一とは限りません。RFC 7591 §3.2.1 は Authorization Server が要求された metadata value を reject または replace し、適切な値を代入できる（MAY）としています。

RFC Editor には `client_id` の `SHOULD NOT` を `MUST NOT` に変更する Technical Errata ID 7782 が登録されていますが、2026年9月21日時点では status は Reported です。そのため、この記事では公開済み RFC 本文の規範強度を維持しています。

## 5. Registration Error は別の JSON object で返る

RFC 7591 §3.2.2 では、registration error condition が発生した場合、別途規定がない限り Authorization Server は HTTP 400 と `application/json` の response を返します。

以下は構造を示すための非規範的な例です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json

{
  "error": "invalid_redirect_uri",
  "error_description": "The redirect URI is not acceptable"
}
```

- **`error`:** REQUIRED な ASCII error code string。
- **`error_description`:** OPTIONAL な human-readable ASCII text。

RFC 7591 §3.2.2 は response にその他の member を含めることも MAY とし、理解できない member は無視しなければならない（MUST）と規定しています。

## 6. Request と response で見る位置関係

Registration Request では、`redirect_uris` などの client metadata が JSON body に入ります。Authorization Server はその request を処理し、成功時には `client_id` と登録済み metadata を JSON response として返します。

`client_id` は Client が request で指定して作る値ではありません。RFC 7591 §3.1 では Authorization Server が Client に client identifier を割り当てます。`client_id` の一意性については、§3.2.1 の公開本文にある SHOULD NOT / MAY の規定も合わせて扱う必要があります。

この request / response の構造と登録結果の扱いがこの記事の範囲です。登録済み Client の configuration を後から read / update / delete する protocol は RFC 7592 の別テーマです。

## 一次資料

- RFC Editor: [RFC 7591 — OAuth 2.0 Dynamic Client Registration Protocol](https://www.rfc-editor.org/rfc/rfc7591.html)
- RFC Editor: [RFC 7591 Errata — Errata ID 7782](https://www.rfc-editor.org/errata/eid7782)
- RFC Editor: [RFC 9525 — Service Identity in TLS](https://www.rfc-editor.org/rfc/rfc9525.html)
- RFC Editor: [BCP 195 — Recommendations for Secure Use of TLS and DTLS](https://www.rfc-editor.org/info/bcp195)

参照した主要節: §1.3, §2, §3, §3.1, §3.2, §3.2.1, §3.2.2, §5  
最終確認: 2026-09-23
