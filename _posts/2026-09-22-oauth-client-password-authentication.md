---
layout: post
title: "OAuth 2.0 の client password authentication：HTTP Basic と request body の配置"
date: 2026-09-22 03:44:00 +0900
categories: [oauth, authentication]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** OAuth 2.0 の client password を使う client authentication について、credential の配置と Authorization Server の要件を確認したい実装者  
**この記事で伝えること:** RFC 6749 §2.3.1 が定義する HTTP Basic authentication と request body parameter による client password authentication の配置、およびそれぞれに対する規範要件  
**扱わないこと:** confidential / public の Client Type 判定、JWT や mTLS による client authentication、grant type 固有の処理、Access Token の検証

## Article brief

- **Reader:** client password を使う OAuth Client / Authorization Server の実装者
- **Question:** `client_id` と client password は HTTP request のどこに置かれ、Authorization Server はどの方法をサポートする必要があるのか
- **Answer:** RFC 6749 §2.3.1 では、client password を持つ Client は HTTP Basic authentication を使用でき、Authorization Server は client password を発行した Client のために HTTP Basic をサポートしなければならない。Authorization Server は `client_id` / `client_secret` を request body で受け取る方法もサポートできるが、その方法には追加の制約がある
- **Scope:** RFC 6749 §2.3, §2.3.1 に定義された client password authentication、HTTP `Authorization` header と request body parameter の配置、TLS と brute-force protection の要件
- **Out of scope:** Client Type の判定、JWT client authentication、mTLS client authentication、個別 grant の validation、credential rotation policy
- **Primary sources:** RFC 6749 §2.3, §2.3.1, Appendix B
- **Diagram:** client password authentication の2つの配置と Authorization Server の support requirement を示す flowchart

## client password authentication には2つの配置が定義されている

RFC 6749 §2.3.1 は、client password を持つ Client の authentication について、HTTP Basic authentication scheme と、`client_id` / `client_secret` を request body に含める方法を定義しています。

Client は1つの request で複数の authentication method を使用してはなりません（**MUST NOT**, RFC 6749 §2.3）。したがって、同一 request で HTTP Basic と request body の client credential を併用することはできません。

```mermaid
flowchart TD
    A[Client password を持つ Client] --> B{credential の配置}
    B --> C[Authorization header: Basic]
    B --> D[request body]
    C --> E[AS は support MUST]
    D --> F[AS は support MAY]
```

この図は RFC 6749 §2.3.1 の配置と support requirement を要約したものです。新しい authentication method を追加するものではありません。

## HTTP Basic authentication

client password を持つ Client は、Authorization Server に対する authentication に HTTP Basic authentication scheme を使用してもよい（**MAY**, RFC 6749 §2.3.1）とされています。

この方法では、`client_id` と client password を RFC 6749 Appendix B の `application/x-www-form-urlencoded` encoding algorithm でそれぞれ encode し、encoded `client_id` を username、encoded client password を password として HTTP Basic authentication に使用します。

Authorization Server は、client password を発行された Client の authentication のために HTTP Basic authentication scheme をサポートしなければなりません（**MUST**, RFC 6749 §2.3.1）。

以下は配置を確認するための**非規範的な例**です。credential の値は illustrative value です。

```http
POST /token HTTP/1.1
Host: as.example
Authorization: Basic aWxsdXN0cmF0aXZlLWNsaWVudDppbGx1c3RyYXRpdmUtc2VjcmV0
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials
```

この例では client credential は HTTP `Authorization` header にあり、request body には grant parameter だけがあります。Base64 表現そのものに追加の OAuth semantics はありません。

## request body に `client_id` と `client_secret` を置く方法

RFC 6749 §2.3.1 は、Authorization Server が client credential を request body で受け取る方法をサポートしてもよい（**MAY**）としています。

この方法の parameter は次のとおりです。

- `client_id`: REQUIRED。Client registration で発行された client identifier。
- `client_secret`: REQUIRED。client secret。ただし client secret が空文字列の場合、Client は parameter を省略してもよい（**MAY**）。

以下は配置を確認するための**非規範的な例**です。値は illustrative value です。

```http
POST /token HTTP/1.1
Host: as.example
Content-Type: application/x-www-form-urlencoded

grant_type=client_credentials&client_id=illustrative-client&client_secret=illustrative-secret
```

`client_id` と `client_secret` は `application/x-www-form-urlencoded` の request body parameter です。この2つの parameter は request body でのみ送信でき、request URI に含めてはなりません（**MUST NOT**, RFC 6749 §2.3.1）。

RFC 6749 §2.3.1 は、この request body による方法を **NOT RECOMMENDED** とし、HTTP Basic authentication scheme または他の password-based HTTP authentication scheme を直接利用できない Client に限定すべき（**SHOULD**）としています。

## password authentication request に対する Authorization Server の要件

RFC 6749 §2.3.1 は、password authentication を使用する request を送る際、Authorization Server が §1.6 に記載された TLS の使用を要求しなければならない（**MUST**）と規定しています。

また、この client authentication method は password を使用するため、Authorization Server は、それを利用する endpoint を brute-force attack から保護しなければなりません（**MUST**, RFC 6749 §2.3.1）。仕様は、この section で具体的な protection mechanism を1つに定めていません。

## まとめ

RFC 6749 §2.3.1 では、client password を持つ Client は HTTP Basic authentication を使用できます（**MAY**）。Authorization Server は、client password を発行した Client に対して HTTP Basic authentication をサポートしなければなりません（**MUST**）。

Authorization Server は `client_id` と `client_secret` を request body で受け取る方法もサポートできます（**MAY**）が、この方法は **NOT RECOMMENDED** であり、HTTP Basic などを直接利用できない Client に限定すべきです（**SHOULD**）。body parameter は request URI に置いてはなりません（**MUST NOT**）。

## 一次資料

- RFC Editor, [RFC 6749: The OAuth 2.0 Authorization Framework](https://www.rfc-editor.org/rfc/rfc6749.html), §2.3, §2.3.1, Appendix B

最終確認: 2026-09-22
