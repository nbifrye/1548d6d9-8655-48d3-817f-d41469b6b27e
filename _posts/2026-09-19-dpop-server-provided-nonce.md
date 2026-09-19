---
layout: post
title: "RFC 9449：DPoP nonce はどう要求され、次の proof にどう入るのか"
date: 2026-09-19 12:47:00 +0900
categories: [authorization, oauth, dpop]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** DPoP nonce を実装・レビューする OAuth Client / Authorization Server / Resource Server 開発者  
**この記事で伝えること:** Server が `DPoP-Nonce` を返し、Client がその値を次の DPoP proof の `nonce` claim に入れて request を再送する処理  
**扱わないこと:** DPoP proof 全般の claim 検証、access token の key binding、authorization code binding、nonce を要求する時期を決める local policy


既存の「DPoP proof は HTTP request の何を証明するのか」は DPoP proof の構造と protected resource access 時の検証を扱い、DPoP nonce を明示的に scope 外としています。本記事は server-provided nonce の往復だけを扱います。

## 1. nonce は Server が Client に渡す値である

RFC 9449 §8 は、Authorization Server が Client に DPoP nonce を提供できる（MAY）と規定しています。Server が nonce を必要と判断する時期を決めるロジックは RFC 9449 の scope 外です。

Nonce value は予測不可能でなければなりません（MUST, §8）。Client にとって nonce は opaque です。

RFC 9449 §9 は Resource Server も nonce を提供できると規定しています。Authorization Server と Resource Server が発行する nonce は別のものであり、発行した Server でのみ使用されます。

<pre class="mermaid">
flowchart TD
    A[Client が request] --> B[Server が nonce を要求]
    B --> C[DPoP-Nonce を response]
    C --> D[Client が nonce を保存]
    D --> E[nonce claim を含む proof を生成]
    E --> F[request を再送]
    F --> G[Server が nonce を検証]
</pre>

## 2. Authorization Server が nonce を要求する場合

Authorization Server が nonce を要求しているのに request の DPoP proof に nonce がない場合、RFC 9449 §8 は HTTP 400 response を返し、error code に `use_dpop_nonce` を使用し、`DPoP-Nonce` HTTP response header で nonce を提供する方法を定義しています。

以下は RFC 9449 §8 の構造に沿った非規範的な例です。

```http
HTTP/1.1 400 Bad Request
DPoP-Nonce: NONCE_VALUE
Content-Type: application/json

{
  "error": "use_dpop_nonce"
}
```

配置は次のとおりです。

- **`DPoP-Nonce`:** HTTP response header。Client が次の proof に使用する nonce value。
- **`error`:** JSON response body の member。値は `use_dpop_nonce`。
- **nonce value:** Client が解釈するための JSON object ではなく、opaque な値。

同じ error code は、Client が送った nonce が Server の要求する値と一致しない場合にも使用されます。`DPoP-Nonce` header は response に複数含めてはなりません（MUST NOT, §8）。

## 3. Client は nonce を DPoP proof の claim に入れる

RFC 9449 §4.2 は、Authorization Server または Resource Server が `DPoP-Nonce` header を提供した場合、DPoP proof に `nonce` claim を含めなければならない（MUST）と規定しています。RFC 9449 の Verified Errata ID 7646 は、同節の “authentication server” を “authorization server” に訂正しています。

以下は claim の配置を示すための非規範的な DPoP proof payload 例です。

```json
{
  "jti": "proof-123",
  "htm": "POST",
  "htu": "https://authorization.example/token",
  "iat": 1790000000,
  "nonce": "NONCE_VALUE"
}
```

`nonce` は DPoP proof JWT の payload に置く top-level claim です。`DPoP-Nonce` という名前の JWT claim にするのではありません。また、nonce 自体を独立した HTTP request header として Client から送り返す方式でもありません。

受信 Server は、Server が Client に nonce を提供していた場合、proof の `nonce` claim が Server-provided nonce と一致することを確認しなければなりません（MUST, §4.3）。§8 は、最近提供した nonce と正確に一致しない場合に Authorization Server が request を拒否しなければならない（MUST）と規定しています。

## 4. Resource Server の challenge は HTTP 401 になる

Resource Server が nonce を要求する場合、RFC 9449 §9 は HTTP 401 response、`WWW-Authenticate: DPoP`、`DPoP-Nonce` を使用します。

以下は構造を示す非規範的な例です。

```http
HTTP/1.1 401 Unauthorized
WWW-Authenticate: DPoP error="use_dpop_nonce"
DPoP-Nonce: RESOURCE_NONCE_VALUE
```

Client は Resource Server から受け取った nonce を、その Resource Server への後続 request 用 DPoP proof の `nonce` claim に入れます。Authorization Server から取得した nonce と Resource Server から取得した nonce を同じ値として扱う規定ではありません。

## 5. Server は成功 response で次の nonce を渡すこともできる

RFC 9449 §8.2 は Authorization Server が新しい nonce を `DPoP-Nonce` response header で提供できる（MAY）と規定しています。新しい nonce は error response だけでなく、直前の request に対する HTTP 200 response でも提供できます。

```http
HTTP/1.1 200 OK
Cache-Control: no-store
DPoP-Nonce: NEXT_NONCE_VALUE
```

HTTP 200 response で新しい nonce が提供された場合、Client はその値を次の token request と、それ以降に Authorization Server が新しい nonce を提供するまでの token request で使用しなければなりません（MUST, §8.2）。

`DPoP-Nonce` を含む response は、古い nonce を後続 request で使用することを防ぐため、cache 不能にすべきと RFC 9449 §8.2 は記載しています。

## 6. nonce を受け取った後に省略してはならない

RFC 9449 §11.3 は、Server が Client に DPoP nonce を提供した後、`nonce` claim を含まない DPoP proof を Server が受け入れてはならない（MUST NOT）と規定しています。

一方、nonce をいつ要求するかは Server が決定し、その判断ロジックは RFC 9449 の scope 外です。本記事では特定の発行頻度や更新間隔を推奨しません。

## 一次資料

- RFC Editor: [RFC 9449 — OAuth 2.0 Demonstrating Proof of Possession (DPoP)](https://www.rfc-editor.org/rfc/rfc9449.html)
- RFC Editor: [Verified Errata ID 7646](https://www.rfc-editor.org/errata/eid7646)

参照した主要節: §4.2, §4.3, §8, §8.1, §8.2, §9, §11.3  
最終確認: 2026-09-19
