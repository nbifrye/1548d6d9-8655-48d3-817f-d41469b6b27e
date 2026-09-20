---
layout: post
title: "OpenID Connect Discovery：Issuer から OP Configuration をどう取得・検証するのか"
date: 2026-09-20 22:40:00 +0900
categories: [authentication, oidc]
---

**記事タイプ:** Flow / Feature Deep Dive  
**対象読者:** OpenID Connect Relying Party の Discovery 処理を実装・レビューする開発者  
**この記事で伝えること:** 既知の Issuer Identifier から OP Configuration URL を構成し、JSON metadata を取得して `issuer` を照合するまでの処理  
**扱わないこと:** WebFinger、Dynamic Client Registration、Authorization Code Flow、ID Token validation、RFC 8414 の一般仕様

## Article brief

- **Reader:** OpenID Connect RP の Discovery 処理を実装・レビューする開発者
- **Question:** Issuer Identifier が既知の場合、RP はどの URL から OP Configuration を取得し、何を確認するのか
- **Answer:** configuration URL の構成、HTTP GET、主要 metadata member、取得した `issuer` と既知 Issuer の一致確認を追える
- **Scope:** OpenID Connect Discovery 1.0 §3–§4
- **Out of scope:** WebFinger、Client Registration、各 endpoint の処理、ID Token validation
- **Primary sources:** OpenID Connect Discovery 1.0 incorporating errata set 2 §3, §4
- **Diagram:** Issuer → configuration URL → JSON metadata → issuer comparison

OpenID Connect Discovery 1.0 は、Relying Party が OpenID Provider の configuration information を動的に取得する方法を定義します。本記事は Issuer Identifier が既知であるところから開始します。

## 1. Issuer から configuration URL を構成する

OpenID Connect Discovery 1.0 §4 により、Discovery をサポートする OP は Issuer Identifier に `/.well-known/openid-configuration` を連結して形成される場所に JSON document を公開しなければなりません（MUST）。

Issuer が `https://server.example.com` なら、configuration URL は次の形です。

```text
https://server.example.com/.well-known/openid-configuration
```

Issuer が path component を含む場合は、その Issuer の末尾に `/.well-known/openid-configuration` を連結します（§4）。

## 2. RP は configuration document を GET する

次は配置を示すための**非規範的な例**です。値は illustrative value です。

```http
GET /.well-known/openid-configuration HTTP/1.1
Host: server.example.com
```

§4 は `openid-configuration` が仕様に準拠する JSON document を指し、`application/json` Content-Type で返されなければならない（MUST）と規定しています。この endpoint は CORS をサポートするべきです（SHOULD）。

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
  "issuer": "https://server.example.com",
  "authorization_endpoint": "https://server.example.com/authorize",
  "token_endpoint": "https://server.example.com/token",
  "jwks_uri": "https://server.example.com/jwks.json",
  "response_types_supported": ["code"],
  "subject_types_supported": ["public"],
  "id_token_signing_alg_values_supported": ["RS256"]
}
```

この JSON は構造と配置を示す非規範的な最小例です。

## 3. 主要 metadata member

OpenID Connect Discovery 1.0 §3 は OP Metadata を JSON member として定義します。

- `issuer`: REQUIRED。OP が主張する Issuer Identifier。
- `authorization_endpoint`: REQUIRED。OP の Authorization Endpoint URL。
- `token_endpoint`: Implicit Flow のみを使用する場合を除き REQUIRED。
- `jwks_uri`: REQUIRED。OP の JWK Set document の URL。`https` scheme を使用しなければなりません（MUST）。
- `response_types_supported`: REQUIRED。サポートする `response_type` の JSON array。
- `subject_types_supported`: REQUIRED。サポートする Subject Identifier type の JSON array。
- `id_token_signing_alg_values_supported`: REQUIRED。ID Token の署名に使用する JWS `alg` values の JSON array。

各 endpoint のプロトコル処理と ID Token validation は本記事の scope 外です。

## 4. `issuer` を既知 Issuer と比較する

§4 は、configuration document の `issuer` value が configuration request の構築に使った Issuer URL と完全に一致しなければならない（MUST）と規定しています。一致しない場合、取得した情報を使用してはなりません（MUST NOT）。

<pre class="mermaid">
flowchart TD
    A[既知の Issuer] --> B[Configuration URL を構成]
    B --> C[HTTP GET]
    C --> D[JSON OP Metadata]
    D --> E{issuer は一致するか}
    E -->|Yes| F[Metadata を利用]
    E -->|No| G[Metadata を利用しない]
</pre>

## 5. RFC 8414 の記事との境界

既存の RFC 8414 記事は OAuth Authorization Server Metadata を扱います。本記事は OpenID Connect Discovery 1.0 の OpenID Provider Configuration に限定し、OpenID Connect 固有 metadata を含む OP Configuration の取得を扱います。

## 一次資料

- OpenID Foundation: OpenID Connect Discovery 1.0 incorporating errata set 2 — https://openid.net/specs/openid-connect-discovery-1_0.html

参照した主要節: §3, §4  
最終確認: 2026-09-20
