---
layout: post
title: "RFC 9126：PAR で Authorization Request はどのように2段階化されるのか"
date: 2026-09-20 12:44:00 +0900
categories: [oauth, authorization]
---

<!--
Article brief
Reader: OAuth Client / Authorization Server で PAR を実装・レビューする開発者
Question: PAR を使うと Authorization Request の parameter はどこへ送られ、request_uri はその後どのように Authorization Endpoint で使われるのか
Answer: Client が Authorization Request の payload を PAR Endpoint へ直接 POSTし、返された request_uri を User Agent 経由の後続 Authorization Request で参照する2段階の配置と処理を理解できる
Scope: RFC 9126 §2.1–§2.3、§4、§5 における PAR request、successful response、後続 Authorization Request、関連 metadata
Out of scope: JAR Request Object の署名・暗号化、PAR 固有の redirect URI 登録緩和、Authorization Code の交換、Access Token 発行、FAPI profile 固有要件
Primary sources: RFC 9126、RFC 6749、RFC 8414
Diagram: Client / Authorization Server / User Agent の2段階処理を示す小規模 sequenceDiagram
-->

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth Client / Authorization Server で PAR を実装・レビューする開発者  
**この記事で伝えること:** Authorization Request の payload を PAR Endpoint に直接送信し、返された `request_uri` を後続の Authorization Request で参照する2段階の処理  
**扱わないこと:** JAR Request Object の署名・暗号化、PAR 固有の redirect URI 登録緩和、Authorization Code の交換、Access Token 発行、FAPI profile 固有要件

## 1. PAR は Authorization Request の payload と User Agent 経由の request を分ける

RFC 9126 §1 は Pushed Authorization Requests（PAR）を、OAuth 2.0 Client が Authorization Request の payload を Authorization Server に直接 push し、その代わりに受け取った `request_uri` を後続の Authorization Endpoint 呼び出しで使用する仕組みとして定義しています。

通常の OAuth 2.0 Authorization Request では、Authorization Request parameter は User Agent を介して Authorization Endpoint に送られます。PAR では処理が2段階になります。

1. Client は Authorization Request parameter を PAR Endpoint に直接送ります。
2. Authorization Server は request data を参照する `request_uri` を返します。
3. Client は User Agent を Authorization Endpoint に向け、`client_id` と `request_uri` を送ります。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant UA as User Agent
    C->>AS: POST PAR request
    AS-->>C: 201 + request_uri
    C->>UA: Authorization URL
    UA->>AS: client_id + request_uri
</pre>

この図は RFC 9126 §1.1、§2、§4 の処理関係を簡略化した非規範的な図です。

## 2. 第1段階：Client は PAR Endpoint に form body を POST する

RFC 9126 §2 は PAR Endpoint を Authorization Server の HTTP API として定義しています。Endpoint URL は `https` scheme を使用しなければなりません（MUST, §2）。

Client は Authorization Request を構成する parameter を、`application/x-www-form-urlencoded` の HTTP request body に入れて `POST` します（§2.1）。Authorization Endpoint で利用可能な OAuth parameter と適用可能な extension parameter を PAR Endpoint に送れます。

次は配置を確認するための非規範的な例です。値は illustrative value です。

```http
POST /par HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

response_type=code&client_id=client-123&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&scope=read&state=state-123&code_challenge=challenge-value&code_challenge_method=S256
```

主要 parameter の配置は次のとおりです。

- `response_type`: form body の Authorization Request parameter。
- `client_id`: form body。RFC 9126 §2.1 では pushed authorization request でも required です。
- `redirect_uri`: form body。
- `scope`、`state`: form body。
- `code_challenge`、`code_challenge_method`: PKCE を利用する場合の form body parameter。RFC 9126 §2 は Authorization Endpoint に適用される extension parameter を PAR Endpoint でも受け付けます。
- Client authentication が必要な場合、その credential は Token Endpoint request と同じ規則で request header または request body に配置します（§2、§2.1）。

`request_uri` はこの第1段階の request に含めてはなりません（MUST NOT, RFC 9126 §2.1）。`request_uri` は Client が作って push する parameter ではなく、成功時に Authorization Server から返される参照値です。

## 3. Authorization Server は pushed request を処理する

RFC 9126 §2.1 は、Authorization Server が pushed authorization request を処理する手順を規定しています。

Authorization Server は Client を Token Endpoint と同じ方法で認証しなければなりません（MUST, §2.1）。また、`request_uri` が request に含まれていれば reject し、pushed request を Authorization Endpoint に送られた Authorization Request と同様に validate します。

Authorization Server は PAR Endpoint で実行できない validation step を省略しても構いません（MAY, §2.1）。ただし、その check は Authorization Endpoint で Authorization Request を処理するときに実行しなければなりません（MUST, §2.1）。

したがって、RFC 9126 は「すべての Authorization Request validation を必ず PAR Endpoint だけで完了する」とは規定していません。

## 4. 成功 response は `request_uri` と `expires_in` を返す

verification が成功すると、Authorization Server は `request_uri` を生成し、HTTP `201` response で返さなければなりません（MUST, RFC 9126 §2.2）。response body は `application/json` です。

次は RFC 9126 §2.2 の構造に沿った非規範的な例です。

```http
HTTP/1.1 201 Created
Content-Type: application/json
Cache-Control: no-cache, no-store

{
  "request_uri": "urn:ietf:params:oauth:request_uri:illustrative-reference",
  "expires_in": 60
}
```

- `request_uri`: pushed authorization request data を参照する URI。RFC 9126 §2.2 は、後続 Authorization Request における respective request data への single-use reference と定義しています。
- `expires_in`: `request_uri` の lifetime を秒で表す正の整数の JSON number。lifetime は Authorization Server の裁量です（§2.2）。

`request_uri` の形式は Authorization Server の裁量ですが、valid value の予測・推測が computationally infeasible となるよう、cryptographically strong pseudorandom algorithm で生成した部分を含めなければなりません（MUST, §2.2）。また `request_uri` は、それを取得した Client に bind されなければなりません（MUST, §2.2）。

## 5. 第2段階：User Agent 経由では `request_uri` を Authorization Endpoint に送る

RFC 9126 §4 では、Client は PAR Endpoint から受け取った `request_uri` を使って、後続の Authorization Request を構成します。

次は非規範的な例です。

```http
GET /authorize?client_id=client-123&request_uri=urn%3Aietf%3Aparams%3Aoauth%3Arequest_uri%3Aillustrative-reference HTTP/1.1
Host: authorization.example
```

この段階では `client_id` と `request_uri` は Authorization Endpoint への request の query parameter にあります。

RFC 9126 §4 では、Client は `request_uri` value を1回だけ使用しなければなりません（MUST）。Authorization Server は `request_uri` を one-time use として扱うべきですが（SHOULD）、User Agent の reload / refresh による duplicate request を許容しても構いません（MAY）。期限切れの `request_uri` は invalid として reject しなければなりません（MUST, §4）。

Authorization Server は pushed request に由来する Authorization Request を、通常の Authorization Request と同様に validate しなければなりません（MUST, §4）。PAR Endpoint ですでに実施した validation step は、pushed request であることを確認でき、request または Authorization Server policy が validation outcome に影響する形で変更されていないことを確認できる場合に限り、省略しても構いません（MAY, §4）。

## 6. PAR Endpoint と PAR 必須 policy は Authorization Server Metadata で表現できる

RFC 9126 §5 は RFC 8414 の Authorization Server Metadata に PAR 用の member を追加しています。PAR をサポートする Authorization Server は `pushed_authorization_request_endpoint` を metadata document に含めるべきです（SHOULD, RFC 9126 §2）。

次は必要な構造だけを示す非規範的な例です。

```json
{
  "issuer": "https://authorization.example",
  "pushed_authorization_request_endpoint": "https://authorization.example/par",
  "require_pushed_authorization_requests": false
}
```

- `pushed_authorization_request_endpoint`: PAR Endpoint URL を表す top-level JSON string（§5）。
- `require_pushed_authorization_requests`: Authorization Server が Authorization Request data を PAR 経由でのみ受け付けるかを表す top-level JSON boolean。省略時の default は `false` です（§5）。

Authorization Server Metadata 自体の取得・`issuer` 検証は RFC 8414 の別の処理であり、本記事の中心テーマには含めません。

## 7. 2段階で変わるのは Authorization Request parameter の運び方である

PAR では、Authorization Request の payload を最初に Client から Authorization Server へ直接 `POST` し、User Agent を介する後続 request では、その data を参照する `request_uri` を使用します。

**The pushed request carries the authorization request payload; the later front-channel request carries a reference to that payload.**  
（pushed request は Authorization Request の payload を運び、後続の front-channel request はその payload への参照を運びます。）

この2段階を区別すると、`response_type`、`redirect_uri`、`scope` などが置かれる第1段階の form body と、`request_uri` が置かれる第2段階の Authorization Endpoint request を分けて確認できます。

## Primary sources

- RFC 9126, *OAuth 2.0 Pushed Authorization Requests*, §1–§5: https://www.rfc-editor.org/rfc/rfc9126.html
- RFC 6749, *The OAuth 2.0 Authorization Framework*, §3.1、§4.1: https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 8414, *OAuth 2.0 Authorization Server Metadata*: https://www.rfc-editor.org/rfc/rfc8414.html
