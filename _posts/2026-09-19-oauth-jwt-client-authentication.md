---
layout: post
title: "RFC 7523：JWT Client Authentication では何を送って何を検証するのか"
date: 2026-09-19 17:39:00 +0900
categories: [oauth, jwt]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Token Endpoint で JWT を使った Client Authentication を実装・レビューする開発者  
**この記事で伝えること:** RFC 7523 の JWT Client Authentication で `client_assertion_type` / `client_assertion` をどこに指定し、JWT に何を含め、Authorization Server が何を検証するか  
**扱わないこと:** JWT Bearer Authorization Grant、JWT の取得方法、鍵配布方法、個別 profile が追加する制約

## Article brief

- **Reader:** Token Endpoint の JWT Client Authentication を実装・レビューする開発者
- **Question:** Client は JWT assertion を request のどこに置き、JWT の claim はどう構成し、Authorization Server は何を検証するのか
- **Answer:** form parameter と JWT Claims Set を区別し、RFC 7523 §2.2、§3、§3.2 の validation と error を追える
- **Scope:** RFC 7523 §1、§2.2、§3、§3.2、§5
- **Out of scope:** RFC 7523 §2.1 の JWT Authorization Grant、assertion の取得、鍵交換、追加 profile
- **Primary sources:** RFC 7523
- **Diagram:** Client が Token Endpoint に form-encoded request を送り、Authorization Server が JWT を検証する流れ

## 1. JWT は Client Authentication の credential として使う

RFC 7523 §1 は、JWT を OAuth Client が Authorization Server に対して認証するための mechanism として定義しています。JWT を authorization grant として使う方法も同じ RFC にありますが、本記事では扱いません。

Client Authentication と grant type は別の要素です。JWT Client Authentication は Token Endpoint で Client を認証する方法であり、完全な token request を構成するには別途 grant type が必要です。

## 2. JWT は `client_assertion` form parameter に入れる

RFC 7523 §2.2 では、JWT Client Authentication に次の parameter を使用します。

- **`client_assertion_type`:** `urn:ietf:params:oauth:client-assertion-type:jwt-bearer`
- **`client_assertion`:** 1個の JWT。複数の JWT を含めてはならない（MUST NOT, §2.2）

これらは JSON member ではなく、Token Endpoint に送る `application/x-www-form-urlencoded` request の form parameter です。

次は構造を示すための非規範的な例です。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&
code=AUTHORIZATION_CODE&
client_assertion_type=urn%3Aietf%3Aparams%3Aoauth%3Aclient-assertion-type%3Ajwt-bearer&
client_assertion=HEADER.PAYLOAD.SIGNATURE
```

`grant_type` と `code` は Authorization Code Grant の parameter です。一方、`client_assertion_type` と `client_assertion` が Client Authentication のための parameter です。

<pre class="mermaid">
flowchart TD
    A[Client] --> B[Token Request]
    B --> C[client_assertion に JWT]
    C --> D[Authorization Server]
    D --> E[JWT を検証]
    E --> F{valid?}
    F -->|Yes| G[Client Authentication 成功]
    F -->|No| H[invalid_client]
</pre>

## 3. `client_assertion` の中身は JWT Claims Set である

RFC 7523 §3 は JWT の validation criteria を定義しています。JWT Client Authentication では特に `sub` の意味が決まっています。

次は構造を理解するための非規範的な Claims Set の例です。

```json
{
  "iss": "client-123",
  "sub": "client-123",
  "aud": "https://authorization.example/token",
  "exp": 1790000300,
  "iat": 1790000000,
  "jti": "assertion-123"
}
```

各 claim の位置と規範要件は次のとおりです。

- **`iss`:** top-level claim。MUST, §3。JWT issuer の一意な identifier。
- **`sub`:** top-level claim。MUST, §3。Client Authentication では OAuth Client の `client_id` でなければならない（MUST）。
- **`aud`:** top-level claim。MUST, §3。Authorization Server を intended audience として識別する値。Token Endpoint URL は audience value として使用できる（MAY）。Authorization Server は自身を intended audience に含まない JWT を拒否しなければならない（MUST）。
- **`exp`:** top-level claim。MUST, §3。JWT を使用できる時間を制限する。Authorization Server は expiration time を過ぎた JWT を拒否しなければならない（MUST）。
- **`nbf`:** top-level claim。MAY, §3。指定されている場合、その時刻より前は token を処理してはならない（MUST NOT）。
- **`iat`:** top-level claim。MAY, §3。
- **`jti`:** top-level claim。MAY, §3。Authorization Server は、有効期間中に使用済み `jti` を保持して replay を防止することができる（MAY）。

上の `iss`、`aud`、時刻、`jti` の値は illustrative value です。RFC 7523 §5 は issuer / audience identifier、key、one-time-use restriction、maximum JWT lifetime などの具体値について当事者間の agreement が必要であり、その交換方法を scope 外としています。

## 4. Authorization Server は JWT を検証する

RFC 7523 §3 により、Authorization Server は Client Authentication に JWT を利用する前に規定された criteria で JWT を検証しなければなりません（MUST）。追加の restriction や policy は Authorization Server の裁量です。

claim の検証に加えて、JWT は issuer による digital signature または MAC が適用されていなければならず（MUST）、Authorization Server は無効な signature または MAC の JWT を拒否しなければなりません（MUST, §3）。また、JWT としてその他の点でも valid でない JWT を拒否しなければなりません（MUST, §3）。

RFC 7523 自体は replay protection を必須にはしていません。`jti` を使った replay prevention は MAY です。

## 5. Client Authentication が失敗すると `invalid_client`

RFC 7523 §3.2 では Client JWT が valid でない場合、Authorization Server は OAuth 2.0 の error response を構成し、`error` parameter を `invalid_client` としなければなりません（MUST）。

次は response object の構造を示す非規範的な例です。

```http
HTTP/1.1 400 Bad Request
Content-Type: application/json
Cache-Control: no-store

{
  "error": "invalid_client"
}
```

Authorization Server は invalid と判断した理由を `error_description` または `error_uri` で追加できる（MAY, §3.2）とされています。

JWT Authorization Grant が invalid な場合の `invalid_grant` は §3.1 の別処理です。本記事の Client Authentication failure では `invalid_client` を扱います。

## 一次資料

- RFC Editor: [RFC 7523 — JSON Web Token (JWT) Profile for OAuth 2.0 Client Authentication and Authorization Grants](https://www.rfc-editor.org/rfc/rfc7523.html)

参照した主要節: §1, §2.2, §3, §3.2, §5  
最終確認: 2026-09-19
