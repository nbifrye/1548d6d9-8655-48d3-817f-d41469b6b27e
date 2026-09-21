---
layout: post
title: "OAuth state parameter：Authorization Response と CSRF protection の要件"
date: 2026-09-22 06:43:00 +0900
categories: [authorization, oauth]
---

## この記事について

**記事タイプ:** Security Practice  
**対象読者:** OAuth の redirect-based flow で Authorization Request / Response と CSRF 対策を実装またはレビューする開発者  
**この記事で伝えること:** `state` の request / response 上の位置と、RFC 6749 および RFC 9700 が定める CSRF protection の要件  
**扱わないこと:** Authorization Code Grant 全体、PKCE の生成・検証手順、OpenID Connect `nonce` の検証手順、mix-up attack、redirect URI validation

## Article brief

- **Reader:** redirect-based OAuth flow の request / callback 処理と CSRF 対策を実装・レビューする開発者
- **Question:** `state` は Authorization Request / Response のどこに置かれ、現在の OAuth Security BCP では CSRF protection のためにいつ必要になるか
- **Answer:** `state` の往復、RFC 6749 の規定、RFC 9700 における PKCE / OpenID Connect `nonce` との関係、および `state` 自体を保護する条件を区別できる
- **Scope:** RFC 6749 §4.1.1、§4.1.2、§4.1.2.1、§10.12、Appendix A.5、RFC 9700 §2.1、§4.7、§4.7.1
- **Out of scope:** grant 全体、PKCE の `code_verifier` / `code_challenge` 詳細、OIDC `nonce` validation、mix-up attack、redirect URI matching、application state の設計方式
- **Primary sources:** RFC 6749 §4.1.1、§4.1.2、§4.1.2.1、§10.12、Appendix A.5、RFC 9700 §2.1、§4.7、§4.7.1
- **Diagram:** Client が `state` を Authorization Request に含め、Authorization Server が同じ値を Authorization Response に返し、Client が user-agent session との binding を検証する流れ

## 1. `state` は Authorization Request から Authorization Response へ返される

RFC 6749 §4.1.1 では、Authorization Code Grant の Authorization Request における `state` は **RECOMMENDED** です。Client が request と callback の間の state を維持するために使う opaque value と定義され、CSRF 防止のために使用すべきとされています（**SHOULD**）。

`state` は Authorization Endpoint への request parameter です。次は配置を示すための**非規範的な例**で、値は illustrative value です。

```http
GET /authorize?response_type=code&client_id=illustrative-client&state=illustrative-state HTTP/1.1
Host: authorization.example
```

RFC 6749 §4.1.2 では、request に `state` が含まれていた場合、Authorization Server は successful Authorization Response に `state` を含めなければなりません（**REQUIRED**）。値は Client から受け取ったものと完全に同じ値です。

```http
HTTP/1.1 302 Found
Location: https://client.example/cb?code=illustrative-code&state=illustrative-state
```

Authorization Request が error になり、Client の redirection URI へ error response を返せる場合も、request に `state` が含まれていれば `state` は **REQUIRED** で、受信した値をそのまま返します（RFC 6749 §4.1.2.1）。

Appendix A.5 では `state` の構文を `1*VSCHAR` と定義しています。

## 2. RFC 6749 の CSRF binding

RFC 6749 §10.12 は、Client の redirection URI に対する CSRF を防ぐため、redirection URI への request に User-Agent の authenticated state と結び付く値を含める方法を説明しています。Client はその値を Authorization Request の `state` parameter で Authorization Server に渡すべきです（**SHOULD**）。

CSRF protection に使う binding value は推測不能な値を含まなければならず（**MUST**）、User-Agent の authenticated state は Client と User-Agent だけがアクセスできる場所に保持しなければなりません（**MUST**）。

**The returned `state` value is useful only when the client validates its binding to the transaction or user-agent state it started with.**  
（返された `state` 値は、Client が開始時の transaction または User-Agent state との binding を検証して初めて意味を持ちます。）

## 3. RFC 9700 は Client に CSRF protection を要求する

RFC 9700 §2.1 は、Client が CSRF を防止しなければならないと規定しています（**MUST**）。そのうえで、利用できる mechanism を条件付きで区別しています。

- Authorization Server が PKCE をサポートすることを Client が確認済みなら、Client は PKCE が提供する CSRF protection に依存してもかまいません（**MAY**）。
- OpenID Connect flow では `nonce` parameter が CSRF protection を提供します。
- それ以外では、User-Agent に安全に bind された one-time-use CSRF token を `state` parameter で運ばなければなりません（**MUST**）。

したがって、RFC 9700 はすべての redirect-based flow に無条件で `state` を MUST としているわけではありません。要件の中心は CSRF protection の **MUST** であり、`state` の **MUST** は上記の代替 mechanism を利用しない場合に適用されます。

## 4. PKCE を CSRF protection に使う条件

RFC 9700 §4.7.1 は、PKCE を `state` または OpenID Connect `nonce` の代わりに CSRF protection として使用する場合、Client は Authorization Server が PKCE をサポートしていることを確認しなければならないと規定しています（**MUST**）。

Authorization Server が PKCE をサポートしない場合、`state` または `nonce` を CSRF protection に使用しなければなりません（**MUST**）。また Authorization Server は、PKCE support を検出できる方法を提供しなければなりません（**MUST**）。RFC 9700 §4.7.1 は RFC 8414 の Authorization Server Metadata の利用を **RECOMMENDED** としつつ、deployment-specific な方法も許可しています（**MAY**）。

## 5. `state` に application state を入れる場合

RFC 9700 §4.7.1 は、`state` を application state の運搬にも使い、その内容の integrity が問題になる場合、Client は `state` を tampering と swapping から保護しなければならないと規定しています（**MUST**）。仕様は browser session への binding や signing / encryption を実現方法として挙げていますが、この記事では一方式を推奨しません。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    C->>AS: Authorization Request + state
    AS-->>C: Authorization Response + same state
    C->>C: binding を検証
</pre>

この図は `state` の往復と Client 側の binding validation を示す**非規範的な図**です。

## 6. 仕様上の境界

`state` は Client が request と callback の間で state を維持するための parameter でもありますが、RFC 9700 の CSRF protection 要件では PKCE と OpenID Connect `nonce` も関係します。どの mechanism を利用できるかは flow と仕様上の条件によって異なります。この記事では application state の具体的なデータ形式や保存方式を定めません。

## Primary sources

- RFC 6749, §4.1.1, §4.1.2, §4.1.2.1, §10.12, Appendix A.5, *The OAuth 2.0 Authorization Framework*: https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 9700, §2.1, §4.7, §4.7.1, *Best Current Practice for OAuth 2.0 Security*: https://www.rfc-editor.org/rfc/rfc9700.html
