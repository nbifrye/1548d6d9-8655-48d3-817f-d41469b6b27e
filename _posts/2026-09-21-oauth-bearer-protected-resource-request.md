---
layout: post
title: "OAuth Bearer Token：Protected Resource request と WWW-Authenticate"
date: 2026-09-21 21:40:00 +0900
categories: [oauth]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth Bearer Access Token を使う Protected Resource request と Resource Server の error response を実装・レビューする開発者  
**この記事で伝えること:** Bearer Access Token を HTTP request のどこに配置するか、Resource Server がどのように challenge / error を返すか、RFC 9700 によって URI query parameter の扱いがどう制約されるかを理解する  
**扱わないこと:** Access Token の発行、JWT Access Token の内部構造、Token Introspection、DPoP、mTLS certificate-bound Access Token、Resource Server 固有の authorization policy

## Article brief

- **Reader:** Bearer Access Token を受け取る API Client / Resource Server を実装・レビューする開発者
- **Question:** Client は Bearer Access Token を Protected Resource request のどこに置き、Resource Server は token がない・invalid・scope 不足の場合にどの HTTP response を返すのか
- **Answer:** `Authorization: Bearer` が RFC 6750 の主要な送信方法であり、1 request で複数の token transmission method を併用してはならないこと、form body method の条件、RFC 9700 により URI query parameter method は現在 MUST NOT であること、`WWW-Authenticate` と標準 error code の response semantics を説明できる
- **Scope:** RFC 6750 §2, §3, §3.1 と RFC 9700 §4.3.2
- **Out of scope:** Access Token issuance、token format / claims、introspection、sender-constrained token、Resource Server の local authorization policy
- **Primary sources:** RFC 6750 §2, §3, §3.1; RFC 9700 §4.3.2
- **Diagram:** Client が Bearer token を Protected Resource request に載せ、Resource Server が request を処理して success または Bearer challenge を返す sequence diagram

## 1. Bearer Token は Protected Resource request で提示する

RFC 6750 §2 は、Bearer Access Token を Resource Server への HTTP request で送信する方法を定義しています。Client は1つの request で token を送信する方法を複数使用してはなりません（MUST NOT, RFC 6750 §2）。

<pre class="mermaid">
sequenceDiagram
    participant C as Client
    participant R as Resource Server
    C->>R: Protected Resource request + Bearer token
    alt request accepted
        R-->>C: Protected Resource response
    else token missing / rejected
        R-->>C: HTTP error + WWW-Authenticate
    end
</pre>

この図は RFC 6750 §2–§3 の処理関係を示す**非規範的な図**です。

## 2. Authorization request header field

RFC 6750 §2.1 では、Client が `Authorization` request header field を使用する場合、`Bearer` authentication scheme で Access Token を送信します。Client はこの方法を使用すべきです（SHOULD）。Resource Server はこの方法をサポートしなければなりません（MUST）。

次は token の配置を示す**非規範的な例**です。token value は illustrative value です。

```http
GET /resource HTTP/1.1
Host: api.example
Authorization: Bearer illustrative-access-token
```

`Authorization` は HTTP request header field です。Bearer credential は `Bearer`、1個以上の space、token value の順に置かれます（RFC 6750 §2.1）。

## 3. Form-encoded request body

RFC 6750 §2.2 は、`access_token` parameter を HTTP request body に置く方法も定義しています。この方法を使用するには、`Content-Type` が `application/x-www-form-urlencoded` であること、body が single-part であること、body content が ASCII のみであること、request body に定義された semantics を持つ HTTP method を使うことなど、同 section の条件をすべて満たす必要があります（MUST NOT unless）。特に GET method では使用してはなりません（MUST NOT）。

RFC 6750 §2.2 では、この方法は participating browser が `Authorization` request header field にアクセスできない application context を除き、使用すべきではありません（SHOULD NOT）。Resource Server はこの方法をサポートしてもかまいません（MAY）。

次は配置を示す**非規範的な例**です。

```http
POST /resource HTTP/1.1
Host: api.example
Content-Type: application/x-www-form-urlencoded

access_token=illustrative-access-token
```

ここで `access_token` は HTTP header ではなく、form-encoded request body の parameter です。

## 4. URI query parameter は RFC 9700 で MUST NOT

RFC 6750 §2.3 は、`access_token` を URI query component に置く方法を記述しています。同 section 自体は、この方法を、header field または request body で token を送れない場合を除き使用すべきではない（SHOULD NOT）としていました。

その後の OAuth 2.0 Security Best Current Practice である RFC 9700 §4.3.2 は、この扱いを強化しています。Client は RFC 6750 §2.3 に記述された方法で Access Token を URI query parameter に渡してはなりません（MUST NOT）。

次は**使用してはならない配置を識別するための非規範的な構造例**です。実装例として推奨するものではありません。

```text
/resource?access_token=illustrative-access-token
```

`access_token` が URI query component に置かれていることが、RFC 9700 §4.3.2 の MUST NOT の対象です。

## 5. WWW-Authenticate challenge

RFC 6750 §3 では、Protected Resource request に authentication credential がない場合、または Resource への access を可能にする Access Token が含まれていない場合、Resource Server は `WWW-Authenticate` response header field を含めなければなりません（MUST）。この specification が定義する challenge は `Bearer` auth-scheme を使用しなければなりません（MUST）。

次は credential を含まない request に対する**非規範的な最小例**です。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="illustrative"
```

RFC 6750 §3 は、request に authentication information が含まれていなかった場合、Resource Server は `error` またはその他の error information を含めるべきではない（SHOULD NOT）としています。

## 6. invalid_request / invalid_token / insufficient_scope

RFC 6750 §3.1 は Protected Resource access error として3つの error code を定義します。

- **`invalid_request`:** request が malformed である場合です。Resource Server は `400 Bad Request` を返すべきです（SHOULD）。
- **`invalid_token`:** token が expired、revoked、malformed、またはその他の理由で invalid な場合です。Resource Server は `401 Unauthorized` を返すべきです（SHOULD）。
- **`insufficient_scope`:** request に必要な privilege が token にない場合です。Resource Server は `403 Forbidden` を返すべきであり（SHOULD）、必要な scope を示す `scope` attribute を含めてもかまいません（MAY）。

次は expired token を表すための**非規範的な例**です。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer realm="illustrative",
  error="invalid_token",
  error_description="access token expired"
```

`WWW-Authenticate` は HTTP response header field です。`error`、`error_description`、`error_uri`、`scope` は Bearer challenge の auth-param として定義されており、Token Endpoint の JSON error response member とは配置が異なります。

## 7. この記事の範囲

この記事は、Bearer Access Token を Protected Resource request に載せる位置と、その request に対する Resource Server の HTTP challenge / error response に限定しています。Access Token の取得方法や内部形式は扱いません。

また、RFC 9700 が RFC 6750 §2.3 の URI query parameter method を MUST NOT としているため、RFC 6750 §2.3 だけを読んだ場合の規範強度と現在の BCP を区別して記載しています。

## Primary sources

- RFC 6750, §2 “Authenticated Requests”  
  https://www.rfc-editor.org/rfc/rfc6750.html#section-2
- RFC 6750, §3 “The WWW-Authenticate Response Header Field”  
  https://www.rfc-editor.org/rfc/rfc6750.html#section-3
- RFC 6750, §3.1 “Error Codes”  
  https://www.rfc-editor.org/rfc/rfc6750.html#section-3.1
- RFC 9700, §4.3.2 “Access Token in Browser History”  
  https://www.rfc-editor.org/rfc/rfc9700.html#section-4.3.2
