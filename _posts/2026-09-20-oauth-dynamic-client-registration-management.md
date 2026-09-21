---
layout: post
title: "RFC 7592：登録済み OAuth Client はどう参照・更新・削除するのか"
date: 2026-09-20 23:46:00 +0900
categories: [oauth, client-registration]
tags: [OAuth, RFC7592, Dynamic Client Registration]
---

**記事タイプ:** Flow / Feature Deep Dive  
**対象読者:** RFC 7591 で動的登録した OAuth Client の登録情報を、その後に参照・更新・削除する処理を実装・レビューする Client / Authorization Server 開発者  
**この記事で伝えること:** RFC 7592 の Client Configuration Endpoint で、Registration Access Token を使って GET / PUT / DELETE を行う位置と主要要件  
**扱わないこと:** RFC 7591 の初回 Client Registration Request の詳細、Client Metadata 各項目の一般的な意味、Registration Access Token の発行ポリシー、登録後の Authorization / Token flow

RFC 7592 は Experimental RFC です。すべての Dynamic Client Registration 対応 Authorization Server が、この registration management protocol をサポートするわけではありません（RFC 7592 §1）。

## 1. 初回登録と registration management は別の処理

RFC 7591 は Client Registration Endpoint への初回登録を定義します。RFC 7592 はその後の registration management を追加し、登録済み Client の現在の情報を参照・更新・削除する方法を定義します（RFC 7592 §1）。

RFC 7592 §3 では、management を利用する場合の Client Information Response に次の2つを含めます。

- `registration_client_uri`: REQUIRED。対象 Client の Client Configuration Endpoint の fully qualified URL。
- `registration_access_token`: REQUIRED。Client Configuration Endpoint への操作に使用する Access Token。

Client は `registration_client_uri` を自分で組み立てたり discovery したりせず、Authorization Server が返した URL をそのまま使用しなければなりません（MUST / MUST NOT、RFC 7592 Appendix B）。

<pre class="mermaid">
flowchart TD
    A[Client Information Response] --> B[registration_client_uri]
    A --> C[registration_access_token]
    B --> D[Client Configuration Endpoint]
    C --> D
    D --> E[GET: read]
    D --> F[PUT: update]
    D --> G[DELETE: deprovision]
</pre>

## 2. Registration Access Token は Bearer Token として提示する

Client Configuration Endpoint は OAuth 2.0 protected resource です。Client は、この endpoint へのすべての call で Registration Access Token を OAuth 2.0 Bearer Token として使用しなければなりません（MUST、RFC 7592 §2）。

次は配置を示すための**非規範的な例**です。URI と token value は illustrative value です。

```http
GET /register/client-123 HTTP/1.1
Host: authorization.example
Accept: application/json
Authorization: Bearer illustrative-registration-token
```

`registration_access_token` は JSON member として request body に送るのではなく、この例では RFC 6750 §2.1 の `Authorization` request header field に配置しています。

## 3. GET は現在の Client Configuration を読む

RFC 7592 §2.1 では、Client は Client Configuration Endpoint に HTTP `GET` request を送り、Registration Access Token で認証します。

成功時、Authorization Server は HTTP `200 OK` と `application/json` の Client Information Response を返します。

次は最小構造を示す**非規範的な例**です。

```http
HTTP/1.1 200 OK
Content-Type: application/json
Cache-Control: no-store

{
  "registration_client_uri": "https://authorization.example/register/client-123",
  "registration_access_token": "illustrative-new-registration-token",
  "client_id": "client-123",
  "redirect_uris": ["https://client.example/callback"]
}
```

read response で新しい `client_secret` または `registration_access_token` が返された場合、Client は以前の値を直ちに破棄しなければなりません（MUST、§2.1）。`client_id` は初回 registration response から変更されてはなりません（MUST NOT、§2.1）。

## 4. PUT は登録情報全体を更新する

RFC 7592 §2.2 の update は HTTP `PUT` です。`Content-Type` は `application/json` で、request entity は top-level member に metadata を持つ JSON object です。

update request は、直前の registration / read / update operation で Client に返された **すべての Client Metadata field** を含めなければなりません（MUST、§2.2）。これは部分更新ではありません。

次は配置を示す**非規範的な例**です。

```http
PUT /register/client-123 HTTP/1.1
Host: authorization.example
Authorization: Bearer illustrative-registration-token
Content-Type: application/json
Accept: application/json

{
  "client_id": "client-123",
  "redirect_uris": ["https://client.example/new-callback"],
  "client_name": "Illustrative Client"
}
```

Client は `client_id` を含めなければならず（MUST）、現在発行されている Client Identifier と同一でなければなりません（MUST、§2.2）。

一方、update request には `registration_access_token`、`registration_client_uri`、`client_secret_expires_at`、`client_id_issued_at` を含めてはなりません（MUST NOT、§2.2）。

valid な metadata value は既存値に追加されるのではなく置換されなければなりません（MUST、§2.2）。省略された field は Server により null または empty value として扱われなければなりません（MUST）。Authorization Server は、その null / empty value を他の value と同様に無視することもできます（MAY）。

成功時は HTTP `200 OK`、`Content-Type: application/json` の Client Information Response が返ります。

## 5. DELETE は Client を deprovision する

RFC 7592 §2.3 では、Client は Client Configuration Endpoint に HTTP `DELETE` request を送り、Registration Access Token で認証します。

次は**非規範的な例**です。

```http
DELETE /register/client-123 HTTP/1.1
Host: authorization.example
Authorization: Bearer illustrative-registration-token
```

成功すると `client_id`、`client_secret`、`registration_access_token` は invalid になります。Authorization Server は HTTP `204 No Content` を返さなければなりません（MUST、§2.3）。

```http
HTTP/1.1 204 No Content
Cache-Control: no-store
```

Authorization Server が delete method をサポートしない場合は HTTP 405 を返さなければなりません（MUST、§2.3）。Client に delete の permission がない場合は HTTP 403 を返さなければなりません（MUST）。

## 6. Client Information Response が management state を返す

RFC 7592 §3 の Client Information Response は `application/json` document で、parameter を JSON object の top-level member として返します。

Authorization Server は、この Client に登録されている metadata をすべて返さなければなりません（MUST、§3）。また、Client が要求した metadata value を reject または適切な value に置換できます（MAY）。

`registration_client_uri` は management 対象となる Client 固有の endpoint を示し、`registration_access_token` はその endpoint に対する後続 operation の credential です。初回 registration で使われ得る Initial Access Token や、Token Endpoint で使う `client_secret` とは用途が異なります（RFC 7592 Appendix A）。

## 7. この記事と RFC 7591 の記事の境界

RFC 7591 の Dynamic Client Registration は、Client Registration Endpoint に metadata を POST して `client_id` 等を取得する初回登録がテーマです。

この記事は、初回登録後に RFC 7592 の Client Configuration Endpoint を使って registration state を GET / PUT / DELETE する処理だけを扱います。Client Metadata の一般的な定義や初回 registration request / response の詳細は RFC 7591 の記事側の範囲です。

## 一次資料

- RFC Editor: [RFC 7592 — OAuth 2.0 Dynamic Client Registration Management Protocol](https://www.rfc-editor.org/rfc/rfc7592.html)
- RFC Editor: [RFC 6750 — The OAuth 2.0 Authorization Framework: Bearer Token Usage](https://www.rfc-editor.org/rfc/rfc6750.html)

参照した主要節: RFC 7592 §1, §1.3, §2, §2.1, §2.2, §2.3, §3, Appendix A, Appendix B; RFC 6750 §2.1  
最終確認: 2026-09-21
