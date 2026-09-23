---
layout: post
title: "FAPI 2.0 Message Signing：Authorization Response を JARM で署名・検証する"
date: 2026-09-23 11:45:00 +0900
categories: [authorization, oauth, fapi]
---

FAPI 2.0 Message Signing は、FAPI 2.0 Security Profile に基づく特定の request / response に署名を付与し、その署名を検証するためのプロファイルです。この記事では **Authorization Response の署名と Client による検証**だけを扱います。

## この記事について

**記事タイプ:** Flow / Requirement  
**対象読者:** FAPI 2.0 Message Signing の Authorization Response signing を実装・レビューする Client / Authorization Server 開発者  
**この記事で伝えること:** Authorization Server が JARM で signed authorization response を発行し、Client が `response_mode=jwt` を要求して JARM の検証規則に従って処理する流れ  
**扱わないこと:** Authorization Request の JAR/PAR、Introspection Response、ID Token、Resource Request / Response、JARM の全 response mode、Authorization Response encryption の詳細

## Article brief

- **Reader:** FAPI 2.0 Message Signing の Authorization Response signing を実装・レビューする Client / Authorization Server 開発者
- **Question:** Authorization Response signing を有効にした場合、Client と Authorization Server は何を要求され、JARM response はどこに配置され、Client は何を検証するのか
- **Answer:** Client は Authorization Request で `response_mode=jwt` を指定し、Authorization Server は JARM による signed authorization response を発行する。JARM JWT は `iss`、`aud`、`exp` と Authorization Response parameter を含み、Client は JARM の processing rules に従って issuer、audience、expiration、signature を検証してから response parameter を処理する
- **Scope:** FAPI 2.0 Message Signing §5.4、JARM §2.1、§2.3.4、§2.4
- **Out of scope:** Authorization Request signing、JARM encryption、Client / Authorization Server metadata の網羅、Token Endpoint、ID Token、Introspection Response
- **Primary sources:** OpenID Foundation FAPI 2.0 Message Signing Final §5.4、JWT Secured Authorization Response Mode for OAuth 2.0 (JARM) Final §2.1、§2.3.4、§2.4
- **Diagram:** Client の `response_mode=jwt` 指定から Authorization Server の signed JARM response、Client の検証までの sequence diagram

## 1. Authorization Response signing の位置

FAPI 2.0 Message Signing §5.4 は、Authorization Response signing を実装する Authorization Server に、JARM をサポートし、その使用を要求し、signed authorization response を発行することを **shall** としています（§5.4.1）。対応する Client は Authorization Request の `response_mode` を `jwt` に設定すること、および signed authorization response を JARM に従って検証することを **shall** とされています（§5.4.2）。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant AS as Authorization Server
    C->>AS: Authorization Request<br/>response_mode=jwt
    AS-->>C: redirect<br/>response=&lt;signed JWT&gt;
    C->>C: JARM JWT を検証
    C->>C: response parameter を処理
</pre>

図は Authorization Response signing に関係する部分だけを示しています。User Agent を介する HTTP redirect の詳細は省略しています。

## 2. `response_mode=jwt` は Authorization Request parameter

FAPI 2.0 Message Signing §5.4.2 は Client に `response_mode` を `jwt` に設定することを要求しています（shall）。`response_mode` は Authorization Request parameter です。

次は配置を示すための**非規範的な例**です。値は説明用です。

```http
GET /authorize?client_id=illustrative-client&response_type=code&response_mode=jwt&redirect_uri=https%3A%2F%2Fclient.example%2Fcb HTTP/1.1
Host: as.example
```

この例は `response_mode` の配置だけを示すために簡略化しています。FAPI 2.0 Security Profile が Authorization Request に課す他の要件を列挙する例ではありません。

## 3. JARM JWT に Authorization Response parameter を入れる

JARM §2.1 は、JWT に `iss`、`aud`、`exp` を含めます。また、対象 response type で定義される Authorization Endpoint response parameter を JWT に含めることを **MUST** としています。

response type が `code` の成功 response では、JARM §2.1.1 に従い `code` を含み、Authorization Request に `state` が含まれていた場合は `state` も含みます。

次は JWT payload の構造を示すための**非規範的な例**です。値は説明用であり、署名済み compact JWT そのものではありません。

```json
{
  "iss": "https://as.example",
  "aud": "illustrative-client",
  "exp": 1790136000,
  "code": "illustrative-code",
  "state": "illustrative-state"
}
```

- `iss`: Authorization Server の issuer URL
- `aud`: response の対象となる Client の `client_id`
- `exp`: JWT の expiration
- `code`: Authorization Code
- `state`: Client が request に `state` を含めた場合の値

FAPI 2.0 Message Signing §5.4.1 は RFC 9207 の `iss` Authorization Response parameter について、JARM §4.1 が Authorization Response parameter を JWT 内に置くことを要求するため、JWT の内側だけに含めるべきである（should）と注記しています。

## 4. `response_mode=jwt` では JWT は `response` query parameter に配置される

JARM §2.3.4 では `jwt` は response type に対応する既定の redirect encoding を選択する shortcut です。response type `code` の場合、既定は `query.jwt` です。

したがって、`code` と `response_mode=jwt` の組み合わせでは、JARM §2.3.1 に従って Authorization Server は Client の redirect URI の query component に `response` parameter を置き、その値として JWT を送ります。

次は配置を示すための**非規範的な例**です。JWT 値は説明用の placeholder です。

```http
HTTP/1.1 302 Found
Location: https://client.example/cb?response=illustrative-signed-jwt
```

ここで `code` や `state` を query parameter として JWT の外側に並べる例にはしていません。JARM §2.1 では Authorization Response parameter は JWT に格納されます。

## 5. Client は JWT の検証を終えてから `code` を処理する

FAPI 2.0 Message Signing §5.4.2 は Client に signed authorization response を JARM に従って検証することを要求しています（shall）。JARM §2.4 は Client の processing rules を定義しています。

Client は少なくとも次を処理します。

1. `iss` が期待している Authorization Server を識別するか確認します。不一致なら処理を中止して response を拒否することを **MUST** としています（JARM §2.4）。
2. `aud` が対応する Authorization Request で使用した Client ID と一致するか確認します。不一致なら処理を中止して response を拒否することを **MUST** としています（JARM §2.4）。
3. `exp` を確認します。JWT が有効でなければ処理を中止して response を拒否することを **MUST** としています（JARM §2.4）。
4. JWT signature を確認することを **MUST** とし、`alg` が `none` の JWT を受け入れてはならない **MUST NOT** としています（JARM §2.4）。
5. これらの確認がすべて成功する前に grant-type-specific な Authorization Response parameter を処理してはならない **MUST NOT** としています（JARM §2.4）。

JARM §2.4 では JWT の復号は OPTIONAL です。この記事は signed Authorization Response に範囲を限定しているため、暗号化された JARM response の処理は扱いません。

## 6. FAPI 2.0 Message Signing と JARM の役割

FAPI 2.0 Message Signing §5.4 は、Authorization Response signing を実装する場合に JARM の使用を要求し、Client と Authorization Server に追加の適合要件を設定します。一方、JWT response document の内容、`response_mode=jwt` の encoding、Client 側の具体的な JWT processing rules は JARM が定義しています。

**The profile requires signed authorization responses; JARM defines their JWT representation and processing.**  
（このプロファイルは署名付き Authorization Response を要求し、その JWT 表現と処理方法は JARM が定義します。）

なお FAPI 2.0 Message Signing §6.1 は、FAPI 2.0 の Authorization Response には confidential information がないため、security または confidentiality の目的では Authorization Response encryption は不要としています。この記事では署名と検証だけを扱い、encryption の構成や metadata は扱いません。

## Primary sources

- OpenID Foundation, **FAPI 2.0 Message Signing**, Final, §5.4, §6.1: <https://openid.net/specs/fapi-message-signing-2_0-final.html>
- OpenID Foundation, **JWT Secured Authorization Response Mode for OAuth 2.0 (JARM)**, Final, §2.1, §2.3.1, §2.3.4, §2.4: <https://openid.net/specs/oauth-v2-jarm-final.html>
