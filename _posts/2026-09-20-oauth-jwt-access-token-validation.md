---
layout: post
title: "RFC 9068：JWT Access Token を Resource Server はどう検証するのか"
date: 2026-09-20 06:46:00 +0900
categories: [oauth, jwt, access-token]
---

## この記事について

**記事タイプ:** Requirement  
**対象読者:** RFC 9068 に準拠した JWT Access Token を受け取る OAuth Resource Server の実装・レビュー担当者  
**この記事で伝えること:** RFC 9068 の JWT Access Token の識別に使う `typ`、必須 Claims、および Resource Server が §4 に従って行う検証  
**扱わないこと:** opaque token の Token Introspection、Access Token の発行フロー、独自 Claim に基づく認可ポリシー、sender-constrained Access Token の proof-of-possession 検証

## 1. RFC 9068 は JWT 形式の Access Token に共通プロファイルを定める

OAuth 2.0 自体は Access Token の形式を規定していません。RFC 9068 §1 は、JWT 形式で Access Token を発行・利用するための相互運用可能な profile を定義しています。

RFC 9068 に準拠する JWT Access Token は、単に JWT として parse できればよいわけではありません。§2 が Header と Claims の要件を定め、§4 が Resource Server に validation requirements を定めています。

本記事では Resource Server 側の検証に範囲を限定します。

## 2. JWT Access Token の Header と必須 Claims

### 2.1 Header

RFC 9068 §2.1 により、JWT Access Token は署名されていなければなりません（MUST）。署名 algorithm に `none` を使用してはなりません（MUST NOT）。

また、Authorization Server と Resource Server は、サポートする signature algorithm に `RS256` を含めなければなりません（MUST）。これは、すべての token を RS256 で署名しなければならないという要件ではありません。

JWT Access Token は `typ` Header Parameter に `application/at+jwt` media type を含めなければなりません（MUST）。RFC 9068 §2.1 は `application/` prefix を省略した `at+jwt` を使用することを SHOULD としています。

以下は構造を確認するための**非規範的な例**です。値は illustrative value です。

```json
{
  "typ": "at+jwt",
  "alg": "RS256",
  "kid": "illustrative-key-1"
}
```

ここで `typ`、`alg`、`kid` は JWT の JOSE Header に置かれます。`kid` はこの例で鍵を識別するために示した値であり、RFC 9068 §2.1 がすべての JWT Access Token に必須としている Header Parameter ではありません。

### 2.2 Claims Set

RFC 9068 §2.2 が JWT Access Token に REQUIRED としている Claims は次の7つです。

- `iss`: issuer。RFC 7519 §4.1.1 で定義される値
- `exp`: expiration time。RFC 7519 §4.1.4 で定義される値
- `aud`: audience。RFC 7519 §4.1.3 で定義される値
- `sub`: subject。RFC 7519 §4.1.2 で定義される値
- `client_id`: Client identifier。RFC 8693 §4.3 で定義される値
- `iat`: token の発行時刻。RFC 7519 §4.1.6 で定義される値
- `jti`: JWT identifier。RFC 7519 §4.1.7 で定義される値

以下は必須 Claims の配置と型のイメージを示すための**非規範的な最小例**です。文字列や時刻値は illustrative value です。

```json
{
  "iss": "https://as.example/",
  "sub": "illustrative-subject",
  "aud": "https://rs.example/",
  "exp": 1790003600,
  "iat": 1790000000,
  "jti": "illustrative-token-id",
  "client_id": "illustrative-client"
}
```

これらは HTTP parameter ではなく、JWT Claims Set の member です。

RFC 9068 §2.2 には `auth_time`、`acr`、`amr`、`scope` など、条件に応じて利用される追加 Claims も定義されています。本記事では Resource Server の基本 validation procedure に焦点を当てるため、それらの意味や発行条件の詳細は扱いません。

## 3. HTTP request では Access Token は Authorization header に置ける

RFC 9068 は JWT Access Token のデータ形式と検証を定める profile です。Bearer token を HTTP request の `Authorization` header で送る形式は RFC 6750 §2.1 が定義しています。

以下は配置を示すための**非規範的な例**です。`JWT_ACCESS_TOKEN_VALUE` は illustrative placeholder です。

```http
GET /resource HTTP/1.1
Host: rs.example
Authorization: Bearer JWT_ACCESS_TOKEN_VALUE
```

この例では JWT Access Token は request body や query parameter ではなく、`Authorization` HTTP header の Bearer credentials に置かれています。

RFC 6750 §2.1 は Client が Bearer scheme を使用する場合、`Authorization` request header field で token を送信することを SHOULD としています。Resource Server はこの method をサポートしなければなりません（MUST）。

## 4. Resource Server が行う validation

RFC 9068 §4 は、JWT Access Token を受け取った Resource Server が実施しなければならない validation を定めています。

<pre class="mermaid">
flowchart TD
    A[JWT Access Token を受信]
    A --> B[typ を確認]
    B --> C[必要なら復号]
    C --> D[iss を完全一致で確認]
    D --> E[aud を確認]
    E --> F[署名と alg を検証]
    F --> G[exp を確認]
    G --> H[検証成功]
</pre>

この図は RFC 9068 §4 の検証項目を読みやすく並べた**非規範的な整理**です。仕様本文の要件を置き換えるものではありません。

### 4.1 `typ` を確認する

Resource Server は `typ` Header Parameter が `at+jwt` または `application/at+jwt` であることを検証しなければならず（MUST）、それ以外の値を持つ token を拒否しなければなりません（MUST）。RFC 9068 §4 の要件です。

この explicit typing は、同じ JWT データ構造を利用する別種の token と JWT Access Token を区別するための検証項目です。

### 4.2 暗号化されている場合は復号する

JWT Access Token が encrypted である場合、Resource Server は registration 時に指定した key と algorithm を使って復号します（RFC 9068 §4）。

Authorization Server との registration 時に encryption が negotiated されているにもかかわらず、受信した JWT Access Token が encrypted でない場合、Resource Server は拒否することを SHOULD とされています。

どの deployment で encryption を negotiate するかは、本記事では扱いません。

### 4.3 `iss` は期待する issuer identifier と完全一致させる

Resource Server は Authorization Server の issuer identifier と JWT Access Token の `iss` Claim を完全一致で比較しなければなりません（MUST, RFC 9068 §4）。

RFC 9068 §4 は issuer identifier を通常 discovery で取得するものとして説明しています。また、Authorization Server は RFC 8414 の Authorization Server Metadata を利用し、`issuer` と `jwks_uri` を Resource Server に公開することを SHOULD としています。

### 4.4 `aud` に自分自身を表す resource indicator が含まれることを確認する

Resource Server は `aud` Claim に、自身について期待する identifier に対応する resource indicator が含まれていることを検証しなければなりません（MUST, RFC 9068 §4）。

現在の Resource Server を valid audience とする resource indicator が `aud` に含まれていない JWT Access Token は拒否しなければなりません（MUST）。

`aud` の具体的な identifier を deployment でどう設定するかについて、本記事では独自の規則を追加しません。

### 4.5 署名を検証し、`alg: none` を拒否する

Resource Server は受信したすべての JWT Access Token の署名を RFC 7515 に従って検証しなければなりません（MUST, RFC 9068 §4）。検証には JWT の `alg` Header Parameter で指定された algorithm と、Authorization Server が提供した key を使用します。

`alg` が `none` の JWT は拒否しなければなりません（MUST）。

RFC 9068 §4 は、Authorization Server が JWT Access Token の署名に asymmetric algorithm を使用することを RECOMMENDED としています。また、署名鍵の公開には RFC 8414 の `jwks_uri` を使用することを SHOULD としています。

### 4.6 `exp` と現在時刻を比較する

Resource Server は現在時刻が `exp` Claim が表す時刻より前であることを確認しなければなりません（MUST, RFC 9068 §4）。

実装は clock skew を考慮するため、小さな leeway を設けることができます（MAY）。RFC 9068 §4 は通常数分以内と記述していますが、特定の固定値を規範要件として定めてはいません。

したがって、本記事でも独自の許容秒数は指定しません。

## 5. validation failure は `invalid_token` として扱う

RFC 9068 §4 は、Resource Server が error を RFC 6750 §3.1 に従って処理しなければならない（MUST）としています。

§4 に列挙された validation check のいずれかが失敗した場合、response には `invalid_token` error code を含めなければなりません（MUST）。

以下は HTTP 上の配置を示すための**非規範的な例**です。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: Bearer error="invalid_token"
```

RFC 6750 §3.1 では、request に authentication credentials が含まれていたものの Access Token が expired、revoked、malformed、その他の理由で invalid である場合、Resource Server は `401` status code で応答することを定めています。

## 6. token validation と authorization decision は同じ処理ではない

RFC 9068 §4 は、JWT Access Token に §2.2.3 の authorization Claims が含まれる場合、Resource Server がそれらを他の contextual information と組み合わせ、現在の call を許可するか拒否するか判断することを SHOULD としています。

一方、その authorization check の詳細は RFC 9068 の scope 外です。

したがって、`typ`、issuer、audience、signature、expiration の validation に成功したという事実だけから、個別 resource operation の authorization policy まで仕様が一意に決めるわけではありません。本記事もその policy を追加しません。

## 7. Client は JWT Access Token の中身を処理対象にしない

JWT Access Token は Client から見ても JWT として decode できる場合があります。しかし RFC 9068 §6 は、Client が Access Token の内容を inspect してはならない（MUST NOT）としています。

Authorization Server と Resource Server は token format を変更でき、OAuth 2.0 framework は Client が Access Token を opaque な値として扱うことを前提としています。

この点は Resource Server による JWT validation と区別する必要があります。JWT Access Token の Claims を検証する主体は、本記事の scope では Resource Server です。

## 8. まとめ

RFC 9068 の JWT Access Token validation では、「JWT として読めること」だけでは検証完了になりません。

Resource Server は RFC 9068 §4 に従い、`typ` が `at+jwt` または `application/at+jwt` であること、`iss` が期待する issuer と完全一致すること、`aud` が自身を valid audience として含むこと、署名が Authorization Server の key で検証できること、`alg` が `none` ではないこと、現在時刻が `exp` より前であることを検証します。

RFC 9068 §2.2 はさらに、JWT Access Token の共通データ構造として `iss`、`exp`、`aud`、`sub`、`client_id`、`iat`、`jti` を REQUIRED としています。

## 一次資料

- RFC 9068, *JSON Web Token (JWT) Profile for OAuth 2.0 Access Tokens*, §1, §2, §4, §6  
  https://www.rfc-editor.org/rfc/rfc9068.html
- RFC 6750, *The OAuth 2.0 Authorization Framework: Bearer Token Usage*, §2.1, §3.1  
  https://www.rfc-editor.org/rfc/rfc6750.html