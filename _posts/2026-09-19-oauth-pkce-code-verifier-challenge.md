---
layout: post
title: "RFC 7636：PKCE の code_verifier と code_challenge はどこに指定するのか"
date: 2026-09-19 14:44:00 +0900
categories: [oauth, security]
---

## この記事について

**記事タイプ:** Flow  
**対象読者:** OAuth 2.0 Authorization Code Grant に PKCE を実装・レビューする開発者  
**この記事で伝えること:** `code_verifier` の生成、`code_challenge` の導出、Authorization Request と Token Request への parameter 配置、Authorization Server による照合を RFC 7636 に沿って理解する  
**扱わないこと:** OAuth 2.0 全体の Authorization Code Grant、Client authentication、redirect URI の選択、PAR、DPoP、RFC 9700 が PKCE の適用対象を拡張する要件

## 1. 2つの値は同じ request に送らない

RFC 7636 の PKCE では、Client は Authorization Request ごとに `code_verifier` を生成し、そこから `code_challenge` を導出します。

`code_challenge` は Authorization Request に送ります。一方、元の `code_verifier` はその時点では送らず、Authorization Code を受け取った後の Token Request に送ります。Authorization Server は、Authorization Request 時に受け取った challenge と、Token Request 時に受け取った verifier から計算した値を比較します（RFC 7636 §1.1, §4）。

<pre class="mermaid">
flowchart TD
    A[Client: code_verifier を生成]
    A --> B[S256 で code_challenge を導出]
    B --> C[Authorization Request: challenge を送信]
    C --> D[Authorization Server: code と challenge を関連付け]
    D --> E[Client: code と verifier を Token Request に送信]
    E --> F[Authorization Server: verifier から challenge を再計算]
    F --> G{保存した challenge と一致}
    G -->|Yes| H[通常の token 処理を継続]
    G -->|No| I[invalid_grant]
</pre>

## 2. `code_verifier` を生成する

RFC 7636 §4.1 では、`code_verifier` は unreserved characters からなる 43〜128 文字の high-entropy cryptographic random string です。使用できる文字は英大文字、英小文字、数字、`-`、`.`、`_`、`~` です。

仕様は verifier が推測困難になるだけの entropy を持つべき（SHOULD）とし、適切な乱数生成器で 32 octets を生成して base64url encode し、43 octets の URL-safe string とする方法を RECOMMENDED としています（§4.1）。

以下の値は構造を示すための非規範的な例です。

```text
code_verifier = dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

## 3. S256 で `code_challenge` を作る

RFC 7636 §4.2 の S256 は次の変換です。

```text
code_challenge = BASE64URL-ENCODE(SHA256(ASCII(code_verifier)))
```

Client が S256 を使用できる場合、S256 を使用しなければなりません（MUST, §4.2）。`plain` を使用できるのは、技術的理由で S256 をサポートできず、かつ server が `plain` をサポートすることを out-of-band configuration で知っている場合に限られます。

RFC 7636 Appendix B の verifier を使うと、S256 の challenge は次の値になります。

```text
E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
```

## 4. Authorization Request に challenge を置く

RFC 7636 §4.3 では、PKCE は Authorization Request に次の parameter を追加します。

- **`code_challenge`:** REQUIRED。導出した challenge。
- **`code_challenge_method`:** OPTIONAL。`S256` または `plain`。省略時は `plain`。

これらは JSON member ではなく OAuth 2.0 Authorization Request parameter です。次は配置を示す非規範的な HTTP 例です。

```http
GET /authorize?response_type=code
  &client_id=client-123
  &redirect_uri=https%3A%2F%2Fclient.example%2Fcb
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
  &code_challenge_method=S256 HTTP/1.1
Host: authorization.example
```

RFC 7636 §4.4 では、Authorization Server が Authorization Code を発行するとき、`code_challenge` と `code_challenge_method` をその code に関連付けなければなりません（MUST）。どのように関連付けて保存するかは仕様の scope 外です。

## 5. Token Request に verifier を置く

Authorization Code を受け取った Client は Token Endpoint への Access Token Request に `code_verifier` を追加します。`code_verifier` は REQUIRED です（RFC 7636 §4.5）。

次は form parameter の配置を示す非規範的な例です。

```http
POST /token HTTP/1.1
Host: authorization.example
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=AUTHORIZATION_CODE&redirect_uri=https%3A%2F%2Fclient.example%2Fcb&code_verifier=dBjftJeZ4CVP-mB92K27uhbUJU1p1r_wW1gFWFOEjXk
```

この request では `code_challenge` を再送するのではなく、元の `code_verifier` を送ります。RFC 7636 §6.1 でも `code_verifier` の usage location は token request、`code_challenge` と `code_challenge_method` は authorization request と登録されています。

## 6. Authorization Server が照合する

RFC 7636 §4.6 では、Authorization Server は Token Endpoint で受け取った `code_verifier` を、Authorization Request で指定された `code_challenge_method` に従って変換し、Authorization Code に関連付けられた `code_challenge` と比較します。

S256 の場合は次の等式を検証します。

```text
BASE64URL-ENCODE(SHA256(ASCII(code_verifier))) == code_challenge
```

値が一致すれば、Token Endpoint は通常の処理を継続しなければなりません（MUST）。一致しなければ、RFC 6749 §5.2 の `invalid_grant` error response を返さなければなりません（MUST, RFC 7636 §4.6）。

Authorization Server が PKCE を public client に要求しており Authorization Request に `code_challenge` がない場合、Authorization Endpoint は `invalid_request` を返さなければなりません（MUST, §4.4.1）。要求された transformation method を server がサポートしない場合も `invalid_request` を返さなければなりません（MUST, §4.4.1）。

## 一次資料

- RFC Editor: [RFC 7636 — Proof Key for Code Exchange by OAuth Public Clients](https://www.rfc-editor.org/rfc/rfc7636.html)

参照した主要節: §1.1, §3, §4.1–§4.6, §6.1, Appendix B  
最終確認: 2026-09-19
