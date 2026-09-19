---
layout: post
title: "RFC 8705：certificate-bound Access Token は証明書をどう検証するのか"
date: 2026-09-20 02:46:00 +0900
categories: [oauth, mtls, access-token]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** mutual-TLS certificate-bound Access Token を実装・レビューする OAuth Client / Authorization Server / Resource Server 開発者  
**この記事で伝えること:** Authorization Server が Access Token を Client certificate に結び付け、Resource Server が protected resource request の certificate と token の binding をどのように検証するか  
**扱わないこと:** mutual-TLS Client Authentication の PKI / Self-Signed Certificate 各方式、`mtls_endpoint_aliases`、TLS handshake 自体の詳細、DPoP

## Article brief

- **Reader:** OAuth Client / Authorization Server / Resource Server の実装者
- **Question:** certificate-bound Access Token では、どの certificate が token に結び付けられ、Resource Server は request 時に何を比較するのか
- **Answer:** Token Endpoint で使用した Client certificate と Access Token の binding、および Resource Server が同じ certificate の提示と binding の一致を検証する処理を説明できる
- **Scope:** RFC 8705 §3、§3.1、§3.2、§3.3、§3.4 に定義された mutual-TLS client certificate-bound Access Token
- **Out of scope:** RFC 8705 §2 の Client Authentication 方式、§5 の endpoint aliases、refresh token の詳細、DPoP
- **Primary sources:** RFC 8705 §3–§3.4
- **Diagram:** Client、Authorization Server、Resource Server の3者で、certificate を使った token binding と protected resource access を示す sequence diagram

## 1. Client Authentication と certificate-bound Access Token は別の仕組み

RFC 8705 は mutual-TLS Client Authentication と mutual-TLS client certificate-bound Access Token の両方を定義していますが、両者は別の仕組みであり、必ずしも一緒に使用する必要はありません（RFC 8705 §1）。

この記事で扱うのは後者です。Client が Token Endpoint への mutual TLS connection で certificate を提示すると、Authorization Server は発行する Access Token をその certificate に結び付けられます。protected resource へのアクセス時には、Client が同じ certificate を使って Resource Server と mutual TLS connection を確立し、Resource Server が token に関連付けられた certificate と照合します（§3）。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    participant RS as Resource Server
    C->>AS: mutual TLS + Token Request
    Note over C,AS: Client certificate を使用
    AS-->>C: certificate-bound Access Token
    C->>RS: mutual TLS + Access Token
    Note over C,RS: 同じ certificate を使用
    RS->>RS: token の binding と certificate を比較
    RS-->>C: protected resource / error
</pre>

## 2. Token Endpoint で certificate と Access Token を結び付ける

RFC 8705 §3 では、Client が Token Endpoint への connection で mutual TLS を使用した場合、Authorization Server は発行する Access Token を Client certificate に結び付けられます。

binding を Resource Server が参照できる形にする方法として、RFC 8705 は次の2つを定義しています。

- JWT Access Token の中に certificate の hash を含める方法（§3.1）
- Token Introspection response で certificate の hash を返す方法（§3.2）

これら以外の certificate と Access Token の関連付け方法は、Authorization Server と Resource Server の合意によって使用できますが、RFC 8705 の scope 外です（§3）。

## 3. JWT では `cnf` の `x5t#S256` で certificate を表す

Access Token が JWT で表現される場合、certificate の hash 情報は `x5t#S256` confirmation method member で表現することが SHOULD とされています（RFC 8705 §3.1）。

`x5t#S256` は `cnf` claim 内の member です。その値は X.509 certificate の DER encoding に SHA-256 を適用した hash を base64url encode したものです。base64url encoded value は末尾の `=` padding をすべて省略しなければならず（MUST）、改行、空白、その他の追加文字を含めてはなりません（MUST NOT, §3.1）。

次は構造を示すための**非規範的な最小例**です。値は illustrative value です。

```json
{
  "cnf": {
    "x5t#S256": "IllustrativeCertificateThumbprint"
  }
}
```

配置は次のとおりです。

- `cnf`: JWT Claims Set の claim
- `x5t#S256`: `cnf` object の member
- 値: certificate の DER encoding の SHA-256 hash を base64url encode した string

この値によって、JWT Access Token がどの Client certificate に結び付けられているかを Resource Server が確認できます。

## 4. opaque token では Introspection response で binding を取得できる

Resource Server が OAuth 2.0 Token Introspection を使って Access Token の情報を取得する場合、RFC 8705 §3.2 は certificate hash を Introspection response の top-level `cnf` member で返す形式を定義しています。`cnf` の形式と意味は JWT の同名 claim と同じで、RFC 8705 では `x5t#S256` member を使用します。

次は構造を示すための**非規範的な例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "active": true,
  "cnf": {
    "x5t#S256": "IllustrativeCertificateThumbprint"
  }
}
```

ここでは `cnf` は JWT claim ではなく、Introspection response JSON の top-level member です。Resource Server はこの certificate hash と、mutual TLS connection で Client が提示した certificate の hash を比較します（§3.2）。

## 5. protected resource request では同じ certificate を使用する

RFC 8705 §3 は、mutual-TLS-protected resource access について明確な要件を定めています。

Client は protected resource request を、Token Endpoint で mutual TLS に使用したものと**同じ certificate**を使用する mutually authenticated TLS connection 上で行わなければなりません（MUST, §3）。

HTTP 上では Access Token を通常の OAuth protected resource request として送ります。certificate は HTTP header や request body の parameter ではなく、mutual TLS connection で提示されます。

次は配置を示すための**非規範的な例**です。

```http
GET /resource HTTP/1.1
Host: api.example.test
Authorization: Bearer illustrative-access-token
```

この request は、Token Endpoint で Access Token の binding に使用したものと同じ Client certificate を使う mutual TLS connection 上で送信されるものとします。certificate 自体を `Authorization` header に含めるわけではありません。

## 6. Resource Server は TLS layer の certificate と token の binding を比較する

Resource Server は TLS implementation layer から mutual TLS に使用された Client certificate を取得しなければなりません（MUST, RFC 8705 §3）。さらに、その certificate が Access Token に関連付けられた certificate と一致することを検証しなければなりません（MUST, §3）。

JWT Access Token で `cnf.x5t#S256` を使用する場合は token 内の thumbprint、Introspection を使用する場合は response の `cnf.x5t#S256` と、TLS layer から得た certificate に基づく値を照合することになります。

一致しない場合、Resource Server は resource access attempt を拒否しなければなりません（MUST）。RFC 8705 §3 は RFC 6750 に従い、HTTP `401` と `invalid_token` error code を使用することを要求しています（MUST）。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token"
```

この例も非規範的です。ここで示しているのは、certificate が一致しない場合の RFC 8705 §3 の error semantics です。

## 7. capability は metadata で表現できる

RFC 8705 §3.3 は Authorization Server が certificate-bound Access Token を発行できることを示す Authorization Server Metadata parameter として `tls_client_certificate_bound_access_tokens` を定義しています。

- type: boolean
- requirement: OPTIONAL
- 省略時: `false`

非規範的な最小例は次のとおりです。

```json
{
  "tls_client_certificate_bound_access_tokens": true
}
```

RFC 8705 §3.4 は同名の Client Registration Metadata parameter も定義しています。Client が certificate-bound Access Token を使用する意図を示す boolean で、OPTIONAL、未指定時の default は `false` です。

Client がこの意図を示しているにもかかわらず Token Endpoint request を mutual TLS ではない connection で行った場合、error を返すか unbound token を発行するかは Authorization Server の裁量です（§3.4）。RFC 8705 は一方を要求していません。

## 8. この flow で確認する境界

certificate-bound Access Token の処理は、次の境界で整理できます。

1. Token Endpoint では Client が mutual TLS で certificate を提示する。
2. Authorization Server は発行する Access Token をその certificate に関連付ける。
3. JWT の場合、certificate hash は `cnf.x5t#S256` で表現することが SHOULD とされる（§3.1）。Introspection を使う場合、同じ構造を response で Resource Server に伝えられる（§3.2）。
4. Client は protected resource request でも同じ certificate を使用しなければならない（MUST, §3）。
5. Resource Server は TLS layer の certificate と Access Token に関連付けられた certificate を照合しなければならない（MUST, §3）。不一致なら request を拒否する（MUST）。

**The access token is bound to the certificate used at the token endpoint, and the protected resource verifies that binding against the certificate used on its own mutual-TLS connection.**  
（Access Token は Token Endpoint で使用された certificate に結び付けられ、protected resource は自身との mutual TLS connection で使用された certificate に対してその binding を検証します。）

## 一次資料

- RFC 8705, *OAuth 2.0 Mutual-TLS Client Authentication and Certificate-Bound Access Tokens*, §1, §3–§3.4  
  https://www.rfc-editor.org/rfc/rfc8705.html
