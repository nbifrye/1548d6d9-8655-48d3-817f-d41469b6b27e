---
layout: post
title: "RFC 6749：Authorization Code を Authorization Endpoint で取得する request / response"
date: 2026-09-21 18:41:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Authorization Code Grant の Authorization Endpoint 側を実装・レビューする開発者  
**この記事で伝えること:** Client が Authorization Request を構成し、Authorization Server が request を検証して Authorization Code または error を redirection URI へ返すまでの parameter 配置と処理を RFC 6749 に沿って理解する  
**扱わないこと:** Token Endpoint での code exchange、PKCE、RFC 9700 の Authorization Code security practice、JAR / PAR、OpenID Connect 固有 parameter、Resource Owner の認証方式

## Article brief

- **Reader:** Authorization Code Grant の Authorization Endpoint 側を実装・レビューする開発者
- **Question:** Authorization Code を取得する request では何をどこに指定し、Authorization Server は成功時・失敗時に何を redirection URI へ返すのか
- **Answer:** `response_type`、`client_id`、`redirect_uri`、`scope`、`state` の配置、Authorization Server の request validation、成功時の `code` / `state`、error response と invalid redirection URI の扱いを説明できる
- **Scope:** RFC 6749 §3.1, §3.1.1, §3.1.2, §4.1.1, §4.1.2, §4.1.2.1 の Authorization Code Authorization Request / Response
- **Out of scope:** RFC 6749 §4.1.3 以降の Token Request / Response、PKCE（RFC 7636）、RFC 9700 の security practice、JAR、PAR、OpenID Connect、Resource Owner authentication の具体的方法
- **Primary sources:** RFC 6749 §3.1, §3.1.1, §3.1.2, §4.1.1, §4.1.2, §4.1.2.1
- **Diagram:** Client が User-Agent を Authorization Endpoint へ導き、Authorization Server が request を検証し、成功時は code、redirect URI 自体を信頼できない失敗では redirect しない流れ

## 1. Authorization Request は Authorization Endpoint の query component に置く

RFC 6749 §4.1.1 では、Client は Authorization Endpoint URI の query component に `application/x-www-form-urlencoded` 形式で parameter を追加して Authorization Request を構成します。

- **`response_type`:** REQUIRED。値は `code` でなければなりません（MUST, §4.1.1）。
- **`client_id`:** REQUIRED。RFC 6749 §2.2 の Client Identifier です。
- **`redirect_uri`:** OPTIONAL。§3.1.2 に従う redirection URI です。
- **`scope`:** OPTIONAL。§3.3 に従う access request の scope です。
- **`state`:** RECOMMENDED。Client が request と callback の間で state を維持するための opaque value です。§4.1.1 は CSRF 防止のために使用すべき（SHOULD）としています。

RFC 6749 §3.1 は Authorization Endpoint が HTTP `GET` をサポートしなければならず（MUST）、`POST` もサポートしてよい（MAY）と定めています。また、Authorization Endpoint への request には TLS を要求しなければなりません（MUST）。

次は parameter の配置を示すための**非規範的な例**です。identifier、URI、scope、state は illustrative value です。

```http
GET /authorize?response_type=code&client_id=client-example&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&scope=read&state=state-example HTTP/1.1
Host: authorization.example
```

この例では、すべての parameter は HTTP header や request body ではなく Authorization Endpoint URI の query component にあります。

## 2. Authorization Server は request を検証して authorization decision を得る

RFC 6749 §4.1.1 では、Authorization Server は required parameter が存在し valid であることを確認します。request が valid であれば、Authorization Server は Resource Owner を認証し、Resource Owner に確認するか、その他の手段で approval を確立して authorization decision を得ます。

Resource Owner をどのように認証するかは RFC 6749 §3.1 の scope 外です。したがって、この記事では login method や authentication factor を追加しません。

<pre class="mermaid">
flowchart TD
    A[Client が Authorization Request を構成]
    A --> B[User-Agent が Authorization Endpoint へ request]
    B --> C[Authorization Server が request を検証]
    C --> D{redirect URI / client_id は valid?}
    D -->|No| E[invalid URI へ自動 redirect しない]
    D -->|Yes| F[Resource Owner の authorization decision]
    F --> G{access granted?}
    G -->|Yes| H[code と必要なら state を redirect URI へ返す]
    G -->|No| I[error と必要なら state を redirect URI へ返す]
</pre>

この図は RFC 6749 §4.1.1, §4.1.2, §4.1.2.1 の処理を示す**非規範的な要約**です。

## 3. 成功時は code を redirection URI の query component に返す

Resource Owner が access request を許可した場合、RFC 6749 §4.1.2 は Authorization Server が Authorization Code を発行し、redirection URI の query component に `application/x-www-form-urlencoded` 形式で次の parameter を追加すると定めています。

- **`code`:** REQUIRED。Authorization Server が生成した Authorization Code です。
- **`state`:** Authorization Request に `state` が含まれていた場合は REQUIRED で、Client から受け取った値をそのまま返します。

Authorization Code は発行後すぐに失効しなければならず（MUST）、最大 lifetime は 10 分が RECOMMENDED です。Client は Authorization Code を複数回使用してはなりません（MUST NOT）。これらは §4.1.2 の code に対する要件です。

次は response parameter の配置を示す**非規範的な例**です。code と state は illustrative value です。

```http
HTTP/1.1 302 Found
Location: https://client.example/cb?code=code-example&state=state-example
```

`code` と `state` は JSON response body ではなく、Client の redirection URI の query component にあります。

## 4. error を redirect できる場合と、してはならない場合を分ける

RFC 6749 §4.1.2.1 は、失敗の種類によって response の経路を分けています。

request が missing / invalid / mismatching redirection URI により失敗した場合、または `client_id` が missing / invalid である場合、Authorization Server は Resource Owner に error を知らせるべき（SHOULD）ですが、invalid redirection URI へ User-Agent を自動的に redirect してはなりません（MUST NOT）。

一方、Resource Owner が access request を拒否した場合、または redirection URI の missing / invalid 以外の理由で request が失敗した場合、Authorization Server は redirection URI の query component に error parameter を追加して Client に通知します。

- **`error`:** REQUIRED。§4.1.2.1 が定義する error code です。
- **`error_description`:** OPTIONAL。Client developer が error を理解するための human-readable ASCII text です。
- **`error_uri`:** OPTIONAL。error の説明を示す human-readable web page の URI です。
- **`state`:** Authorization Request に `state` が含まれていた場合は REQUIRED で、受け取った値をそのまま返します。

次は Resource Owner が request を拒否した場合の parameter 配置を示す**非規範的な例**です。

```http
HTTP/1.1 302 Found
Location: https://client.example/cb?error=access_denied&state=state-example
```

## 5. Authorization Endpoint 共通の parameter processing

RFC 6749 §3.1 は、値を持たない parameter を request から省略されたものとして扱わなければならない（MUST）と定めています。また、Authorization Server は認識しない request parameter を無視しなければなりません（MUST）。RFC 6749 が定義する request / response parameter は複数回含めてはなりません（MUST NOT）。

`response_type` が欠落している、または理解できない場合、Authorization Server は §3.1.1 に従って §4.1.2.1 の error response を返さなければなりません（MUST）。

## 6. この記事で扱わないこと

この記事は Authorization Endpoint で Authorization Code を取得する request / response に限定しています。取得済み code を Token Endpoint で交換する処理は別テーマです。PKCE、RFC 9700 が更新する Authorization Code security practice、JAR、PAR、OpenID Connect 固有の request parameter もここでは扱いません。

## 一次資料

- RFC 6749, *The OAuth 2.0 Authorization Framework*, §3.1, §3.1.1, §3.1.2, §4.1.1, §4.1.2, §4.1.2.1  
  https://www.rfc-editor.org/rfc/rfc6749.html
- RFC 6749 Inline Errata（§3.1 の verified erratum を確認）  
  https://www.rfc-editor.org/rfc/inline-errata/rfc6749.html

最終確認日: 2026-09-21
