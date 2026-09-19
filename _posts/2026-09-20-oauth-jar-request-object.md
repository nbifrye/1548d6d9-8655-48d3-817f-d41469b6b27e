---
layout: post
title: "RFC 9101：JAR の Request Object は Authorization Request をどう表現するのか"
date: 2026-09-20 01:44:00 +0900
categories: [oauth, authorization]
---

## この記事について

**記事タイプ:** Feature Deep Dive  
**対象読者:** OAuth 2.0 の Authorization Request を実装・レビューし、JWT-Secured Authorization Request（JAR）の `request` / `request_uri` を扱う開発者  
**この記事で伝えること:** Request Object が Authorization Request parameter を JWT Claims Set に保持し、`request` または `request_uri` として Authorization Endpoint に渡される構造と、Authorization Server が検証する要点  
**扱わないこと:** PAR の push 処理、Authorization Response、FAPI 固有要件、個別の暗号アルゴリズム選定、JWS / JWE 一般の詳細

## Article brief

- **Reader:** OAuth Client / Authorization Server 実装者
- **Question:** JAR では Authorization Request parameter をどのデータ構造に入れ、Authorization Endpoint へどのように渡し、Authorization Server は何を検証するのか
- **Answer:** Request Object の Claims Set、`request` / `request_uri` の配置、外側の `client_id` との関係、署名・暗号化された Request Object の基本的な検証境界を区別できる
- **Scope:** RFC 9101 §2、§5、§6 の Request Object、Authorization Request、JWT-based request validation
- **Out of scope:** RFC 9126 PAR、Authorization Response、FAPI profile、algorithm selection、JWS / JWE 自体の詳細
- **Primary sources:** RFC 9101
- **Diagram:** Client が Request Object を作成し、Authorization Endpoint に渡し、Authorization Server が検証する flowchart

## 1. Request Object は Authorization Request parameter を JWT Claims Set に保持する

RFC 9101 §2.1 は Request Object を、OAuth 2.0 Authorization Request parameter を JSON 形式で保持する JWT として定義しています。Authorization Request parameter は JWT Claims Set の member として表現されます。

RFC 9101 §2.2 では、Request Object の parameter name と string value は JSON string として含めなければならず（MUST）、JSON string は UTF-8 で encode しなければなりません（MUST）。数値は JSON number として含めなければなりません（MUST）。また、Request Object は extension parameter を含めてもかまいません（MAY）。

Request Object は JWS で署名するか、JWS で署名したうえで JWE で暗号化します。RFC 9101 §5 は Authorization Request Object がこのいずれかでなければならないと規定しています（MUST）。

以下は構造を示すための**非規範的な例**です。値は illustrative value です。

```json
{
  "iss": "client-123",
  "aud": "https://authorization.example",
  "response_type": "code",
  "client_id": "client-123",
  "redirect_uri": "https://client.example/cb",
  "scope": "read",
  "state": "state-123"
}
```

これは署名・encode 前の Claims Set を示しています。`response_type`、`client_id`、`redirect_uri`、`scope`、`state` は Authorization Request parameter です。

RFC 9101 §2.2 では、署名された Request Object は `iss` と `aud` claim を含むことが SHOULD とされています。`aud` の値は Authorization Server の issuer value とすることが SHOULD です。

<pre class="mermaid">
flowchart TD
    A[Client が Authorization Request parameter を用意]
    A --> B[Request Object の Claims Set に格納]
    B --> C[JWS 署名]
    C --> D{JWE 暗号化するか}
    D -->|しない| E[request または request_uri で渡す]
    D -->|する| F[JWE 暗号化]
    F --> E
    E --> G[Authorization Server が検証]
</pre>

## 2. Authorization Endpoint では `request` または `request_uri` を query parameter に置く

RFC 9101 §5 では、Client は Authorization Endpoint URI の query component に `application/x-www-form-urlencoded` 形式で parameter を追加します。

- **HTTP method:** Authorization Endpoint への request。RFC 9101 の例は `GET`
- **`request`:** query parameter。`request_uri` を指定しない場合は REQUIRED
- **`request_uri`:** query parameter。`request` を指定しない場合は REQUIRED
- **`client_id`:** query parameter。REQUIRED
- **Request Object:** `request` の値として直接渡すか、`request_uri` が参照する resource として渡す

`request` と `request_uri` を同時に含めてはなりません（MUST NOT, RFC 9101 §5）。また、外側の `client_id` は Request Object 内の `client_id` と一致しなければなりません（MUST, §5）。

以下は `request` を使用する場合の**非規範的な例**です。JWT は構造を示すため省略表記しています。

```http
GET /authorize?client_id=client-123&request=eyJ...signature HTTP/1.1
Host: authorization.example
```

`request` は query parameter であり、その値が Request Object です。Request Object 自体は JSON object をそのまま query に置くのではなく、JWT として渡されます。

`request_uri` を使用する場合は、Request Object を参照する absolute URI を query parameter に置きます。

```http
GET /authorize?client_id=client-123&request_uri=https%3A%2F%2Fclient.example%2Frequest.jwt HTTP/1.1
Host: authorization.example
```

この例も非規範的です。RFC 9101 §2.2 は Request Object URI を absolute URI と定義しています。

## 3. 外側に重複した parameter があっても Request Object 内を使用する

RFC 9101 §5 は、後方互換性などのために Client が Request Object 内の parameter を query parameter に重複して送ることを MAY としています。

ただし、JAR をサポートする Authorization Server は Request Object に含まれる parameter だけを使用しなければなりません（MUST, §5）。

したがって、JAR では「JWT の外側にも同名 parameter があるか」ではなく、「Authorization Server が Request Object 内の値を Authorization Request として処理する」という境界が仕様上明確です。

## 4. Authorization Server は署名済み Request Object を検証する

RFC 9101 §6.2 は、Authorization Server が JWS-signed Request Object の signature を検証しなければならないと規定しています（MUST）。`kid` Header Parameter が存在する場合、その `kid` で識別される key を使用しなければならず（MUST）、その key は Client に関連付けられた key でなければなりません（MUST）。

署名は Client に関連付けられた key と `alg` Header Parameter で指定された algorithm を用いて検証しなければなりません（MUST）。Algorithm verification も RFC 8725 §3.1、§3.2 に従って実施しなければなりません（MUST, RFC 9101 §6.2）。

Request Object が JWE で暗号化されている場合、Authorization Server は RFC 7516 に従って JWT を復号しなければなりません（MUST, RFC 9101 §6.1）。復号に失敗した場合は `invalid_request_object` error を返さなければなりません（MUST, §6.1）。復号結果は signed Request Object です。

RFC 9101 §6.3 では、Request Object の `client_id` と Authorization Request の `client_id` が同一でなければならないと規定されています（MUST）。この check または request validation が失敗した場合、Authorization Server は OAuth 2.0 の Authorization Request error として応答しなければなりません（MUST）。

## 5. `request_uri` と PAR の `request_uri` は同じ名前でも生成経路が異なる

RFC 9101 の `request_uri` は Request Object URI を表す Authorization Request parameter です。一方、RFC 9126 PAR では Authorization Server が Pushed Authorization Request を受理した後に `request_uri` を発行します。

この記事では RFC 9101 の Request Object とその参照方法だけを扱います。PAR Endpoint への POST、PAR response の `request_uri` / `expires_in`、Authorization Server が発行した PAR の request URI の処理は、PAR の記事で扱います。

## まとめ

JAR の Request Object は Authorization Request parameter を JWT Claims Set に保持します。Client は Authorization Endpoint の query component に `client_id` と、`request` または `request_uri` を置きます。`request` と `request_uri` は同時に使用できません（MUST NOT, RFC 9101 §5）。

Authorization Server は Request Object の署名を検証し（MUST, §6.2）、暗号化されている場合は先に復号します（MUST, §6.1）。外側の `client_id` と Request Object 内の `client_id` も一致しなければなりません（MUST, §5、§6.3）。

**The Request Object is the authorization request data structure; `request` and `request_uri` are the mechanisms used to carry or reference it.**  
（Request Object が Authorization Request のデータ構造であり、`request` と `request_uri` はそれを直接運ぶ、または参照するための仕組みです。）

## 一次資料

- RFC 9101, *The OAuth 2.0 Authorization Framework: JWT-Secured Authorization Request (JAR)*, §2, §5, §6
  - https://www.rfc-editor.org/rfc/rfc9101.html
