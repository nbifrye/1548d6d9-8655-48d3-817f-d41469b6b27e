---
layout: post
title: "OpenID Connect：UserInfo Endpoint は Claims をどう返し、Client は sub をどう確認するのか"
date: 2026-09-20 21:45:00 +0900
categories: [authentication, oidc]
tags: [OpenID Connect, UserInfo]
---

OpenID Connect Core 1.0 の UserInfo Endpoint は、OpenID Connect Authentication で得た Access Token を使って、認証された End-User の Claims を取得する OAuth 2.0 Protected Resource です。

## この記事について

**記事タイプ:** Flow / Requirement  
**対象読者:** OpenID Connect の Relying Party / OpenID Provider を実装・レビューし、UserInfo request / response と `sub` の照合要件を確認したい開発者  
**この記事で伝えること:** Client が Access Token を UserInfo Endpoint に送り、Claims を受け取り、UserInfo Response の `sub` を ID Token の `sub` と照合するまでの処理  
**扱わないこと:** ID Token 全体の validation、`claims` request parameter の詳細、scope ごとの Claim 選択、Aggregated / Distributed Claims、Client Registration による signed / encrypted UserInfo response の設定方法

### Article brief

- **Reader:** OpenID Connect の Relying Party / OpenID Provider 実装者
- **Question:** UserInfo Endpoint へ Access Token をどう送り、返された Claims のうち何を必ず確認するのか
- **Answer:** Bearer Access Token を使う UserInfo Request、JSON response の構造、`sub` の必須性と ID Token の `sub` との exact match、response validation の位置を説明できる
- **Scope:** OpenID Connect Core 1.0 §5.3–§5.3.4
- **Out of scope:** ID Token validation 全般、Claim request の指定方法、Aggregated / Distributed Claims、registration metadata の設定手順
- **Primary sources:** OpenID Connect Core 1.0 incorporating errata set 2 §5.3–§5.3.4、RFC 6750 §2 / §3
- **Diagram:** Client が UserInfo Endpoint に Bearer Access Token を送り、JSON Claims を受けて `sub` を照合する flowchart

## 1. UserInfo Endpoint の位置

OpenID Connect Core 1.0 §5.3 は、UserInfo Endpoint を OAuth 2.0 Protected Resource と定義しています。Client は OpenID Connect Authentication で得た Access Token を使って UserInfo Endpoint に request を送り、認証された End-User の Claims を取得します。

通信には TLS を使用しなければなりません（MUST, §5.3）。UserInfo Endpoint は HTTP `GET` と `POST` の両方をサポートしなければならず（MUST）、Bearer Access Token を受け付けなければなりません（MUST）。

<pre class="mermaid">
flowchart TD
    C[Client] -->|Bearer Access Token| U[UserInfo Endpoint]
    U -->|UserInfo Response| C
    C --> S{UserInfo sub = ID Token sub?}
    S -->|Yes| A[Response を利用]
    S -->|No| R[Response values を使用しない]
</pre>

この図は UserInfo request / response と `sub` の照合だけを示しています。ID Token 自体の validation 手順は含めません。

## 2. UserInfo Request では Access Token を Bearer Token として送る

OpenID Connect Core §5.3.1 は、Client が UserInfo Request を HTTP `GET` または `POST` で送信し、OpenID Connect Authentication Request によって得た Access Token を RFC 6750 に従う Bearer Token として送ることを要求しています（MUST）。

同節は HTTP `GET` を使用し、Access Token を `Authorization` header field で送ることを RECOMMENDED としています。

以下は配置を示すための**非規範的な例**です。token value は illustrative value です。

```http
GET /userinfo HTTP/1.1
Host: server.example.com
Authorization: Bearer illustrative-access-token
```

この例では Access Token は query parameter や JSON member ではなく、HTTP `Authorization` header に配置されています。

## 3. 通常の成功 response は JSON object で Claims を返す

OpenID Connect Core §5.3.2 は、Client Registration で signed または encrypted response が要求されていない場合、UserInfo Claims を JSON object の member として返さなければならない（MUST）と規定しています。

text JSON object を返す場合、HTTP response の `Content-Type` は `application/json` でなければなりません（MUST）。response body は UTF-8 で encode することが SHOULD です。

以下は構造を示すための**非規範的な例**です。Claim values は illustrative value です。

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "sub": "illustrative-subject-123",
  "name": "Example User",
  "email": "user@example.com"
}
```

この JSON object では Claim Name が member name、Claim Value が member value です。

OpenID Provider は privacy 上の理由から、requested Claim の一部を返さないことができます（MAY, §5.3.2）。requested Claim を返さないこと自体は error condition ではありません。Claim を返さない場合、その Claim Name は JSON object から省略することが SHOULD であり、`null` や空文字列として含めることは SHOULD NOT とされています。

## 4. `sub` は必ず返し、ID Token の `sub` と一致させる

UserInfo Response では `sub` Claim を常に返さなければなりません（MUST, §5.3.2）。

Client は UserInfo Response の `sub` が ID Token の `sub` と exact match することを確認しなければなりません（MUST, §5.3.2）。一致しない場合、Client は UserInfo Response の値を使用してはなりません（MUST NOT）。

この確認は、UserInfo Response が ID Token で識別された End-User と同じ Subject に関するものかを Client が結び付ける処理です。OpenID Connect Core §5.3.2 は token substitution attack の可能性を理由としてこの照合を要求しています。

## 5. signed / encrypted response の形式

Client Registration で signed または encrypted UserInfo Response が指定されている場合、Claims は JWT で返され、`Content-Type` は `application/jwt` でなければなりません（MUST, §5.3.2）。

signed response には `iss` と `aud` Claims を含めなければなりません（MUST）。`iss` は OP の Issuer Identifier URL でなければならず（MUST）、`aud` は RP の Client ID であるか、それを含まなければなりません（MUST）。

signing と encryption の両方が要求される場合、response は先に sign してから encrypt しなければなりません（MUST）。

本記事では signed / encrypted response を選択する Client Registration metadata の詳細は扱いません。

## 6. Client が行う UserInfo Response validation

OpenID Connect Core §5.3.4 は、Client に次の validation を要求しています。

1. TLS server certificate check により、応答した OP が意図した OP であることを確認する（MUST）。
2. Client Registration で `userinfo_encrypted_response_alg` を指定している場合、Registration で指定した key を使って response を decrypt する（MUST）。
3. response が signed である場合、JWS に従って signature を validate することが SHOULD。

これらに加えて、§5.3.2 の `sub` exact match が UserInfo Response の値を利用する前提になります。

## 7. error response

OpenID Connect Core §5.3.3 は、UserInfo Endpoint で error condition が発生した場合、RFC 6750 §3 の Error Response を返すと規定しています。

以下は形式を示すための**非規範的な例**です。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token"
```

Bearer Token に関係しない HTTP error は、該当する HTTP status code で返されます。

## 一次資料

- OpenID Foundation: [OpenID Connect Core 1.0 incorporating errata set 2](https://openid.net/specs/openid-connect-core-1_0.html)
- RFC Editor: [RFC 6750 — The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html)

参照した主要節: OpenID Connect Core 1.0 §5.3, §5.3.1, §5.3.2, §5.3.3, §5.3.4; RFC 6750 §2, §3  
最終確認: 2026-09-20
